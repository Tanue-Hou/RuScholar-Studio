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

mcp = FastMCP("RuScholar Studio MCP Server")

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
            raise ValueError(
                f"Local model not found at '{MODEL_PATH}'. "
                f"To resolve this, you can call the MCP tool 'thesis_download_model_tool' to download it automatically, "
                f"or run the following command in your terminal to download manually: "
                f"python -c \"from naturalization_layer.model_downloader import download_model, MODEL_PATH; download_model(MODEL_PATH)\""
            )
    else:
        judge_inst = StyleJudge(None)

    if os.path.exists(MODEL_PATH):
        if citation_judge is None:
            if engine_inst:
                citation_judge = NLICitationJudge(engine_inst.llm)
    if citation_judge is None:
        citation_judge = NLICitationJudge(None)

    return engine_inst, judge_inst, citation_judge

from enum import Enum

class EngineType(str, Enum):
    local = "local"
    hybrid_pro = "hybrid-pro"
    hybrid_flash = "hybrid-flash"
    cloud_pro = "cloud-pro"
    cloud_flash = "cloud-flash"

class Discipline(str, Enum):
    sci_tech = "SCI_TECH"
    automation_control = "AUTOMATION_CONTROL"
    agri_med = "AGRI_MED"
    hum_pol_econ = "HUM_POL_ECON"
    arts_sports = "ARTS_SPORTS"
    universal = "UNIVERSAL"

class ReportFormat(str, Enum):
    markdown = "markdown"
    json = "json"

# ==========================================
# CORE PYTHON FUNCTIONS (Original Signatures for Compatibility & Tests)
# ==========================================

async def analyze_manuscript(
    text: str,
    session_id: str = "mcp_session",
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = "",
    discipline: str = None
) -> list[dict]:
    # Initialize engines
    engine_inst, judge_inst, cit_judge = get_engines(engine_type)
    
    # 1. Resolve discipline
    if not discipline or discipline == "UNIVERSAL":
        use_cloud = bool(api_key and api_key.strip())
        actual_engine = ("deepseek-v4-flash" if "flash" in engine_type else "deepseek-v4-pro") if use_cloud else "local"
        
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
    results = await run_sentence_diagnose_batch(
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
    return results

async def audit_citations(
    text: str,
    session_id: str = "mcp_session",
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = ""
) -> dict:
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

async def retrieve_evidence(
    claim: str,
    citation_key: str,
    session_id: str = "mcp_session"
) -> dict:
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

async def suggest_revision(
    sentence: str,
    discipline: str,
    context_before: str = "",
    context_after: str = "",
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = ""
) -> dict:
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
        else:
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
        
    bib_keys_added = []
    pdf_keys_added = []
    
    if bibtex_text and bibtex_text.strip():
        try:
            bib_entries = parse_bibtex(bibtex_text)
            session_references[session_id]["bibtex"].update(bib_entries)
            bib_keys_added = list(bib_entries.keys())
        except Exception as e:
            raise ValueError(f"Failed to parse BibTeX: {str(e)}")
            
    if pdf_paths:
        for path in pdf_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"PDF file not found at path: {path}")
            filename = os.path.basename(path)
            name_part, ext = os.path.splitext(filename)
            clean_name = re.sub(r'[\[\]]', '', name_part).strip().lower()
            
            try:
                with open(path, "rb") as f:
                    contents = f.read()
            except Exception as e:
                raise IOError(f"Failed to read file {path}: {str(e)}")
                
            text = ""
            if ext.lower() == ".pdf":
                try:
                    from pypdf import PdfReader
                    import io
                    reader = PdfReader(io.BytesIO(contents))
                    text = ""
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            text += t + "\n"
                except Exception as e:
                    raise IOError(f"Failed to parse PDF {filename}: {str(e)}")
            else:
                try:
                    text = contents.decode("utf-8")
                except Exception as e:
                    raise IOError(f"Failed to decode text file {filename}: {str(e)}")
                    
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
                pdf_keys_added.append(clean_name)
                
    return {
        "status": "success",
        "bibtex_keys_added": bib_keys_added,
        "pdf_keys_added": pdf_keys_added,
        "total_bibtex_keys": list(session_references[session_id]["bibtex"].keys()),
        "total_pdf_keys": list(session_references[session_id]["retrievers"].keys())
    }

