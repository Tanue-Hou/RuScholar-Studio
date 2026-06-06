import os
import sys
import json
import asyncio
import math
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from contextlib import asynccontextmanager

# Add parent dir to path to import naturalization_layer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from naturalization_layer.rules_engine import analyze_text_rules, should_run_ppl_heuristic
from naturalization_layer.ppl_engine import PPLEngine
from naturalization_layer.llm_judge import StyleJudge
import docx

MODEL_PATH = "../models/Qwen3-4B-Q5_K_M.gguf"
engine = None
judge = None
SKILL_RULES_PATH = os.path.expanduser("~/.gemini/config/skills/phd-thesis-butler/assets/references/polishing_rules_v5.json")
global_clusters = {}
model_lock = asyncio.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, judge, global_clusters
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

@app.get("/api/detect_discipline")
async def detect_discipline_endpoint(
    text: str,
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = ""
):
    """
    Zero-shot academic discipline classification endpoint.
    Samples the first 1000 characters and identifies the academic domain cluster.
    """
    global engine, judge
    judge_inst = None
    
    if engine_type == "local":
        model_path = "../models/Qwen3-4B-Q5_K_M.gguf"
        if os.path.exists(model_path):
            if engine is None:
                engine = PPLEngine(model_path)
                judge = StyleJudge(engine.llm)
            judge_inst = judge
    else:
        judge_inst = StyleJudge(None)
        
    if judge_inst is None:
        # Fallback to simple keyword detection if local model file is missing
        text_lower = text.lower()
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
            if engine_type == "local":
                async with model_lock:
                    discipline = await asyncio.to_thread(
                        judge_inst.detect_discipline, text, engine_type, api_key, base_url
                    )
            else:
                discipline = await asyncio.to_thread(
                    judge_inst.detect_discipline, text, engine_type, api_key, base_url
                )
        except Exception as e:
            print(f"Discipline detection failed: {e}. Falling back to UNIVERSAL.")
            discipline = "UNIVERSAL"
            
    return {"discipline": discipline}

@app.get("/api/diagnose")
async def diagnose_stream(
    text: str,
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = "",
    discipline: str = "UNIVERSAL"
):
    """
    Server-Sent Events endpoint to stream the analysis of sentences.
    Accepts raw text (URL encoded) and configuration parameters.
    """
    async def event_generator():
        try:
            # 1. Run Rules Engine on the whole text (faster and context-aware)
            rules_res = analyze_text_rules(text)
            sentences = rules_res["sentences"]
            
            # Engine initialization (lazy loading)
            engine_inst = None
            judge_inst = None
            
            if engine_type == "local":
                model_path = "../models/Qwen3-4B-Q5_K_M.gguf"
                if os.path.exists(model_path):
                    global engine, judge
                    if engine is None:
                        engine = PPLEngine(model_path)
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
                # For DeepSeek API, instantiate StyleJudge with None LLM
                judge_inst = StyleJudge(None)
            
            # Load dynamic rules for the specified discipline
            active_rules = get_discipline_rules(discipline)
            
            # Yield init event matching frontend expectations
            yield {
                "event": "init",
                "data": json.dumps({"total_sentences": len(sentences), "discipline": discipline})
            }
            
            # Track values for document-level Style Risk Indices
            ppl_vals = []
            flagged_count = 0
            nv_ratios = []
            passive_counts = []
            genitive_chain_counts = []
            cliche_counts = []
            
            for i, s in enumerate(sentences):
                diag_rules = rules_res["sentence_diagnostics"][i]
                
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
                        "cliches_count": len(diag_rules.get("cliches_found", []))
                    }
                }
                
                has_track_a_triggers = (
                    len(diag_rules.get("cliches_found", [])) > 0 or
                    len(diag_rules.get("genitive_chains", [])) > 0 or
                    diag_rules.get("nv_ratio", 0.0) > 4.0 or
                    diag_rules.get("passive_count", 0) > 0
                )
                
                if engine_type == "local" and engine_inst:
                    ee_tokens = 6 if not has_track_a_triggers else 0
                    ee_lower = 15.0 if not has_track_a_triggers else 0.0
                    ee_upper = 80.0 if not has_track_a_triggers else float('inf')
                    
                    async with model_lock:
                        ppl, was_early_exited = await asyncio.to_thread(
                            engine_inst.evaluate_sentence_ppl, s, ee_tokens, ee_lower, ee_upper
                        )
                    
                    result["ppl"] = round(ppl, 2) if ppl else None
                    is_suspicious = ppl < 15.0 or ppl > 80.0 or has_track_a_triggers
                else:
                    was_early_exited = False
                    is_suspicious = has_track_a_triggers
                
                if was_early_exited:
                    result["status"] = "early_exit"
                elif is_suspicious:
                    ctx_before = sentences[max(0, i-2):i]
                    ctx_after = sentences[i+1:min(len(sentences), i+3)]
                    
                    if engine_type == "local":
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
                    else:
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
                        result["status"] = "flagged"
                    else:
                        result["status"] = "passed"
                else:
                    result["status"] = "passed"
                
                # Append to metric trackers
                ppl_vals.append(result["ppl"])
                nv_ratios.append(result["metrics"]["nv_ratio"])
                passive_counts.append(result["metrics"]["passive_count"])
                genitive_chain_counts.append(result["metrics"]["genitive_chains_count"])
                cliche_counts.append(result["metrics"]["cliches_count"])
                if result["status"] == "flagged":
                    flagged_count += 1
                    
                yield {"event": "result", "data": json.dumps(result)}
                # Brief pause to allow event loop to breathe
                await asyncio.sleep(0.01)
            
            # Calculate final document-level risks
            ppl_evaluated = [p for p in ppl_vals if p is not None]
            
            # 1. Predictability Risk
            if ppl_evaluated:
                pred_count = sum(1 for p in ppl_evaluated if p < 15.0)
                predictability_risk = round((pred_count / len(ppl_evaluated)) * 100, 1)
            else:
                predictability_risk = round((flagged_count / max(1, len(sentences))) * 100, 1)
                
            # 2. Uniformity Risk
            if len(ppl_evaluated) > 1:
                mean_ppl = sum(ppl_evaluated) / len(ppl_evaluated)
                variance = sum((p - mean_ppl) ** 2 for p in ppl_evaluated) / len(ppl_evaluated)
                std_dev = math.sqrt(variance)
                uniformity_risk = round(max(0.0, min(100.0, (30.0 - std_dev) * 4.0)), 1)
            else:
                uniformity_risk = 0.0
                
            # 3. Translationese Risk
            trans_scores = []
            for nv, pas, gen in zip(nv_ratios, passive_counts, genitive_chain_counts):
                nv_score = min(2.0, max(0.0, nv - 1.5)) / 2.0
                pas_score = min(1.0, pas * 0.5)
                gen_score = min(1.0, gen * 0.5)
                trans_scores.append((nv_score + pas_score + gen_score) / 3.0)
            
            translationese_risk = round((sum(trans_scores) / max(1, len(trans_scores))) * 100, 1)
            
            # 4. Redundancy Risk
            if cliche_counts:
                cliche_sent_count = sum(1 for c in cliche_counts if c > 0)
                redundancy_risk = round((cliche_sent_count / len(cliche_counts)) * 100, 1)
            else:
                redundancy_risk = 0.0
            
            yield {
                "event": "done",
                "data": json.dumps({
                    "predictability_risk": predictability_risk,
                    "uniformity_risk": uniformity_risk,
                    "translationese_risk": translationese_risk,
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
