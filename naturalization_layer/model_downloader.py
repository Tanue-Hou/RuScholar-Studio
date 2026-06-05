import os
import urllib.request
from rich.console import Console

console = Console()

MODEL_URL = "https://modelscope.cn/api/v1/models/qwen/Qwen2.5-3B-Instruct-GGUF/repo?Revision=master&FilePath=qwen2.5-3b-instruct-q5_k_m.gguf"

def download_model(dest_path: str):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    # If file exists but is suspiciously small (e.g., less than 10MB), delete and download again
    if os.path.exists(dest_path):
        if os.path.getsize(dest_path) > 10 * 1024 * 1024:
            return
        else:
            console.print("[yellow]Existing model file is corrupted or too small. Re-downloading...[/yellow]")
            os.remove(dest_path)
        
    console.print(f"[yellow]Downloading Qwen GGUF model to {dest_path}...[/yellow]")
    urllib.request.urlretrieve(MODEL_URL, dest_path)
    console.print("[green]Download complete![/green]")
