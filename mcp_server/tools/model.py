"""Local model status and download tools."""

from mcp_server.app import mcp
from mcp_server.core import (
    check_model_installed, download_model_tool,
)


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
