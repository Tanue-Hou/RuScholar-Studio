"""Citation, claim and evidence audit tools (incl. VAK/GOST compliance)."""
import asyncio

from services.model_registry import registry
from mcp_server import app
from mcp_server.app import mcp, EngineType
from mcp_server.core import (
    audit_citations, retrieve_evidence,
)


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
    _, _, cit_judge = await asyncio.to_thread(app.get_engines, engine_type_str)

    if engine_type_str == "local":
        # Local llama.cpp context is shared; serialise like every other local call.
        nli_res = await registry.run_local(
            cit_judge.verify_citation,
            claim, snippets, engine_type_str, api_key, base_url
        )
    else:
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
            engine_inst, _, _ = app.get_engines(engine_type_str)
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
