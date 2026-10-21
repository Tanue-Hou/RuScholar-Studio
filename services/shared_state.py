import asyncio
import os

# Global session references cache
session_references = {}

# Lock for Llama model local inference
model_lock = asyncio.Lock()

# 模型路径解析统一由 services.config 负责（RS-0002）
from services.config import resolve_model_path

MODEL_PATH = resolve_model_path()