def clear_references(session_id: str) -> dict:
    if session_id in session_references:
        session_references[session_id] = {
            "bibtex": {},
            "corpus": {},
            "retrievers": {},
            "online_cache": {},
            "bib_mapping": {}
        }
        return {"status": "success", "message": f"References for session '{session_id}' cleared."}
    return {"status": "success", "message": f"Session '{session_id}' was not initialized or already empty."}

def list_references(session_id: str) -> dict:
    session_ref = session_references.get(session_id, {})
    return {
        "session_id": session_id,
        "bibtex_keys": list(session_ref.get("bibtex", {}).keys()),
        "pdf_keys": list(session_ref.get("retrievers", {}).keys())
    }

# ==========================================
# DECORATED MCP TOOLS (New Thesis prefixed APIs returning uniform schemas)
# ==========================================

@mcp.tool()
async def thesis_route_workflow(
    user_request: str,
    text_sample: str = "",
    assets_available: list[str] = None,
    engine_type: EngineType = EngineType.local,
    api_key: str = "",
    base_url: str = ""
) -> dict:
    """
    Route a user request to the correct Russian PhD dissertation workflow.
    
    Args:
        user_request: The prompt, query, or instruction from the user.
        text_sample: Optional pasted manuscript draft or outline sample.
        assets_available: Optional list of available files/assets in the session.
        engine_type: Inference mode for LLM classification fallback.
        api_key: API key for remote model.
        base_url: Base URL for remote model.
    """
    req_lower = user_request.lower()
    
    # 1. Rule-based Heuristic router
    detected_workflow = None
    reason = ""
    evidence_keywords = []
    
    # Citation check keywords
    citation_kw = ["citation", "reference", "audit", "gap", "gost", "nli", "ссылк", "литератур", "библиограф", "гост", "ппл", "ppl", "проверить", "引用", "文献", "支撑"]
    # Landscape check keywords
    landscape_kw = ["dissercat", "zotero", "elibrary", "cyberleninka", "rsl", "landscape", "похожие", "диссертаци", "сравн", "обзор", "同方向", "对比", "文献调研", "别人怎么写"]
    # Planning check keywords
    planning_kw = ["structure", "plan", "chapter", "outline", "experiment", "methodology", "структур", "план", "глав", "эксперимент", "методологи", "введен", "актуальност", "новизн", "положен", "защит", "规划", "结构", "章节", "开题", "导师"]
    
    # Check citation
    for kw in citation_kw:
        if kw in req_lower:
            detected_workflow = "citation_audit"
            reason = f"Detected citation auditing intent via keyword '{kw}'"
            evidence_keywords.append(kw)
            break
            
    # Check landscape (has priority over planning if both match)
    if not detected_workflow:
        for kw in landscape_kw:
            if kw in req_lower:
                detected_workflow = "literature_landscape"
                reason = f"Detected literature review or landscape intent via keyword '{kw}'"
                evidence_keywords.append(kw)
                break
                
    # Check planning
    if not detected_workflow:
        for kw in planning_kw:
            if kw in req_lower:
                detected_workflow = "planning_and_structure"
                reason = f"Detected structural planning or dissertation design intent via keyword '{kw}'"
                evidence_keywords.append(kw)
                break
                
    # Default to polishing
    if not detected_workflow:
        detected_workflow = "polishing_and_style"
        reason = "No specific structural or citation keywords matched. Defaulting to Russian polishing and style naturalization."
        
    # 3. Map to workflow details and Tool Execution Plan
    workflows_map = {
        "polishing_and_style": {
            "name": "俄语润色与表达优化 (Russian Polishing & Expression Optimization)",
            "description": "Refines style, corrects noun stacking, passive voice, and aligns with Russian academic sentence templates.",
            "next_actions": ["thesis_analyze_manuscript", "thesis_suggest_revision"]
        },
        "planning_and_structure": {
            "name": "论文规划与结构设计 (Thesis Planning & Structure Design)",
            "description": "Helps design chapter outlines, methodology blueprints, and experiment matrices according to VAK requirements.",
            "next_actions": ["thesis_map_vak_specialty"]
        },
        "literature_landscape": {
            "name": "文献调研与同方向论文对比 (Literature Research & Landscape Comparison)",
            "description": "Searches, filters, and compares similar Russian dissertations and structures from Zotero or CyberLeninka.",
            "next_actions": ["thesis_register_references", "thesis_list_references"]
        },
        "citation_audit": {
            "name": "证据检查与引用修复 (Citation Audit & Verification)",
            "description": "Checks in-text citation coherence, references mapping, and audits claims using Natural Language Inference (NLI).",
            "next_actions": ["thesis_audit_citations", "thesis_retrieve_evidence"]
        }
    }
    
    selected = workflows_map[detected_workflow]
    
    return {
        "summary": f"User request routed to workflow: {selected['name']}",
        "findings": {
            "workflow": detected_workflow,
            "workflow_name": selected["name"],
            "description": selected["description"],
            "reason": reason
        },
        "evidence": {
            "detected_keywords": evidence_keywords,
            "user_request_length": len(user_request),
            "assets_available": assets_available or []
        },
        "next_actions": selected["next_actions"]
    }

