import sys
import os
import asyncio
from services.shared_state import session_references, MODEL_PATH
from naturalization_layer.ppl_engine import PPLEngine
from naturalization_layer.llm_judge import StyleJudge
from naturalization_layer.nli_judge import NLICitationJudge
from naturalization_layer.citation_integrity import check_citation_integrity, extract_bibliography_mapping
from services.diagnostic_service import run_sentence_diagnose_batch
from services.citation_audit_service import perform_nli_citation_audit
from services.report_service import export_report_data
from services.diagnostic_service import get_discipline_rules
from naturalization_layer.rules_engine import analyze_text_rules

# Import FastMCP
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("PhD Thesis Butler MCP Server")

# Lazily initialized model instances
engine = None
judge = None
citation_judge = None

def get_engines(engine_type: str):
    global engine, judge, citation_judge
    
    # Check if local model file exists
    if os.path.exists(MODEL_PATH):
        if engine is None:
            engine = PPLEngine(MODEL_PATH)
        engine_inst = engine
    else:
        engine_inst = None

    if engine_type == "local":
        if engine_inst:
            if judge is None:
                judge = StyleJudge(engine_inst.llm)
            judge_inst = judge
        else:
            raise ValueError(f"Local model not found at {MODEL_PATH}. Please download it first or use hybrid/cloud modes.")
    else:
        judge_inst = StyleJudge(None)

    if os.path.exists(MODEL_PATH):
        if citation_judge is None:
            if engine_inst:
                citation_judge = NLICitationJudge(engine_inst.llm)
    if citation_judge is None:
        citation_judge = NLICitationJudge(None)

    return engine_inst, judge_inst, citation_judge

@mcp.tool()
async def analyze_manuscript(
    text: str,
    session_id: str = "mcp_session",
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = "",
    discipline: str = None
) -> list[dict]:
    """
    Analyze manuscript text for style issues, formula markings, translationese, and predictability.
    
    Args:
        text: Full manuscript text or paragraphs to analyze.
        session_id: Session identifier to bind uploaded references.
        engine_type: Mode to run diagnostics: 'local' (offline), 'hybrid-pro', 'hybrid-flash', 'cloud-pro', 'cloud-flash'.
        api_key: Remote LLM API Key (if using hybrid or cloud mode).
        base_url: Remote LLM API base URL.
        discipline: Optional academic discipline (e.g. AUTOMATION_CONTROL, AGRI_MED, SCI_TECH, HUM_POL_ECON). If not provided, it will be auto-detected.
    """
    # Initialize engines
    engine_inst, judge_inst, cit_judge = get_engines(engine_type)
    
    # 1. Resolve discipline
    if not discipline or discipline == "UNIVERSAL":
        use_cloud = bool(api_key and api_key.strip())
        actual_engine = ("deepseek-v4-flash" if "flash" in engine_type else "deepseek-v4-pro") if use_cloud else "local"
        
        try:
            if actual_engine == "local" and not engine_inst:
                discipline = "UNIVERSAL"
            else:
                discipline = await asyncio.to_thread(
                    judge_inst.detect_discipline, text, actual_engine, api_key, base_url
                )
        except Exception:
            discipline = "UNIVERSAL"

    # 2. Run diagnostics
    results = await run_sentence_diagnose_batch(
        text=text,
        session_id=session_id,
        engine_type=engine_type,
        api_key=api_key,
        base_url=base_url,
        discipline=discipline,
        engine_inst=engine_inst,
        judge_inst=judge_inst,
        citation_judge=cit_judge
    )
    return results

@mcp.tool()
async def audit_citations(
    text: str,
    session_id: str = "mcp_session",
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = ""
) -> dict:
    """
    Perform a cross-consistency check of brackets citation keys and bibliography entries,
    detecting citation gaps, hallucinated reference listings, and support logical status via NLI.
    
    Args:
        text: Manuscript text containing references list at the end.
        session_id: Session identifier.
        engine_type: Inference mode.
        api_key: Remote API Key.
        base_url: Remote base URL.
    """
    # 1. Global consistency check
    integrity_report = check_citation_integrity(text)
    
    # 2. Initialize mapping in session references
    if session_id not in session_references:
        session_references[session_id] = {
            "bibtex": {},
            "corpus": {},
            "retrievers": {},
            "online_cache": {},
            "bib_mapping": {}
        }
    session_references[session_id]["bib_mapping"] = extract_bibliography_mapping(text)
    
    # 3. Retrieve engine for citation NLI verification
    engine_inst, judge_inst, cit_judge = get_engines(engine_type)
    
    # 4. Perform sentence-level citation audits
    from naturalization_layer.rules_engine import analyze_text_rules
    rules_res = analyze_text_rules(text)
    sentences = rules_res["sentences"]
    
    all_sentence_audits = []
    for s in sentences:
        audits = await perform_nli_citation_audit(
            s, session_id, engine_type, api_key, base_url, cit_judge
        )
        if audits:
            all_sentence_audits.append({
                "sentence": s,
                "audits": audits
            })
            
    return {
        "integrity_warnings": integrity_report.get("warnings", []),
        "sentence_citation_audits": all_sentence_audits
    }

