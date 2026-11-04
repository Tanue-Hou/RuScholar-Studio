"""Workflow routing and VAK specialty mapping tools."""

import asyncio
from functools import partial

from mcp_server import app
from mcp_server.app import mcp, EngineType
from services.model_registry import registry
from services.settings import settings


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
            engine_inst, _, _ = await asyncio.to_thread(app.get_engines, engine_type_str)
            if engine_inst:
                llm_inst = partial(registry.call_local, engine_inst.llm)
        except Exception:
            # Fallback to None (triggers keyword fallback inside map_vak_specialty)
            pass

    res = await map_vak_specialty(
        topic=topic,
        abstract=abstract,
        keywords=keywords,
        engine_type=engine_type_str,
        api_key=settings.resolve_api_key(api_key),
        base_url=settings.resolve_base_url(base_url),
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
