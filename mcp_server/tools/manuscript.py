"""Manuscript diagnostics, revision suggestions and report export tools."""

from mcp_server.app import mcp, EngineType, Discipline, ReportFormat
from mcp_server.core import (
    analyze_manuscript, suggest_revision, export_report,
)


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
