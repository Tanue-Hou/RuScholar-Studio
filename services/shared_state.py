import asyncio
import os

from services.settings import settings
from services.session_store import ExpiringDict

# Uploaded references per session: {"bibtex", "corpus", "retrievers", "online_cache", "bib_mapping"}.
# Create entries via services.reference_service.ensure_reference_session().
session_references = ExpiringDict(settings.session_ttl_seconds)

# Analyses registered via POST /api/session and consumed by GET /api/diagnose.
pending_analyses = ExpiringDict(settings.session_ttl_seconds)

# Lock for Llama model local inference
model_lock = asyncio.Lock()

# 模型路径解析统一由 services.config 负责（RS-0002）
from services.config import resolve_model_path

MODEL_PATH = resolve_model_path()
