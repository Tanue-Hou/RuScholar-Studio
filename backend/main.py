import os
import sys
import json
import asyncio
import math
import uuid
from fastapi import FastAPI, UploadFile, File, Form
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

from services.shared_state import session_references, model_lock, MODEL_PATH
engine = None
judge = None
citation_judge_global = None

SKILL_RULES_PATH = os.path.expanduser("~/.gemini/config/skills/phd-thesis-butler/assets/references/polishing_rules_v5.json")
CALIBRATION_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "naturalization_layer/calibration/calibration_config.json")
global_clusters = {}
calibration_db = {}

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

def parse_pdf_bytes(file_bytes):
    import io
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text

def extract_citation_keys(sentence: str) -> list[str]:
    from services.citation_audit_service import extract_citation_keys as ext_keys
    return ext_keys(sentence)

async def perform_nli_citation_audit(text_str: str, session_id: str, engine_type: str, api_key: str, base_url: str, citation_judge) -> list:
    from services.citation_audit_service import perform_nli_citation_audit as audit_cit
    return await audit_cit(text_str, session_id, engine_type, api_key, base_url, citation_judge)


@app.post("/api/upload_references")
async def upload_references(
    session_id: str = Form(...),
    bibtex: str = Form(""),
    files: list[UploadFile] = File([])
):
    from naturalization_layer.rag_retriever import parse_bibtex, chunk_text, BM25Retriever
    import re
    
    if session_id not in session_references:
        session_references[session_id] = {
            "bibtex": {},
            "corpus": {},
            "retrievers": {},
            "online_cache": {},
            "bib_mapping": {}
        }
    
    bib_entries = {}
    if bibtex.strip():
        try:
            bib_entries = parse_bibtex(bibtex)
            session_references[session_id]["bibtex"].update(bib_entries)
        except Exception as e:
            print(f"Failed to parse BibTeX: {e}")
            
    for file in files:
        contents = await file.read()
        filename = file.filename
        name_part, ext = os.path.splitext(filename)
        clean_name = re.sub(r'[\[\]]', '', name_part).strip().lower()
        
        text = ""
        if ext.lower() == ".pdf":
            try:
                text = parse_pdf_bytes(contents)
            except Exception as e:
                print(f"Failed to parse PDF {filename}: {e}")
        elif ext.lower() in (".docx",):
            try:
                text = parse_docx(contents)
            except Exception as e:
                print(f"Failed to parse DOCX {filename}: {e}")
        else:
            try:
                text = contents.decode("utf-8")
            except Exception as e:
                print(f"Failed to decode file {filename}: {e}")
                
        if text.strip():
            chunks = chunk_text(text)
            corpus_entries = []
            for idx, chunk in enumerate(chunks):
                corpus_entries.append({
                    "text": chunk,
                    "metadata": {
                        "filename": filename,
                        "key": clean_name,
                        "chunk_index": idx
                    }
                })
            
            session_references[session_id]["corpus"][clean_name] = corpus_entries
            session_references[session_id]["retrievers"][clean_name] = BM25Retriever(corpus_entries)
            
    return {
        "status": "ok",
        "bibtex_keys": list(session_references[session_id]["bibtex"].keys()),
        "pdf_keys": list(session_references[session_id]["retrievers"].keys())
    }

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    contents = await file.read()
    if file.filename.lower().endswith(".docx"):
        text = parse_docx(contents)
    elif file.filename.lower().endswith(".pdf"):
        text = parse_pdf_bytes(contents)
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
    
    # Prioritize cloud API classification if api_key is provided
    use_cloud = bool(req.api_key and req.api_key.strip())
    
    if use_cloud:
        actual_engine = "deepseek-v4-flash" if "flash" in req.engine_type else "deepseek-v4-pro"
        judge_inst = StyleJudge(None)
    else:
        actual_engine = "local"
        if os.path.exists(MODEL_PATH):
            if engine is None:
                engine = PPLEngine(MODEL_PATH)
                judge = StyleJudge(engine.llm)
            judge_inst = judge
        
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
            if actual_engine == "local":
                async with model_lock:
                    discipline = await asyncio.to_thread(
                        judge_inst.detect_discipline, req.text, actual_engine, req.api_key, req.base_url
                    )
            else:
                discipline = await asyncio.to_thread(
                    judge_inst.detect_discipline, req.text, actual_engine, req.api_key, req.base_url
                )
        except Exception as e:
            print(f"Discipline detection failed: {e}. Falling back to keywords.")
            text_lower = req.text.lower()
            if any(w in text_lower for w in ["управление", "робот", "автоматиз", "регулятор", "динамик", "control", "robot", "automat", "cybernetic", "feedback"]):
                discipline = "AUTOMATION_CONTROL"
            elif any(w in text_lower for w in ["биолог", "медиц", "клетк", "терап", "ген", "biolog", "medic", "cell", "gene", "patient", "clinical", "dna", "rna"]):
                discipline = "AGRI_MED"
            elif any(w in text_lower for w in ["физик", "хими", "сплав", "материал", "энерг", "physic", "chemic", "material", "alloy", "thermodynamic", "mechanic"]):
                discipline = "SCI_TECH"
            elif any(w in text_lower for w in ["эконом", "полити", "гуманитар", "истори", "обществ", "econom", "polit", "social", "humanit", "history", "societ"]):
                discipline = "HUM_POL_ECON"
            else:
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
    
    global engine, judge, citation_judge_global
    
    engine_inst = None
    if os.path.exists(MODEL_PATH):
        if engine is None:
            engine = PPLEngine(MODEL_PATH)
        engine_inst = engine
        
    if engine_type == "local":
        if engine_inst:
            if judge is None:
                judge = StyleJudge(engine_inst.llm)
            judge_inst = judge
        else:
            async def error_generator():
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Local model not found. Please download it first."})
                }
            return EventSourceResponse(error_generator())
    else:
        judge_inst = StyleJudge(None)
        
    citation_judge = None
    if os.path.exists(MODEL_PATH):
        if citation_judge_global is None:
            from naturalization_layer.nli_judge import NLICitationJudge
            if engine_inst:
                citation_judge_global = NLICitationJudge(engine_inst.llm)
        citation_judge = citation_judge_global
        
    if not citation_judge:
        from naturalization_layer.nli_judge import NLICitationJudge
        citation_judge = NLICitationJudge(None)

    if session_id not in session_references:
        session_references[session_id] = {
            "bibtex": {},
            "corpus": {},
            "retrievers": {},
            "online_cache": {},
            "bib_mapping": {}
        }
    if "online_cache" not in session_references[session_id]:
        session_references[session_id]["online_cache"] = {}
    from naturalization_layer.citation_integrity import extract_bibliography_mapping
    session_references[session_id]["bib_mapping"] = extract_bibliography_mapping(text)

    from services.diagnostic_service import run_sentence_diagnose_stream

    async def event_generator():
        try:
            async for result in run_sentence_diagnose_stream(
                text=text,
                session_id=session_id,
                engine_type=engine_type,
                api_key=api_key,
                base_url=base_url,
                discipline=discipline,
                engine_inst=engine_inst,
                judge_inst=judge_inst,
                citation_judge=citation_judge
            ):
                yield result
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
