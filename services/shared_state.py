import asyncio
import os

# Global session references cache
session_references = {}

# Lock for Llama model local inference
model_lock = asyncio.Lock()

# Model Path configuration
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "Qwen3-4B-Q5_K_M.gguf")
