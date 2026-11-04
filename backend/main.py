"""
FastAPI adapter for the Web UI. All logic lives in services/; this module only
maps HTTP requests onto it.
"""
import asyncio
import json
import os
import sys
import traceback
import uuid
from contextlib import asynccontextmanager

if __package__ in (None, ""):
    # Started as a script (`python backend/main.py`): make the project root
    # importable. Installed (`pip install -e .`) or `python -m backend.main`
    # runs need nothing here.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from naturalization_layer.citation_integrity import extract_bibliography_mapping
from naturalization_layer.discipline import detect_discipline_by_keywords
from naturalization_layer.document_parser import parse_document_bytes
from naturalization_layer.llm_client import cloud_model_for
from naturalization_layer.llm_judge import StyleJudge
from services.citation_audit_service import extract_citation_keys  # noqa: F401  (re-export, used by tests)
from services.diagnostic_service import run_sentence_diagnose_stream
from services.model_registry import registry
from services.reference_service import (
    ensure_reference_session, ingest_bibtex, ingest_reference_document, list_reference_keys,
)
from services.rules_config import get_calibration_db, get_rule_clusters
from services.settings import settings
from services.shared_state import pending_analyses


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_rule_clusters()
    get_calibration_db()
    print("Loading local model (if present)...")
    engine = await asyncio.to_thread(registry.get_engine)
    if engine is not None:
        print("Model loaded successfully.")
    elif registry.model_exists():
        print(f"Local model failed to load ({registry.load_error}). Running in Heuristics-only mode.")
    else:
        print(f"Model not found at {registry.model_path}. Running in Heuristics-only mode.")
    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

# The built frontend is served from this same origin, so CORS is only needed
# for the Vite dev server. Extra origins: comma-separated RUSCHOLAR_CORS_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


async def _read_upload(file: UploadFile) -> bytes:
    """Read an upload, refusing anything above RUSCHOLAR_MAX_UPLOAD_MB."""
    limit = settings.max_upload_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"{file.filename} is larger than {limit // (1024 * 1024)} MB (RUSCHOLAR_MAX_UPLOAD_MB).",
        )
    return data


def _sse_error(message: str) -> EventSourceResponse:
    async def gen():
        yield {"event": "error", "data": json.dumps({"error": message})}
    return EventSourceResponse(gen())


