import os
import sys
import json
import asyncio
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
global_skill_rules = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, judge, global_skill_rules
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
                clusters = rules_data.get("clusters", {})
                # Try to load AUTOMATION_CONTROL or default to first
                global_skill_rules = clusters.get("AUTOMATION_CONTROL", next(iter(clusters.values()), None))
                print("Loaded phd-thesis-butler polishing rules.")
        except Exception as e:
            print(f"Failed to load skill rules: {e}")
            
    if not global_skill_rules:
        # Robust fallback if file doesn't exist
        global_skill_rules = {
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

@app.get("/api/diagnose")
async def diagnose_stream(text: str):
    """
    Server-Sent Events endpoint to stream the analysis of sentences.
    Accepts raw text (URL encoded).
    """
    async def event_generator():
        # 1. Run Rules Engine
        rules_res = analyze_text_rules(text)
        sentences = rules_res["sentences"]
        
        # Send initial metadata
        yield {
            "event": "init",
            "data": json.dumps({"total_sentences": len(sentences)})
        }
        
        # 2. Iterate and process each sentence
        for i, s in enumerate(sentences):
            diag_rules = rules_res["sentence_diagnostics"][i]
            run_ppl = should_run_ppl_heuristic(diag_rules, "Smart Probe")
            
            result = {
                "index": i,
                "text": s,
                "ppl": None,
                "issue_type": None,
                "severity": None,
                "explanation": None,
                "suggestion": None,
                "think": None,
                "status": "ok"
            }
            
            if not run_ppl or not engine:
                result["status"] = "skipped_heuristic"
                yield {"event": "result", "data": json.dumps(result)}
                continue
                
            has_track_a_triggers = (
                len(diag_rules.get("cliches_found", [])) > 0 or
                len(diag_rules.get("genitive_chains", [])) > 0 or
                diag_rules.get("nv_ratio", 0.0) > 4.0 or
                diag_rules.get("passive_count", 0) > 0
            )
            
            ee_tokens = 6 if not has_track_a_triggers else 0
            ee_lower = 15.0 if not has_track_a_triggers else 0.0
            ee_upper = 80.0 if not has_track_a_triggers else float('inf')
            
            # Run inference in threadpool to not block async loop
            ppl, was_early_exited = await asyncio.to_thread(
                engine.evaluate_sentence_ppl, s, ee_tokens, ee_lower, ee_upper
            )
            
            result["ppl"] = round(ppl, 2) if ppl else None
            
            if was_early_exited:
                result["status"] = "early_exit"
            else:
                is_suspicious = ppl < 15.0 or ppl > 80.0 or has_track_a_triggers
                if is_suspicious:
                    # Extract context
                    ctx_before = sentences[max(0, i-2):i]
                    ctx_after = sentences[i+1:min(len(sentences), i+3)]
                    
                    diag = await asyncio.to_thread(
                        judge.diagnose_sentence, 
                        s, 
                        stats=diag_rules, 
                        ppl=ppl, 
                        context_before=ctx_before, 
                        context_after=ctx_after,
                        skill_rules=global_skill_rules
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
                    
            yield {"event": "result", "data": json.dumps(result)}
            # Brief pause to allow event loop to breathe
            await asyncio.sleep(0.01)
            
        yield {"event": "done", "data": "[]"}
        
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
