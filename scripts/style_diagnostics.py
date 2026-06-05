import argparse
from rich.console import Console

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Russian Style Diagnostics & Naturalization Engine")
    parser.add_argument("--input", required=True, help="Path to input markdown or text file")
    parser.add_argument("--model", required=False, help="Path to Qwen 3 GGUF model")
    args = parser.parse_args()

    console.print(f"[bold blue]Initializing Diagnostics for:[/bold blue] {args.input}")

if __name__ == "__main__":
    main()