@mcp.tool()
async def thesis_map_vak_specialty(
    topic: str,
    abstract: str = "",
    keywords: str = "",
    engine_type: EngineType = EngineType.local,
    api_key: str = "",
    base_url: str = ""
) -> dict:
    """
    Map a dissertation topic/abstract/keywords to the closest VAK specialty code.
    
    Args:
        topic: The title or topic of the dissertation.
        abstract: Optional abstract/summary of the work.
        keywords: Optional keywords list or comma-separated string.
        engine_type: Inference mode: 'local' (offline), 'hybrid-pro', etc.
        api_key: Remote LLM API Key (if using hybrid/cloud mode).
        base_url: Remote LLM API base URL.
    """
    from naturalization_layer.vak_specialty_mapper import map_vak_specialty, load_vak_nomenclature
    
    engine_type_str = engine_type.value if hasattr(engine_type, 'value') else engine_type
    
    # Get local LLM if using local mode
    llm_inst = None
    if engine_type_str == "local":
        try:
            engine_inst, _, _ = get_engines(engine_type_str)
            if engine_inst:
                llm_inst = engine_inst.llm
        except Exception:
            # Fallback to None (triggers keyword fallback inside map_vak_specialty)
            pass
            
    res = await map_vak_specialty(
        topic=topic,
        abstract=abstract,
        keywords=keywords,
        engine_type=engine_type_str,
        api_key=api_key,
        base_url=base_url,
        llm=llm_inst
    )
    
    # Load full details from nomenclature
    nomenclature = load_vak_nomenclature()
    matched_spec = next((s for s in nomenclature if s["code"] == res["code"]), nomenclature[0])
    
    return {
        "summary": f"Mapped to VAK specialty code {res['code']} ({matched_spec['name_ru']}) with confidence {res['confidence']:.2f}.",
        "findings": {
            "code": res["code"],
            "name_ru": matched_spec["name_ru"],
            "name_zh": matched_spec["name_zh"],
            "cluster": matched_spec["cluster"],
            "confidence": res["confidence"],
            "reasoning_zh": res["reasoning_zh"],
            "reasoning_ru": res["reasoning_ru"],
            "publications_min": matched_spec["publications_min"],
            "gost_structure": matched_spec["gost_structure"],
            "evidence_roles": matched_spec["evidence_roles"]
        },
        "evidence": {
            "topic": topic,
            "abstract": abstract,
            "keywords": keywords,
            "out_of_scope_warnings": matched_spec.get("out_of_scope", [])
        },
        "next_actions": ["thesis_analyze_manuscript", "thesis_audit_vak_gost_compliance"]
    }

@mcp.tool()
async def thesis_analyze_manuscript(
    text: str,
    session_id: str = "mcp_session",
    engine_type: EngineType = EngineType.local,
    api_key: str = "",
    base_url: str = "",
    discipline: Discipline = None
) -> dict:
    """
    Analyze manuscript text for style issues, formula markings, translationese, and predictability.
    
    Args:
        text: Full manuscript text or paragraphs to analyze.
        session_id: Session identifier to bind uploaded references.
        engine_type: Mode to run diagnostics: 'local' (offline), 'hybrid-pro', 'hybrid-flash', 'cloud-pro', 'cloud-flash'.
        api_key: Remote LLM API Key (if using hybrid or cloud mode).
        base_url: Remote LLM API base URL.
        discipline: Academic discipline. If not provided, it will be auto-detected.
    """
    engine_type_str = engine_type.value if hasattr(engine_type, 'value') else engine_type
    discipline_str = discipline.value if discipline and hasattr(discipline, 'value') else discipline
    
    results = await analyze_manuscript(
        text=text,
        session_id=session_id,
        engine_type=engine_type_str,
        api_key=api_key,
        base_url=base_url,
        discipline=discipline_str
    )
    
    return {
        "summary": f"Completed style diagnostics on {len(results)} sentences.",
        "findings": results,
        "evidence": {
            "total_sentences": len(results),
            "flagged_count": sum(1 for r in results if r.get("status") == "flagged")
        },
        "next_actions": ["thesis_suggest_revision", "thesis_export_report"]
    }

