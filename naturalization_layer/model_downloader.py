import os
import urllib.request
from rich.console import Console

console = Console()

MODEL_URL = "https://modelscope.cn/api/v1/models/Qwen/Qwen3-4B-GGUF/repo?Revision=master&FilePath=Qwen3-4B-Q5_K_M.gguf"

def download_model(dest_path: str, progress_callback=None):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    # If file exists but is suspiciously small (e.g., less than 10MB), delete and download again
    if os.path.exists(dest_path):
        if os.path.getsize(dest_path) > 10 * 1024 * 1024:
            return
        else:
            console.print("[yellow]Existing model file is corrupted or too small. Re-downloading...[/yellow]")
            os.remove(dest_path)
        
    console.print(f"[yellow]Downloading Qwen GGUF model to {dest_path}...[/yellow]")
    
    def reporthook(block_num, block_size, total_size):
        if progress_callback and total_size > 0:
            downloaded = block_num * block_size
            progress = min(1.0, downloaded / total_size)
            progress_callback(progress)
            
    urllib.request.urlretrieve(MODEL_URL, dest_path, reporthook)
    console.print("[green]Download complete![/green]")
