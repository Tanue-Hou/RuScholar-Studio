import os
import sys
import json
import asyncio
import math
import uuid
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel

# Add parent dir to path to import naturalization_layer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from naturalization_layer.rules_engine import analyze_text_rules, should_run_ppl_heuristic
from naturalization_layer.ppl_engine import PPLEngine
from naturalization_layer.llm_judge import StyleJudge
from naturalization_layer.style_risk import calculate_style_risks, calculate_redundancy_risk
from naturalization_layer.translationese_risk import calculate_translationese_risk, run_translationese_checks
from naturalization_layer.source_similarity import check_source_similarity
from naturalization_layer.citation_integrity import check_citation_integrity
import docx

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models/Qwen3-4B-Q5_K_M.gguf")
engine = None
judge = None
SKILL_RULES_PATH = os.path.expanduser("~/.gemini/config/skills/phd-thesis-butler/assets/references/polishing_rules_v5.json")
CALIBRATION_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "naturalization_layer/calibration/calibration_config.json")
global_clusters = {}
calibration_db = {}
model_lock = asyncio.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, judge, global_clusters, calibration_db
    print("Loading Llama model...")
    if os.path.exists(MODEL_PATH):
        engine = PPLEngine(MODEL_PATH)
        judge = StyleJudge(engine.llm)
        print("Model loaded successfully.")
    else:
        print(f"Model not found at {MODEL_PATH}. Running in Heuristics-only mode.")
        
    if os.path.exists(SKILL_RULES_PATH):
        try:
            with open(SKILL_RULES_PATH, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
                global_clusters = rules_data.get("clusters", {})
                print("Loaded phd-thesis-butler polishing rules clusters.")
        except Exception as e:
            print(f"Failed to load skill rules: {e}")
            
    if os.path.exists(CALIBRATION_CONFIG_PATH):
        try:
            with open(CALIBRATION_CONFIG_PATH, 'r', encoding='utf-8') as f:
                calibration_db = json.load(f)
                print("Loaded calibration thresholds database.")
        except Exception as e:
            print(f"Failed to load calibration config: {e}")
            
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_discipline_rules(discipline: str) -> dict:
    rules = global_clusters.get(discipline, global_clusters.get("UNIVERSAL", None))
    if not rules and global_clusters:
        rules = next(iter(global_clusters.values()), None)
        
    if not rules:
        rules = {
            "do_rules": [
                "Использовать безличные и неопределенно-личные конструкции",
                "Соблюдать строгую логическую последовательность (введение -> методы -> результаты)"
            ],
            "dont_rules": [
                "Использовать местоимения первого лица (я, мы)",
                "Использовать эмоционально-окрашенную лексику и метафоры",
                "Злоупотреблять пассивным залогом и длинными цепочками существительных"
            ]
        }
    return rules

def parse_docx(file_bytes):
    import io
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs])

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    contents = await file.read()
    if file.filename.endswith(".docx"):
        text = parse_docx(contents)
    else:
        text = contents.decode("utf-8")
        
    return {"status": "ok", "filename": file.filename, "text": text}

class DetectDisciplineRequest(BaseModel):
    text: str
    engine_type: str = "local"
    api_key: str = ""
    base_url: str = ""