@mcp.tool()
async def thesis_audit_citations(
    text: str,
    session_id: str = "mcp_session",
    engine_type: EngineType = EngineType.local,
    api_key: str = "",
    base_url: str = ""
) -> dict:
    """
    Perform a cross-consistency check of brackets citation keys and bibliography entries,
    detecting citation gaps, hallucinated reference listings, and support logical status via NLI.
    
    Args:
        text: Manuscript text containing references list at the end.
        session_id: Session identifier.
        engine_type: Inference mode: 'local' (offline), 'hybrid-pro', 'hybrid-flash', 'cloud-pro', 'cloud-flash'.
        api_key: Remote API Key.
        base_url: Remote base URL.
    """
    engine_type_str = engine_type.value if hasattr(engine_type, 'value') else engine_type
    
    res = await audit_citations(
        text=text,
        session_id=session_id,
        engine_type=engine_type_str,
        api_key=api_key,
        base_url=base_url
    )
    
    return {
        "summary": f"Completed citation integrity audit. Found {len(res['integrity_warnings'])} integrity warnings and audited {len(res['sentence_citation_audits'])} sentences.",
        "findings": res,
        "evidence": {
            "total_audited_sentences": len(res['sentence_citation_audits'])
        },
        "next_actions": ["thesis_retrieve_evidence", "thesis_export_report"]
    }

@mcp.tool()
def thesis_extract_claims(text: str) -> dict:
    """
    Extract scientific claims from a manuscript draft and classify their claim types.
    
    Args:
        text: Paragraphs or full manuscript text.
    """
    from services.citation_audit_service import extract_claims
    claims = extract_claims(text)
    return {
        "summary": f"Extracted {len(claims)} scientific claims from draft.",
        "findings": claims,
        "evidence": {},
        "next_actions": ["thesis_classify_evidence_need", "thesis_bind_evidence"]
    }

@mcp.tool()
def thesis_classify_evidence_need(claim: str) -> dict:
    """
    Evaluate if a scientific assertion requires citation or external evidence support.
    
    Args:
        claim: A single sentence/claim to evaluate.
    """
    from services.citation_audit_service import classify_evidence_need
    res = classify_evidence_need(claim)
    return {
        "summary": f"Evidence need level for claim: {res['need_level'].upper()}",
        "findings": res,
        "evidence": {},
        "next_actions": ["thesis_bind_evidence"]
    }

@mcp.tool()
async def thesis_bind_evidence(
    claim: str,
    references: list[str],
    session_id: str = "mcp_session"
) -> dict:
    """
    Query local and online database sources to bind evidence snippets for the given claim.
    
    Args:
        claim: The assertion sentence.
        references: List of citation keys to query and bind (e.g. ['1', 'smith2022']).
        session_id: Session identifier.
    """
    from services.citation_audit_service import bind_evidence
    res = await bind_evidence(claim, references, session_id)
    return {
        "summary": f"Bound evidence for references: {', '.join(references)}",
        "findings": res["bound_references"],
        "evidence": {
            "claim": claim
        },
        "next_actions": ["thesis_judge_claim_evidence_nli"]
    }

@mcp.tool()
async def thesis_judge_claim_evidence_nli(
    claim: str,
    snippets: list[str],
    engine_type: EngineType = EngineType.local,
    api_key: str = "",
    base_url: str = ""
) -> dict:
    """
    Perform Natural Language Inference (NLI) logic verification to check if snippets support a claim.
    
    Args:
        claim: The scientific assertion.
        snippets: List of text snippets retrieved from the cited references.
        engine_type: Inference mode: 'local' (offline), 'hybrid-pro', etc.
        api_key: API key.
        base_url: Base URL.
    """
    engine_type_str = engine_type.value if hasattr(engine_type, 'value') else engine_type
    _, _, cit_judge = get_engines(engine_type_str)
    
    nli_res = await asyncio.to_thread(
        cit_judge.verify_citation,
        claim, snippets, engine_type_str, api_key, base_url
    )
    
    return {
        "summary": f"NLI verification status: {nli_res['status']}",
        "findings": {
            "status": nli_res["status"],
            "explanation_zh": nli_res["explanation_zh"],
            "evidence_snippet": nli_res["evidence_snippet"]
        },
        "evidence": {
            "claim": claim,
            "snippets": snippets,
            "think": nli_res.get("think")
        },
        "next_actions": ["thesis_suggest_revision"]
    }