@mcp.tool()
async def retrieve_evidence(
    claim: str,
    citation_key: str,
    session_id: str = "mcp_session"
) -> dict:
    """
    Retrieve specific snippets or citation abstract details associated with a claim from
    the session references (local chunk corpus or OpenAlex database search).
    
    Args:
        claim: The statement or assertion in the text.
        citation_key: Citation key (e.g. '1', 'ivanov2022').
        session_id: Session identifier.
    """
    session_ref = session_references.get(session_id, {})
    retrievers = session_ref.get("retrievers", {})
    bibtex_db = session_ref.get("bibtex", {})
    online_cache = session_ref.get("online_cache", {})
    bib_mapping = session_ref.get("bib_mapping", {})
    
    key_lower = citation_key.lower()
    snippets = []
    title = f"文献 {citation_key}"
    author = ""
    year = ""
    source = "unknown"
    
    # 1. Local retriever check
    if key_lower in retrievers:
        retriever = retrievers[key_lower]
        retrieved = retriever.retrieve(claim, top_k=3)
        snippets = [r["text"] for r in retrieved]
        source = "local"
        meta = bibtex_db.get(key_lower, {})
        title = meta.get("title", title)
        author = meta.get("author", "")
        year = meta.get("year", "")
    else:
        # 2. Check online cache / retrieve
        if key_lower in online_cache:
            cache_entry = online_cache[key_lower]
            if cache_entry:
                snippets = [cache_entry["abstract"]] if cache_entry["abstract"] else []
                title = cache_entry["title"]
                source = "online"
        else:
            query_str = ""
            if key_lower in bibtex_db:
                meta = bibtex_db[key_lower]
                query_str = f"{meta.get('title', '')} {meta.get('author', '')} {meta.get('year', '')}".strip()
            elif key_lower in bib_mapping:
                query_str = bib_mapping[key_lower]
                
            if query_str:
                from naturalization_layer.rag_retriever import fetch_openalex_abstract
                online_res = await asyncio.to_thread(fetch_openalex_abstract, query_str)
                if online_res:
                    online_cache[key_lower] = online_res
                    snippets = [online_res["abstract"]] if online_res["abstract"] else []
                    title = online_res["title"]
                    source = "online"
                    
    return {
        "citation_key": citation_key,
        "title": title,
        "author": author,
        "year": year,
        "snippets": snippets,
        "source": source
    }

@mcp.tool()
async def suggest_revision(
    sentence: str,
    discipline: str,
    context_before: str = "",
    context_after: str = "",
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = ""
) -> dict:
    """
    Suggest revision and Russian academic polishing rewrite for a sentence.
    
    Args:
        sentence: The draft sentence to refine.
        discipline: Discipline category (e.g. AUTOMATION_CONTROL, AGRI_MED, SCI_TECH, HUM_POL_ECON).
        context_before: Surrounding preceding text (optional).
        context_after: Surrounding succeeding text (optional).
        engine_type: Local or cloud engine type.
        api_key: API key.
        base_url: Base URL.
    """
    engine_inst, judge_inst, cit_judge = get_engines(engine_type)
    
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
    else:
        return {
            "sentence": sentence,
            "status": "passed",
            "explanation": "No major stylistic issue detected.",
            "rewrite_suggestion": sentence,
            "think": diag.get("think", "")
        }

@mcp.tool()
def export_report(
    diagnostics: list[dict],
    citations: list[dict] = None,
    format: str = "markdown"
) -> str:
    """
    Export structural diagnostics and citation audit results as a beautiful report.
    
    Args:
        diagnostics: List of sentence-level diagnostic dicts.
        citations: List of citation audit results.
        format: Export format: 'markdown' or 'json'.
    """
    return export_report_data(diagnostics, citations, format)

if __name__ == "__main__":
    mcp.run(transport="stdio")
