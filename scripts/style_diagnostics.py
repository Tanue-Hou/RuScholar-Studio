import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from rich.console import Console
from rich.table import Table

from naturalization_layer.rules_engine import analyze_text_rules
from naturalization_layer.ppl_engine import PPLEngine
from naturalization_layer.llm_judge import StyleJudge

console = Console()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", required=False)
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Rules
    rules_res = analyze_text_rules(text)
    console.print(f"[bold green]Track A: Heuristics[/bold green]")
    console.print(f"Sentences: {rules_res['sentence_count']}")
    console.print(f"Cliches found: {rules_res['matched_cliches']}")
    
    if not args.model or not os.path.exists(args.model):
        console.print("[yellow]No model provided. Skipping Track B & C.[/yellow]")
        return
        
    # 2. PPL & Judge
    console.print(f"[bold green]Loading Model...[/bold green]")
    engine = PPLEngine(args.model)
    judge = StyleJudge(engine.llm)
    
    table = Table(title="Sentence Diagnostics")
    table.add_column("Sentence", style="cyan", max_width=40)
    table.add_column("PPL", justify="right", style="magenta")
    table.add_column("Suggestion", style="green", max_width=40)
    
    for s in rules_res["sentences"]:
        ppl = engine.evaluate_sentence_ppl(s)
        # Mock trigger: evaluate if PPL is suspiciously low or it contains cliches
        if ppl < 10.0 or rules_res['cliche_matches'] > 0:
            diag = judge.diagnose_sentence(s)
            suggestion = diag.get("rewrite_suggestion", "")
        else:
            suggestion = "-"
        table.add_row(s[:50]+"...", f"{ppl:.2f}", str(suggestion))
        
    console.print(table)

if __name__ == "__main__":
    main()