@mcp.tool()
async def thesis_audit_vak_gost_compliance(
    manuscript: str,
    bibliography: str = "",
    vak_code: str = "",
    engine_type: EngineType = EngineType.local,
    api_key: str = "",
    base_url: str = ""
) -> dict:
    """
    Audit a PhD dissertation draft for VAK structure completeness, citation consistency, and GOST reference styling.
    
    Args:
        manuscript: The main text of the introduction or full dissertation.
        bibliography: Optional list of references. If omitted, they are extracted from the manuscript.
        vak_code: Optional VAK code (e.g. 2.3.1) to cross-validate publication requirements.
        engine_type: Inference mode: 'local' (offline), 'hybrid-pro', etc.
        api_key: API Key.
        base_url: Base URL.
    """
    import re
    from naturalization_layer.citation_integrity import check_citation_integrity
    
    # 1. VAK Heading Check
    VAK_HEADERS = {
        "relevance": {
            "patterns": [r"актуальность\s+темы", r"актуальность\s+исследования"],
            "name_zh": "研究课题紧迫性 (Актуальность темы)",
            "name_ru": "Актуальность темы исследования"
        },
        "degree_developed": {
            "patterns": [r"степень\s+разработанности"],
            "name_zh": "课题前沿研究程度 (Степень разработанности)",
            "name_ru": "Степень разработанности темы исследования"
        },
        "goal_tasks": {
            "patterns": [r"цель\s+и\s+задачи", r"цель\s+исследования", r"задачи\s+исследования"],
            "name_zh": "研究目标与任务 (Цель и задачи)",
            "name_ru": "Цель и задачи исследования"
        },
        "novelty": {
            "patterns": [r"научная\s+новизна"],
            "name_zh": "科学新颖性 (Научная новизна)",
            "name_ru": "Научная новизна результатов"
        },
        "significance": {
            "patterns": [r"теоретическая\s+и\s+практическая\s+значимость", r"теоретическая\s+значимость", r"практическая\s+значимость"],
            "name_zh": "理论与实践意义 (Теоретическая и практическая значимость)",
            "name_ru": "Теоретическая и практическая значимость"
        },
        "methodology": {
            "patterns": [r"методология\s+и\s+методы", r"методология\s+исследования", r"методы\s+исследования"],
            "name_zh": "研究方法与方法论 (Методология и методы)",
            "name_ru": "Методология и методы исследования"
        },
        "provisions": {
            "patterns": [r"положения,\s+выносимые\s+на\s+защиту", r"на\s+защиту\s+выносятся"],
            "name_zh": "答辩核心观点/要点 (Положения на защиту)",
            "name_ru": "Положения, выносимые на защиту"
        },
        "reliability": {
            "patterns": [r"достоверность\s+и\s+апробация", r"степень\s+достоверности", r"апробация\s+результатов", r"апробация\s+работы"],
            "name_zh": "结果可靠度与学术成果发表验证 (Достоверность и апробация)",
            "name_ru": "Степень достоверности и апробация результатов"
        }
    }
    
    vak_checks = {}
    missing_headers = []
    for key, info in VAK_HEADERS.items():
        found = False
        for pat in info["patterns"]:
            if re.search(pat, manuscript, re.IGNORECASE):
                found = True
                break
        vak_checks[key] = {
            "name_zh": info["name_zh"],
            "name_ru": info["name_ru"],
            "status": "passed" if found else "missing"
        }
        if not found:
            missing_headers.append(info["name_zh"])
            
    # 2. Reference consistency (pairing)
    pairing_res = check_citation_integrity(manuscript)
    
    # 3. GOST bibliography check
    bib_lines = []
    if bibliography and bibliography.strip():
        bib_lines = [line.strip() for line in bibliography.split("\n") if line.strip()]
    else:
        # Extract from manuscript text
        from naturalization_layer.citation_integrity import extract_bibliography_mapping
        mapping = extract_bibliography_mapping(manuscript)
        bib_lines = list(mapping.values())
        
    engine_type_str = engine_type.value if hasattr(engine_type, 'value') else engine_type
    
    llm_inst = None
    if engine_type_str == "local":
        try:
            engine_inst, _, _ = get_engines(engine_type_str)
            if engine_inst:
                llm_inst = engine_inst.llm
        except Exception:
            pass
            
    from naturalization_layer.gost_validator import check_gost_compliance
    gost_audits = []
    gost_scores = []
    for entry in bib_lines:
        res_gost = await check_gost_compliance(
            entry, engine_type_str, api_key, base_url, llm_inst
        )
        gost_scores.append(res_gost["score"])
        gost_audits.append({
            "original": entry,
            "score": res_gost["score"],
            "errors_zh": res_gost["errors_zh"],
            "errors_ru": res_gost["errors_ru"],
            "corrected": res_gost["corrected"]
        })
        
    avg_gost_score = sum(gost_scores) / len(gost_scores) if gost_scores else 100
    
    # 4. VAK specialty publications requirements check
    publication_warning = ""
    min_publications = 0
    if vak_code:
        from naturalization_layer.vak_specialty_mapper import load_vak_nomenclature
        try:
            nomenclature = load_vak_nomenclature()
            spec = next((s for s in nomenclature if s["code"] == vak_code), None)
            if spec:
                min_publications = spec["publications_min"]
                publication_warning = f"根据ВАК规定，专业方向 {vak_code} 要求在推荐期刊上至少发表 {min_publications} 篇论文。请核查您的论文发表清单。"
        except Exception:
            pass
            
    return {
        "summary": f"Completed VAK/GOST compliance audit. VAK structure: {len(missing_headers)} missing sections. Bibliography GOST score: {avg_gost_score:.1f}/100.",
        "findings": {
            "vak_structure_audit": vak_checks,
            "missing_vak_headers": missing_headers,
            "average_gost_score": avg_gost_score,
            "bibliography_gost_audit": gost_audits,
            "citation_integrity": pairing_res,
            "vak_code_requirements": {
                "vak_code": vak_code,
                "min_publications": min_publications,
                "publication_warning": publication_warning
            }
        },
        "evidence": {
            "manuscript_length": len(manuscript),
            "bibliography_entries_count": len(bib_lines)
        },
        "next_actions": ["thesis_suggest_revision", "thesis_export_report"]
    }



