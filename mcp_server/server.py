"""
RuScholar Studio MCP server (stdio) entry point.

Layout:
  mcp_server/app.py    — FastMCP instance, get_engines(), argument enums
  mcp_server/core.py   — plain functions behind the tools (importable directly)
  mcp_server/tools/*   — the 17 @mcp.tool() definitions, grouped by area

This module registers all tools and re-exports the public names, so
`python -m mcp_server.server` and `from mcp_server.server import X` keep working.
To patch engine loading in tests, patch `mcp_server.app.get_engines`.
"""
from mcp_server.app import Discipline, EngineType, ReportFormat, get_engines, mcp  # noqa: F401
from mcp_server.core import (  # noqa: F401
    analyze_manuscript, audit_citations, check_model_installed, clear_references,
    download_model_tool, export_report, list_references, register_references,
    retrieve_evidence, suggest_revision,
)
from mcp_server.tools.workflow import thesis_map_vak_specialty, thesis_route_workflow  # noqa: F401
from mcp_server.tools.manuscript import (  # noqa: F401
    thesis_analyze_manuscript, thesis_export_report, thesis_suggest_revision,
)
from mcp_server.tools.citations import (  # noqa: F401
    thesis_audit_citations, thesis_audit_vak_gost_compliance, thesis_bind_evidence,
    thesis_classify_evidence_need, thesis_extract_claims, thesis_judge_claim_evidence_nli,
    thesis_retrieve_evidence,
)
from mcp_server.tools.model import thesis_check_model_installed, thesis_download_model_tool  # noqa: F401
from mcp_server.tools.references import (  # noqa: F401
    thesis_clear_references, thesis_list_references, thesis_register_references,
)
from services.model_registry import registry  # noqa: F401
from services.shared_state import MODEL_PATH, session_references  # noqa: F401


def run() -> None:
    """Console entry point: `ruscholar-mcp` (or `python -m mcp_server.server`)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
