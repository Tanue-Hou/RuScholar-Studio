import asyncio
import os

# Global session references cache
session_references = {}

# Lock for Llama model local inference
model_lock = asyncio.Lock()

# Smart Model Path resolver: supports root relative detection and fallback
def resolve_model_path() -> str:
    env_path = os.getenv("THESIS_BUTLER_MODEL_PATH")
    if env_path:
        return os.path.abspath(os.path.expanduser(env_path))

    # 1. Base absolute path dynamically calculated from file location (project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    abs_path = os.path.join(project_root, "models", "Qwen3-4B-Q5_K_M.gguf")
    
    # 2. Pure relative path (if run from project root)
    rel_path_cwd = os.path.join("models", "Qwen3-4B-Q5_K_M.gguf")
    
    # 3. Parent relative path (if run from backend/ or mcp_server/ directory)
    rel_path_parent = os.path.join("..", "models", "Qwen3-4B-Q5_K_M.gguf")
    
    # Check existence sequentially
    if os.path.exists(rel_path_cwd):
        return os.path.abspath(rel_path_cwd)
    elif os.path.exists(abs_path):
        return abs_path
    elif os.path.exists(rel_path_parent):
        return os.path.abspath(rel_path_parent)
        
    # Default fallback path (where downloader will store the model)
    return abs_path

MODEL_PATH = resolve_model_path()
