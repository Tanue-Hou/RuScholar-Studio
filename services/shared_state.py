import asyncio
import os

# Global session references cache
session_references = {}

# Lock for Llama model local inference
model_lock = asyncio.Lock()

# Smart Model Path resolver: supports root relative detection and fallback
def resolve_model_path() -> str:
    env_path = os.getenv("RUSCHOLAR_MODEL_PATH")
    if env_path:
        return os.path.abspath(os.path.expanduser(env_path))

    # 1. Base absolute path dynamically calculated from file location (project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_model_name = "Qwen3-8B-Q5_K_M.gguf"
    fallback_model_name = "Qwen3-4B-Q5_K_M.gguf"

    abs_path_8b = os.path.join(project_root, "models", target_model_name)
    abs_path_4b = os.path.join(project_root, "models", fallback_model_name)
    
    # Check 8B model existence sequentially
    if os.path.exists(os.path.join("models", target_model_name)):
        return os.path.abspath(os.path.join("models", target_model_name))
    elif os.path.exists(abs_path_8b):
        return abs_path_8b
    elif os.path.exists(os.path.join("..", "models", target_model_name)):
        return os.path.abspath(os.path.join("..", "models", target_model_name))
        
    # Check 4B fallback if 8B is not present
    if os.path.exists(os.path.join("models", fallback_model_name)):
        return os.path.abspath(os.path.join("models", fallback_model_name))
    elif os.path.exists(abs_path_4b):
        return abs_path_4b
    elif os.path.exists(os.path.join("..", "models", fallback_model_name)):
        return os.path.abspath(os.path.join("..", "models", fallback_model_name))
        
    # Default target path (where downloader will store the model)
    return abs_path_8b

MODEL_PATH = resolve_model_path()
