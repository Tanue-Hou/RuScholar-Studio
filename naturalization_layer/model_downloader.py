import os
import urllib.request
from rich.console import Console

console = Console()

MODEL_URL = "https://modelscope.cn/api/v1/models/qwen/Qwen2.5-3B-Instruct-GGUF/repo/files?path=qwen2.5-3b-instruct-q5_k_m.gguf"

def download_model(dest_path: str):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    if os.path.exists(dest_path):
        return
        
    console.print(f"[yellow]Downloading Qwen GGUF model to {dest_path}...[/yellow]")
    urllib.request.urlretrieve(MODEL_URL, dest_path)
    console.print("[green]Download complete![/green]")
