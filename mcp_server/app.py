"""Shared MCP server object, engine access and argument enums."""
from enum import Enum

from mcp.server.fastmcp import FastMCP

from services.model_registry import registry

mcp = FastMCP("RuScholar Studio MCP Server")


def get_engines(engine_type: str):
    """
    (engine_or_None, style_judge, citation_judge) from the shared ModelRegistry.
    Unlike the Web UI, MCP refuses to silently degrade: "local" without a model
    raises with instructions to download it.
    """
    engine_inst, style_judge, citation_judge = registry.get_judges(engine_type)
    if engine_type == "local" and engine_inst is None:
        if registry.model_exists():
            raise ValueError(
                f"Local model at '{registry.model_path}' failed to load: {registry.load_error}"
            )
        raise ValueError(
            f"Local model not found at '{registry.model_path}'. "
            f"To resolve this, you can call the MCP tool 'thesis_download_model_tool' to download it automatically, "
            f"or run the following command in your terminal to download manually: "
            f"python -c \"from naturalization_layer.model_downloader import download_model; "
            f"from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)\""
        )
    return engine_inst, style_judge, citation_judge

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
