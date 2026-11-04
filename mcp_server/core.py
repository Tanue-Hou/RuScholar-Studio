"""Plain async/sync functions behind the MCP tools (also importable directly, e.g. by tests)."""
import asyncio
import os

from naturalization_layer.citation_integrity import check_citation_integrity, extract_bibliography_mapping
from naturalization_layer.llm_client import cloud_model_for
from naturalization_layer.rules_engine import analyze_text_rules
from services.citation_audit_service import perform_nli_citation_audit, resolve_reference
from services.diagnostic_service import get_discipline_rules, run_sentence_diagnose_batch
from services.model_registry import registry
from services.reference_service import (
    ensure_reference_session, ingest_bibtex, ingest_reference_document,
    list_reference_keys, reset_reference_session,
)
from services.report_service import export_report_data
from services.shared_state import MODEL_PATH, session_references
from mcp_server import app


async def analyze_manuscript(
    text: str,
    session_id: str = "mcp_session",
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = "",
    discipline: str = None
) -> list[dict]:
    engine_inst, judge_inst, cit_judge = app.get_engines(engine_type)

    # 1. Resolve discipline
    if not discipline or discipline == "UNIVERSAL":
        use_cloud = bool(api_key and api_key.strip())
        actual_engine = cloud_model_for(engine_type) if use_cloud else "local"
        try:
            if actual_engine == "local" and not engine_inst:
                discipline_str = "UNIVERSAL"
            else:
                discipline_str = await asyncio.to_thread(
                    judge_inst.detect_discipline, text, actual_engine, api_key, base_url
                )
        except Exception:
            discipline_str = "UNIVERSAL"
    else:
        discipline_str = discipline

    # 2. Run diagnostics
    return await run_sentence_diagnose_batch(
        text=text,
        session_id=session_id,
        engine_type=engine_type,
        api_key=api_key,
        base_url=base_url,
        discipline=discipline_str,
        engine_inst=engine_inst,
        judge_inst=judge_inst,
        citation_judge=cit_judge
    )

async def audit_citations(
    text: str,
    session_id: str = "mcp_session",
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = ""
) -> dict:
    # 1. Global consistency check
    integrity_report = check_citation_integrity(text)

    # 2. Map numbered citations to the manuscript's bibliography
    ensure_reference_session(session_id)["bib_mapping"] = extract_bibliography_mapping(text)

    # 3. Retrieve engine for citation NLI verification
    _, _, cit_judge = app.get_engines(engine_type)

    # 4. Perform sentence-level citation audits
    all_sentence_audits = []
    for s in analyze_text_rules(text)["sentences"]:
        audits = await perform_nli_citation_audit(
            s, session_id, engine_type, api_key, base_url, cit_judge
        )
        if audits:
            all_sentence_audits.append({"sentence": s, "audits": audits})

    return {
        "integrity_warnings": integrity_report.get("warnings", []),
        "sentence_citation_audits": all_sentence_audits
    }

async def retrieve_evidence(
    claim: str,
    citation_key: str,
    session_id: str = "mcp_session"
) -> dict:
    ref = await resolve_reference(session_references.get(session_id, {}), citation_key, claim)
    return {"citation_key": citation_key, **ref}

async def suggest_revision(
    sentence: str,
    discipline: str,
    context_before: str = "",
    context_after: str = "",
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = ""
) -> dict:
    engine_inst, judge_inst, cit_judge = app.get_engines(engine_type)

    # Analyze text rules to find any Track A triggers
    rules_res = analyze_text_rules(sentence)
    diag_rules = rules_res["sentence_diagnostics"][0] if rules_res["sentence_diagnostics"] else {}

    active_rules = get_discipline_rules(discipline)

    diag = await asyncio.to_thread(
        judge_inst.diagnose_sentence,
        sentence,
        stats=diag_rules,
        ppl=None,
        context_before=[context_before] if context_before else [],
        context_after=[context_after] if context_after else [],
        skill_rules=active_rules,
        engine_type=engine_type,
        api_key=api_key,
        base_url=base_url
    )

    # Return formatted suggestion
    issues = diag.get("issues", [])
    if issues:
        issue = issues[0]
        return {
            "sentence": sentence,
            "status": "flagged",
            "issue_type": issue.get("issue_type"),
            "severity": issue.get("severity"),
            "explanation": issue.get("explanation_zh"),
            "rewrite_suggestion": issue.get("rewrite_suggestion"),
            "think": diag.get("think", "")
        }
    return {
        "sentence": sentence,
        "status": "passed",
        "explanation": "No major stylistic issue detected.",
        "rewrite_suggestion": sentence,
        "think": diag.get("think", "")
    }

