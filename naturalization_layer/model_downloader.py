import os
import urllib.request
from rich.console import Console

console = Console()

MODEL_URL = "https://modelscope.cn/models/Qwen/Qwen3-4B-GGUF/resolve/master/Qwen3-4B-Q5_K_M.gguf"

EXPECTED_SIZE = 2889513184

def download_model(dest_path: str, progress_callback=None):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    # If final file exists and is complete, return
    if os.path.exists(dest_path):
        if os.path.getsize(dest_path) == EXPECTED_SIZE:
            return
        else:
            console.print("[yellow]Existing model file size is incorrect. Deleting...[/yellow]")
            os.remove(dest_path)
            
    tmp_path = dest_path + ".tmp"
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
        
    console.print(f"[yellow]Downloading Qwen GGUF model to {dest_path}...[/yellow]")
    
    def reporthook(block_num, block_size, total_size):
        if progress_callback and total_size > 0:
            downloaded = block_num * block_size
            progress = min(1.0, downloaded / total_size)
            progress_callback(progress)
            
    try:
        urllib.request.urlretrieve(MODEL_URL, tmp_path, reporthook)
        os.rename(tmp_path, dest_path)
        console.print("[green]Download complete![/green]")
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e