@app.post("/api/upload_references")
async def upload_references(
    session_id: str = Form(...),
    bibtex: str = Form(""),
    files: list[UploadFile] = File([])
):
    ensure_reference_session(session_id)
    try:
        ingest_bibtex(session_id, bibtex)
    except Exception as e:
        print(f"Failed to parse BibTeX: {e}")

    for file in files:
        contents = await _read_upload(file)
        try:
            ingest_reference_document(session_id, file.filename, contents)
        except Exception as e:
            print(f"Failed to parse reference file {file.filename}: {e}")

    keys = list_reference_keys(session_id)
    return {"status": "ok", "bibtex_keys": keys["bibtex_keys"], "pdf_keys": keys["pdf_keys"]}


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    contents = await _read_upload(file)
    try:
        text = parse_document_bytes(file.filename, contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read {file.filename}: {e}")
    return {"status": "ok", "filename": file.filename, "text": text}


class DetectDisciplineRequest(BaseModel):
    text: str
    engine_type: str = "local"
    api_key: str = ""
    base_url: str = ""


@app.post("/api/detect_discipline")
async def detect_discipline_endpoint(req: DetectDisciplineRequest):
    """
    Zero-shot academic discipline classification (first 1000 characters).
    Cloud if the request carries an API key, else the local model, else keywords.
    """
    if req.api_key and req.api_key.strip():
        model, judge = cloud_model_for(req.engine_type), StyleJudge(None)
    else:
        engine = await asyncio.to_thread(registry.get_engine)
        model, judge = "local", (registry.get_style_judge("local") if engine else None)

    if judge is None:
        return {"discipline": detect_discipline_by_keywords(req.text)}

    try:
        if model == "local":
            async with registry.model_lock:
                discipline = await asyncio.to_thread(
                    judge.detect_discipline, req.text, model, req.api_key, req.base_url
                )
        else:
            discipline = await asyncio.to_thread(
                judge.detect_discipline, req.text, model, req.api_key, req.base_url
            )
    except Exception as e:
        print(f"Discipline detection failed: {e}. Falling back to keywords.")
        discipline = detect_discipline_by_keywords(req.text)
    return {"discipline": discipline}


class SessionRequest(BaseModel):
    text: str
    engine_type: str = "local"
    api_key: str = ""
    base_url: str = ""
    discipline: str = "UNIVERSAL"


@app.post("/api/session")
async def create_session(req: SessionRequest):
    session_id = str(uuid.uuid4())
    pending_analyses[session_id] = req.model_dump()
    return {"session_id": session_id}


@app.get("/api/diagnose")
async def diagnose_stream(session_id: str):
    """
    Server-Sent Events stream of sentence diagnostics for a session created
    via POST /api/session. Each session can be streamed once.
    """
    session = pending_analyses.get(session_id)
    if not session:
        return _sse_error("Session expired or not found.")

    engine_type = session["engine_type"]
    engine_inst, judge_inst, citation_judge = await asyncio.to_thread(registry.get_judges, engine_type)
    if engine_type == "local" and engine_inst is None:
        print("Local GGUF model unavailable, falling back to Heuristic mode.")

    refs = ensure_reference_session(session_id)
    refs["bib_mapping"] = extract_bibliography_mapping(session["text"])

    async def event_generator():
        try:
            async for result in run_sentence_diagnose_stream(
                text=session["text"],
                session_id=session_id,
                engine_type=engine_type,
                api_key=session["api_key"],
                base_url=session["base_url"],
                discipline=session["discipline"],
                engine_inst=engine_inst,
                judge_inst=judge_inst,
                citation_judge=citation_judge
            ):
                yield result
        except Exception as e:
            traceback.print_exc()
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
        finally:
            pending_analyses.pop(session_id, None)

    return EventSourceResponse(event_generator())


@app.get("/api/check_model")
async def check_model():
    return {"exists": registry.model_exists()}


@app.post("/api/download_model")
async def download_model_endpoint():
    async def event_generator():
        try:
            current_progress = 0

            def progress_callback(progress: float):
                nonlocal current_progress
                current_progress = progress * 100

            from naturalization_layer.model_downloader import download_model

            # Download in a background thread to keep the event loop free
            task = asyncio.create_task(
                asyncio.to_thread(download_model, registry.model_path, progress_callback)
            )

            last_yielded = -1
            while not task.done():
                if int(current_progress) != last_yielded:
                    last_yielded = int(current_progress)
                    yield {"data": json.dumps({"status": "downloading", "progress": current_progress})}
                await asyncio.sleep(0.5)

            await task
            registry.reset()  # pick up the new file on next use
            yield {"data": json.dumps({"status": "complete"})}
        except Exception as e:
            traceback.print_exc()
            yield {"data": json.dumps({"status": "error", "message": str(e)})}

    return EventSourceResponse(event_generator())


# Serve frontend build statically
frontend_dist = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
else:
    print(f"Warning: Frontend build directory not found at {frontend_dist}. Please run `npm run build` in the frontend directory.")

def run() -> None:
    """Console entry point: `ruscholar-web` (or `python -m backend.main`)."""
    import uvicorn
    # Loopback by default (see services/settings.py): manuscripts are private.
    # Set RUSCHOLAR_RELOAD=1 for auto-reload during development.
    reload = os.getenv("RUSCHOLAR_RELOAD", "") == "1"
    uvicorn.run("backend.main:app", host=settings.host, port=settings.port, reload=reload)


if __name__ == "__main__":
    run()