def export_report(
    diagnostics: list[dict],
    citations: list[dict] = None,
    format: str = "markdown"
) -> str:
    return export_report_data(diagnostics, citations, format)

def check_model_installed() -> dict:
    from naturalization_layer.model_downloader import EXPECTED_SIZE
    if os.path.exists(MODEL_PATH):
        size = os.path.getsize(MODEL_PATH)
        if size == EXPECTED_SIZE:
            return {
                "installed": True,
                "model_path": MODEL_PATH,
                "size_bytes": size,
                "expected_size_bytes": EXPECTED_SIZE,
                "message": "Local model is installed and verified."
            }
        return {
            "installed": False,
            "model_path": MODEL_PATH,
            "size_bytes": size,
            "expected_size_bytes": EXPECTED_SIZE,
            "message": f"Local model file exists but has incorrect size ({size} bytes, expected {EXPECTED_SIZE} bytes)."
        }
    return {
        "installed": False,
        "model_path": MODEL_PATH,
        "size_bytes": 0,
        "expected_size_bytes": EXPECTED_SIZE,
        "message": f"Local model not found at '{MODEL_PATH}'. Please call 'download_model_tool' to download it."
    }

async def download_model_tool() -> dict:
    from naturalization_layer.model_downloader import download_model
    try:
        await asyncio.to_thread(download_model, MODEL_PATH)
        registry.reset()  # pick up the new file on next use
        return {
            "status": "success",
            "model_path": MODEL_PATH,
            "message": "Model downloaded successfully! You can now use local engine_type for offline diagnostics."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to download model: {str(e)}"
        }

async def register_references(
    session_id: str,
    bibtex_text: str = "",
    pdf_paths: list[str] = None
) -> dict:
    ensure_reference_session(session_id)

    bib_keys_added = []
    if bibtex_text and bibtex_text.strip():
        try:
            bib_keys_added = ingest_bibtex(session_id, bibtex_text)
        except Exception as e:
            raise ValueError(f"Failed to parse BibTeX: {str(e)}")

    pdf_keys_added = []
    for path in pdf_paths or []:
        if not os.path.exists(path):
            raise FileNotFoundError(f"PDF file not found at path: {path}")
        try:
            with open(path, "rb") as f:
                contents = f.read()
        except Exception as e:
            raise IOError(f"Failed to read file {path}: {str(e)}")
        try:
            key = ingest_reference_document(session_id, os.path.basename(path), contents)
        except Exception as e:
            raise IOError(f"Failed to parse {os.path.basename(path)}: {str(e)}")
        if key:
            pdf_keys_added.append(key)

    totals = list_reference_keys(session_id)
    return {
        "status": "success",
        "bibtex_keys_added": bib_keys_added,
        "pdf_keys_added": pdf_keys_added,
        "total_bibtex_keys": totals["bibtex_keys"],
        "total_pdf_keys": totals["pdf_keys"]
    }

def clear_references(session_id: str) -> dict:
    if reset_reference_session(session_id):
        return {"status": "success", "message": f"References for session '{session_id}' cleared."}
    return {"status": "success", "message": f"Session '{session_id}' was not initialized or already empty."}

def list_references(session_id: str) -> dict:
    return {"session_id": session_id, **list_reference_keys(session_id)}