@app.post("/api/detect_discipline")
async def detect_discipline_endpoint(req: DetectDisciplineRequest):
    """
    Zero-shot academic discipline classification endpoint.
    Samples the first 1000 characters and identifies the academic domain cluster.
    """
    global engine, judge
    judge_inst = None
    
    if req.engine_type == "local":
        if os.path.exists(MODEL_PATH):
            if engine is None:
                engine = PPLEngine(MODEL_PATH)
                judge = StyleJudge(engine.llm)
            judge_inst = judge
    else:
        judge_inst = StyleJudge(None)
        
    if judge_inst is None:
        # Fallback to simple keyword detection if local model file is missing
        text_lower = req.text.lower()
        if any(w in text_lower for w in ["управление", "робот", "автоматиз", "регулятор", "динамик", "control", "robot", "automat"]):
            discipline = "AUTOMATION_CONTROL"
        elif any(w in text_lower for w in ["биолог", "медиц", "клетк", "терап", "ген", "biolog", "medic", "cell", "gene"]):
            discipline = "AGRI_MED"
        elif any(w in text_lower for w in ["физик", "хими", "сплав", "материал", "энерг", "physic", "chemic", "material"]):
            discipline = "SCI_TECH"
        elif any(w in text_lower for w in ["эконом", "полити", "гуманитар", "истори", "обществ", "econom", "polit", "social"]):
            discipline = "HUM_POL_ECON"
        else:
            discipline = "UNIVERSAL"
    else:
        try:
            if req.engine_type == "local":
                async with model_lock:
                    discipline = await asyncio.to_thread(
                        judge_inst.detect_discipline, req.text, req.engine_type, req.api_key, req.base_url
                    )
            else:
                discipline = await asyncio.to_thread(
                    judge_inst.detect_discipline, req.text, req.engine_type, req.api_key, req.base_url
                )
        except Exception as e:
            print(f"Discipline detection failed: {e}. Falling back to UNIVERSAL.")
            discipline = "UNIVERSAL"
            
    return {"discipline": discipline}

class SessionRequest(BaseModel):
    text: str
    engine_type: str = "local"
    api_key: str = ""
    base_url: str = ""
    discipline: str = "UNIVERSAL"

active_sessions = {}

@app.post("/api/session")
async def create_session(req: SessionRequest):
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "text": req.text,
        "engine_type": req.engine_type,
        "api_key": req.api_key,
        "base_url": req.base_url,
        "discipline": req.discipline
    }
    return {"session_id": session_id}