@mcp.tool()
async def thesis_retrieve_evidence(
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
    res = await retrieve_evidence(
        claim=claim,
        citation_key=citation_key,
        session_id=session_id
    )
    
    return {
        "summary": f"Retrieved {len(res['snippets'])} evidence snippets from {res['source']} for citation '{citation_key}'.",
        "findings": {
            "citation_key": citation_key,
            "title": res["title"],
            "author": res["author"],
            "year": res["year"],
            "source": res["source"]
        },
        "evidence": {
            "snippets": res["snippets"]
        },
        "next_actions": ["thesis_suggest_revision"]
    }

@mcp.tool()
async def thesis_suggest_revision(
    sentence: str,
    discipline: Discipline,
    context_before: str = "",
    context_after: str = "",
    engine_type: EngineType = EngineType.local,
    api_key: str = "",
    base_url: str = ""
) -> dict:
    """
    Suggest revision and Russian academic polishing rewrite for a sentence.
    
    Args:
        sentence: The draft sentence to refine.
        discipline: Academic discipline.
        context_before: Surrounding preceding text (optional).
        context_after: Surrounding succeeding text (optional).
        engine_type: Local or cloud engine type.
        api_key: API key.
        base_url: Base URL.
    """
    engine_type_str = engine_type.value if hasattr(engine_type, 'value') else engine_type
    discipline_str = discipline.value if hasattr(discipline, 'value') else discipline
    
    res = await suggest_revision(
        sentence=sentence,
        discipline=discipline_str,
        context_before=context_before,
        context_after=context_after,
        engine_type=engine_type_str,
        api_key=api_key,
        base_url=base_url
    )
    
    if res["status"] == "flagged":
        return {
            "summary": "Style issues detected, generated rewrite suggestion.",
            "findings": res,
            "evidence": {
                "think": res.get("think", "")
            },
            "next_actions": ["thesis_analyze_manuscript"]
        }
    else:
        return {
            "summary": "No major stylistic issue detected. Suggestion returned.",
            "findings": res,
            "evidence": {
                "think": res.get("think", "")
            },
            "next_actions": ["thesis_analyze_manuscript"]
        }

@mcp.tool()
def thesis_export_report(
    diagnostics: list[dict],
    citations: list[dict] = None,
    format: ReportFormat = ReportFormat.markdown
) -> dict:
    """
    Export structural diagnostics and citation audit results as a beautiful report.
    
    Args:
        diagnostics: List of sentence-level diagnostic dicts.
        citations: List of citation audit results.
        format: Export format: 'markdown' or 'json'.
    """
    format_str = format.value if hasattr(format, 'value') else format
    report_content = export_report(diagnostics, citations, format_str)
    return {
        "summary": f"Exported thesis audit report in {format_str} format.",
        "findings": {
            "format": format_str
        },
        "evidence": {
            "report_content": report_content
        },
        "next_actions": []
    }

@mcp.tool()
def thesis_check_model_installed() -> dict:
    """
    Check if the local Qwen GGUF model is installed and matches the expected file size.
    
    Returns:
        A dictionary containing:
        - installed (bool): Whether the model is present and correct.
        - model_path (str): File path to the model.
        - size_bytes (int): Current size of the file.
        - expected_size_bytes (int): Expected size of the file.
        - message (str): Friendly message describing the status.
    """
    res = check_model_installed()
    return {
        "summary": res["message"],
        "findings": {
            "installed": res["installed"],
            "model_path": res["model_path"]
        },
        "evidence": {
            "size_bytes": res["size_bytes"],
            "expected_size_bytes": res["expected_size_bytes"]
        },
        "next_actions": [] if res["installed"] else ["thesis_download_model_tool"]
    }

@mcp.tool()
async def thesis_download_model_tool() -> dict:
    """
    Automatically download the Qwen GGUF model (approx. 2.7 GB) from ModelScope to enable offline diagnostics.
    This tool saves the model to the local 'models/' directory.
    
    Returns:
        A dictionary indicating the download status, message, and path.
    """
    res = await download_model_tool()
    return {
        "summary": res["message"],
        "findings": {
            "status": res["status"]
        },
        "evidence": {
            "model_path": res.get("model_path", "")
        },
        "next_actions": ["thesis_check_model_installed"]
    }

@mcp.tool()
async def thesis_register_references(
    session_id: str,
    bibtex_text: str = "",
    pdf_paths: list[str] = None
) -> dict:
    """
    Register BibTeX text and/or local PDF paths to a session's reference library for citation auditing.
    
    Args:
        session_id: Session identifier to bind the references to.
        bibtex_text: Bibliography database entries in BibTeX format.
        pdf_paths: List of absolute file paths to PDF papers.
    """
    res = await register_references(
        session_id=session_id,
        bibtex_text=bibtex_text,
        pdf_paths=pdf_paths
    )
    return {
        "summary": f"Successfully registered references: {len(res['bibtex_keys_added'])} BibTeX keys, {len(res['pdf_keys_added'])} PDF keys.",
        "findings": {
            "status": res["status"]
        },
        "evidence": res,
        "next_actions": ["thesis_list_references", "thesis_audit_citations"]
    }

@mcp.tool()
def thesis_clear_references(session_id: str) -> dict:
    """
    Clear all registered references (BibTeX and PDFs) for the given session.
    
    Args:
        session_id: Session identifier to clear.
    """
    res = clear_references(session_id)
    return {
        "summary": res["message"],
        "findings": {
            "status": res["status"]
        },
        "evidence": {},
        "next_actions": ["thesis_register_references"]
    }

@mcp.tool()
def thesis_list_references(session_id: str) -> dict:
    """
    List all currently registered BibTeX keys and PDF keys for the given session.
    
    Args:
        session_id: Session identifier.
    """
    res = list_references(session_id)
    return {
        "summary": f"List of registered references: {len(res['bibtex_keys'])} BibTeX keys, {len(res['pdf_keys'])} PDF keys.",
        "findings": {
            "session_id": res["session_id"]
        },
        "evidence": res,
        "next_actions": ["thesis_audit_citations"]
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
