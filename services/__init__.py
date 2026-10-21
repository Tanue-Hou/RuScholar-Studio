"""Shared service layer used by the Web UI and MCP tools."""
from services.config import load_env_file as _load_env_file

_load_env_file()