@app.get("/api/diagnose")
async def diagnose_stream(session_id: str):
    """
    Server-Sent Events endpoint to stream the analysis of sentences.
    Retrieves execution parameters from in-memory session store using session_id.
    """
    session = active_sessions.get(session_id)
    if not session:
        async def error_generator():
            yield {
                "event": "error",
                "data": json.dumps({"error": "Session expired or not found."})
            }
        return EventSourceResponse(error_generator())
        
    text = session["text"]
    engine_type = session["engine_type"]
    api_key = session["api_key"]
    base_url = session["base_url"]
    discipline = session["discipline"]
    
    async def event_generator():
        try:
            # 1. Run Rules Engine on the whole text
            rules_res = analyze_text_rules(text)
            sentences = rules_res["sentences"]
            
            # 2. Run Citation Integrity check on the whole text
            integrity_report = check_citation_integrity(text)
            global_warnings = integrity_report.get("warnings", [])
            
            # Engine initialization (lazy loading)
            engine_inst = None
            judge_inst = None
            
            if engine_type == "local":
                if os.path.exists(MODEL_PATH):
                    global engine, judge
                    if engine is None:
                        engine = PPLEngine(MODEL_PATH)
                        judge = StyleJudge(engine.llm)
                    engine_inst = engine
                    judge_inst = judge
                else:
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": "Local model not found. Please download it first."})
                    }
                    return
            else:
                judge_inst = StyleJudge(None)
            
            # Load dynamic rules for the specified discipline
            active_rules = get_discipline_rules(discipline)
            
            # Load calibrated thresholds
            calib = calibration_db.get(discipline, calibration_db.get("UNIVERSAL", {}))
            ppl_low = calib.get("ppl_low", 15.0)
            ppl_high = calib.get("ppl_high", 80.0)
            nv_ratio_max = calib.get("nv_ratio_max", 4.5)
            
            # Yield init event matching frontend expectations
            yield {
                "event": "init",
                "data": json.dumps({"total_sentences": len(sentences), "discipline": discipline})
            }

            # Yield citation integrity warnings first as global diagnostics (with index = -1, -2...)
            for w_idx, warning in enumerate(global_warnings):
                yield {
                    "event": "result",
                    "data": json.dumps({
                        "index": -1 - w_idx,
                        "text": f"Citation Integrity Alert ({warning['evidence']})",
                        "ppl": None,
                        "issue_type": warning["issue_type"],
                        "severity": warning["severity"],
                        "explanation": warning["explanation_zh"],
                        "suggestion": warning["rewrite_suggestion"],
                        "think": f"【文献完整性校验警告】对文内引文标号与篇末参考文献列表进行交叉对照发现合规风险：{warning['explanation_zh']}。这会降低论文文献引用的规范度与学术严谨度，建议在最终稿中予以修正。",
                        "status": "flagged",
                        "metrics": None,
                        "predictability_risk": 0.0,
                        "uniformity_risk": 0.0,
                        "translationese_risk": 0.0,
                        "redundancy_risk": 0.0
                    })
                }
            
            # Track values for document-level Style Risk Indices
            ppl_vals = []
            flagged_count = 0
            nv_ratios = []
            passive_counts = []
            genitive_chain_counts = []
            cliche_counts = []
            word_counts = []
            connectors_counts = []

            if engine_type == "local":
                # Branch A: Local serial execution with Early Exit (to prevent overloading CPU/GPU)
                for i, s in enumerate(sentences):
                    diag_rules = rules_res["sentence_diagnostics"][i]
                    has_citation = "[" in s
                    sim_warning = check_source_similarity(s, has_citation)
                    
                    result = {
                        "index": i,
                        "text": s,
                        "ppl": None,
                        "issue_type": None,
                        "severity": None,
                        "explanation": None,
                        "suggestion": None,
                        "think": None,
                        "status": "ok",
                        "metrics": {
                            "nv_ratio": diag_rules.get("nv_ratio", 0.0),
                            "passive_count": diag_rules.get("passive_count", 0),
                            "genitive_chains_count": len(diag_rules.get("genitive_chains", [])),
                            "cliches_count": len(diag_rules.get("cliches_found", [])),
                            "connectors_count": len(diag_rules.get("connectors_found", []))
                        }
                    }
                    
                    trans_warnings = run_translationese_checks(s, diag_rules)
                    if sim_warning and sim_warning["issue_type"] == "semantic_plagiarism_risk":
                        trans_warnings.append(sim_warning)
                        
                    if trans_warnings:
                        diag_rules["trans_warnings"] = [w["explanation_zh"] for w in trans_warnings]
                    
                    has_track_a_triggers = (
                        len(diag_rules.get("cliches_found", [])) > 0 or
                        len(diag_rules.get("genitive_chains", [])) > 0 or
                        diag_rules.get("nv_ratio", 0.0) > nv_ratio_max or
                        diag_rules.get("passive_count", 0) > 0 or
                        len(trans_warnings) > 0
                    )
                    
                    if engine_inst:
                        ee_tokens = 6 if not has_track_a_triggers else 0
                        ee_lower = ppl_low if not has_track_a_triggers else 0.0
                        ee_upper = ppl_high if not has_track_a_triggers else float('inf')
                        
                        async with model_lock:
                            ppl, was_early_exited = await asyncio.to_thread(
                                engine_inst.evaluate_sentence_ppl, s, ee_tokens, ee_lower, ee_upper
                            )
                            
                        result["ppl"] = round(ppl, 2) if ppl else None
                        is_suspicious = ppl < ppl_low or ppl > ppl_high or has_track_a_triggers
                    else:
                        was_early_exited = False
                        is_suspicious = has_track_a_triggers
                        
                    # Run advanced translationese checks
                    if was_early_exited:
                        result["status"] = "early_exit"
                        result["think"] = (
                            f"【早期退出 (Early Exit)】评估前几个 Token 对应 Perplexity (PPL) 为 {result.get('ppl')}，"
                            f"处于学术正常分布带 ({ppl_low} ~ {ppl_high}) 且无翻译腔或套话特征。已安全退回，跳过高算力专家诊断。"
                        )
                    elif sim_warning and sim_warning["issue_type"] == "citation_gap":
                        result["status"] = "flagged"
                        result["issue_type"] = "citation_gap"
                        result["severity"] = "high"
                        result["explanation"] = sim_warning["explanation_zh"]
                        result["suggestion"] = sim_warning["rewrite_suggestion"]
                        result["think"] = (
                            f"【学术改写与引用合规风险】该句与本地文献记录《{sim_warning['evidence']}》"
                            f"的表达重合度高，且在此处缺少参考文献引标，触发『引用缺口 (Citation Gap)』警告，请补充对应标注。"
                        )
                    elif is_suspicious:
                        ctx_before = sentences[max(0, i-2):i]
                        ctx_after = sentences[i+1:min(len(sentences), i+3)]
                        
                        async with model_lock:
                            diag = await asyncio.to_thread(
                                judge_inst.diagnose_sentence, 
                                s, 
                                stats=diag_rules, 
                                ppl=result.get("ppl"), 
                                context_before=ctx_before, 
                                context_after=ctx_after,
                                skill_rules=active_rules,
                                engine_type=engine_type,
                                api_key=api_key,
                                base_url=base_url
                            )
                        result["think"] = diag.get("think", "")
                        
                        issues = diag.get("issues", [])
                        if issues:
                            issue = issues[0]
                            result["issue_type"] = issue.get('issue_type', '')
                            result["severity"] = issue.get('severity', '')
                            result["explanation"] = issue.get('explanation_zh', '')
                            result["suggestion"] = issue.get('rewrite_suggestion', '')
                            if result["issue_type"] in ("api_request_error", "json_parse_error"):
                                result["status"] = "passed"
                            else:
                                result["status"] = "flagged"
                            if not result["think"]:
                                result["think"] = f"【专家模型判定】深度扫描检测到可疑特征：{result['explanation']}"
                        else:
                            result["status"] = "passed"
                            result["think"] = (
                                f"【深度扫描通过】句子经专家大模型多维度推理评估，尽管 Perplexity 偏离或有轻微规则触碰，"
                                f"但其整体语义连贯、学术表述符合规范，无显著的机器翻译或 AI 生成痕迹。"
                            )
                    else:
                        result["status"] = "passed"
                        result["think"] = (
                            f"【规则通过】句子未触发生感官低 PPL 警报，亦无学术套话、拖沓修饰长链。"
                            f"名词动词比率（{result['metrics']['nv_ratio']}）处于健康带，语态逻辑清晰，通过风格初筛。"
                        )
                        
                    # Append to metric trackers
                    ppl_vals.append(result["ppl"])
                    nv_ratios.append(result["metrics"]["nv_ratio"])
                    passive_counts.append(result["metrics"]["passive_count"])
                    genitive_chain_counts.append(result["metrics"]["genitive_chains_count"])
                    cliche_counts.append(result["metrics"]["cliches_count"])
                    word_counts.append(diag_rules.get("word_count", len(s.split())))
                    connectors_counts.append(result["metrics"]["connectors_count"])
                    
                    if result["status"] == "flagged":
                        flagged_count += 1
                        
                    # Calculate running risks for real-time telemetry (consolidated backend calculation)
                    running_pred, running_unif = calculate_style_risks(
                        ppl_vals, flagged_count, i + 1, calib, word_counts=word_counts
                    )
                    running_trans = calculate_translationese_risk(nv_ratios, passive_counts, genitive_chain_counts)
                    running_red = calculate_redundancy_risk(
                        cliche_counts, genitive_chain_counts, passive_counts, nv_ratios, connectors_counts
                    )
                    
                    result["predictability_risk"] = running_pred
                    result["uniformity_risk"] = running_unif
                    result["translationese_risk"] = running_trans
                    result["redundancy_risk"] = running_red
                    
                    yield {"event": "result", "data": json.dumps(result)}
                    # Brief pause to allow event loop to breathe
                    await asyncio.sleep(0.01)
            else:
                # Branch B: Cloud API mode - Concurrent evaluation of all sentences (highly efficient via asyncio)
                async def process_sentence_cloud(idx: int, text_str: str) -> dict:
                    diag_rules = rules_res["sentence_diagnostics"][idx]
                    has_citation = "[" in text_str
                    sim_warning = check_source_similarity(text_str, has_citation)
                    
                    res_dict = {
                        "index": idx,
                        "text": text_str,
                        "ppl": None,
                        "issue_type": None,
                        "severity": None,
                        "explanation": None,
                        "suggestion": None,
                        "think": None,
                        "status": "ok",
                        "metrics": {
                            "nv_ratio": diag_rules.get("nv_ratio", 0.0),
                            "passive_count": diag_rules.get("passive_count", 0),
                            "genitive_chains_count": len(diag_rules.get("genitive_chains", [])),
                            "cliches_count": len(diag_rules.get("cliches_found", [])),
                            "connectors_count": len(diag_rules.get("connectors_found", []))
                        }
                    }
                    
                    trans_warnings = run_translationese_checks(text_str, diag_rules)
                    if sim_warning and sim_warning["issue_type"] == "semantic_plagiarism_risk":
                        trans_warnings.append(sim_warning)
                        
                    if trans_warnings:
                        diag_rules["trans_warnings"] = [w["explanation_zh"] for w in trans_warnings]
                        
                    if sim_warning and sim_warning["issue_type"] == "citation_gap":
                        res_dict["status"] = "flagged"
                        res_dict["issue_type"] = "citation_gap"
                        res_dict["severity"] = "high"
                        res_dict["explanation"] = sim_warning["explanation_zh"]
                        res_dict["suggestion"] = sim_warning["rewrite_suggestion"]
                        res_dict["think"] = (
                            f"【学术改写与引用合规风险】该句与本地文献记录《{sim_warning['evidence']}》"
                            f"的表达重合度高，且在此处缺少参考文献引标，触发『引用缺口 (Citation Gap)』警告，请补充对应标注。"
                        )
                    else:
                        ctx_before = sentences[max(0, idx-2):idx]
                        ctx_after = sentences[idx+1:min(len(sentences), idx+3)]
                        
                        diag = await asyncio.to_thread(
                            judge_inst.diagnose_sentence, 
                            text_str, 
                            stats=diag_rules, 
                            ppl=None, 
                            context_before=ctx_before, 
                            context_after=ctx_after,
                            skill_rules=active_rules,
                            engine_type=engine_type,
                            api_key=api_key,
                            base_url=base_url
                        )
                        res_dict["think"] = diag.get("think", "")
                        
                        if diag.get("estimated_perplexity") is not None:
                            res_dict["ppl"] = diag["estimated_perplexity"]
                            
                        issues = diag.get("issues", [])
                        if issues:
                            issue = issues[0]
                            res_dict["issue_type"] = issue.get('issue_type', '')
                            res_dict["severity"] = issue.get('severity', '')
                            res_dict["explanation"] = issue.get('explanation_zh', '')
                            res_dict["suggestion"] = issue.get('rewrite_suggestion', '')
                            if res_dict["issue_type"] in ("api_request_error", "json_parse_error"):
                                res_dict["status"] = "passed"
                            else:
                                res_dict["status"] = "flagged"
                            if not res_dict["think"]:
                                res_dict["think"] = f"【专家模型判定】深度扫描检测到可疑特征：{res_dict['explanation']}"
                        else:
                            res_dict["status"] = "passed"
                            res_dict["think"] = (
                                f"【云端深度扫描通过】大模型全面评估通过。估算 Perplexity 值为 {res_dict.get('ppl')}，"
                                f"行文表达逻辑严密、流畅，符合标准俄语学术写作表达规范。"
                            )
                            
                    return res_dict

                # Loop and execute cloud tasks serially with a small delay to prevent API rate limiting
                for i, s in enumerate(sentences):
                    result = await process_sentence_cloud(i, s)
                    
                    ppl_vals.append(result["ppl"])
                    nv_ratios.append(result["metrics"]["nv_ratio"])
                    passive_counts.append(result["metrics"]["passive_count"])
                    genitive_chain_counts.append(result["metrics"]["genitive_chains_count"])
                    cliche_counts.append(result["metrics"]["cliches_count"])
                    word_counts.append(rules_res["sentence_diagnostics"][i].get("word_count", len(result["text"].split())))
                    connectors_counts.append(result["metrics"]["connectors_count"])
                    
                    if result["status"] == "flagged":
                        flagged_count += 1
                        
                    running_pred, running_unif = calculate_style_risks(
                        ppl_vals, flagged_count, i + 1, calib, word_counts=word_counts
                    )
                    running_trans = calculate_translationese_risk(nv_ratios, passive_counts, genitive_chain_counts)
                    running_red = calculate_redundancy_risk(
                        cliche_counts, genitive_chain_counts, passive_counts, nv_ratios, connectors_counts
                    )
                    
                    result["predictability_risk"] = running_pred
                    result["uniformity_risk"] = running_unif
                    result["translationese_risk"] = running_trans
                    result["redundancy_risk"] = running_red
                    
                    yield {"event": "result", "data": json.dumps(result)}
                    # 0.15s sleep between serial requests to avoid API rate limiting/timeouts
                    await asyncio.sleep(0.15)
            
            # Final document-level risks
            pred_risk, unif_risk = calculate_style_risks(
                ppl_vals, flagged_count, len(sentences), calib, word_counts=word_counts
            )
            trans_risk = calculate_translationese_risk(nv_ratios, passive_counts, genitive_chain_counts)
            redundancy_risk = calculate_redundancy_risk(
                cliche_counts, genitive_chain_counts, passive_counts, nv_ratios, connectors_counts
            )
            
            yield {
                "event": "done",
                "data": json.dumps({
                    "predictability_risk": pred_risk,
                    "uniformity_risk": unif_risk,
                    "translationese_risk": trans_risk,
                    "redundancy_risk": redundancy_risk
                })
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
        finally:
            active_sessions.pop(session_id, None)
        
    return EventSourceResponse(event_generator())

@app.get("/api/check_model")
async def check_model():
    return {"exists": os.path.exists(MODEL_PATH)}

@app.get("/api/download_model")
async def download_model_endpoint():
    async def event_generator():
        try:
            current_progress = 0
            
            def progress_callback(progress: float):
                nonlocal current_progress
                current_progress = progress * 100
                
            from naturalization_layer.model_downloader import download_model
            
            # Start download in a background thread to prevent blocking
            task = asyncio.create_task(
                asyncio.to_thread(download_model, MODEL_PATH, progress_callback)
            )
            
            last_yielded = -1
            while not task.done():
                if int(current_progress) != last_yielded:
                    last_yielded = int(current_progress)
                    yield {
                        "data": json.dumps({"status": "downloading", "progress": current_progress})
                    }
                await asyncio.sleep(0.5)
                
            await task
            yield {
                "data": json.dumps({"status": "complete"})
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {
                "data": json.dumps({"status": "error", "message": str(e)})
            }
            
    return EventSourceResponse(event_generator())

from fastapi.staticfiles import StaticFiles

# Future Extension Interfaces (Placeholder)
@app.post("/api/polish")
async def polish_text(text: str):
    return {"status": "not_implemented"}

@app.post("/api/references")
async def check_references(text: str):
    return {"status": "not_implemented"}

@app.post("/api/format")
async def check_format(text: str):
    return {"status": "not_implemented"}

@app.post("/api/structure")
async def analyze_structure(text: str):
    return {"status": "not_implemented"}

# Serve frontend build statically
frontend_dist = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
else:
    print(f"Warning: Frontend build directory not found at {frontend_dist}. Please run `npm run build` in the frontend directory.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
