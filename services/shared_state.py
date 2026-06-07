import asyncio
import os

# Global session references cache
session_references = {}

# Lock for Llama model local inference
model_lock = asyncio.Lock()

# Model Path configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "Qwen3-4B-Q5_K_M.gguf")
