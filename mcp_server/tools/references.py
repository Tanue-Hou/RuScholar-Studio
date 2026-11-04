"""Reference registration tools."""

from mcp_server.app import mcp
from mcp_server.core import (
    register_references, clear_references, list_references,
)


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
