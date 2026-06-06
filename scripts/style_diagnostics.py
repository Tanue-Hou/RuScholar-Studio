import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from rich.console import Console
from rich.table import Table

from naturalization_layer.rules_engine import analyze_text_rules, should_run_ppl_heuristic
from naturalization_layer.ppl_engine import PPLEngine
from naturalization_layer.llm_judge import StyleJudge

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Style Diagnostics Tool")
    parser.add_argument("--file", required=True, help="Path to the file to analyze")
    parser.add_argument("--model_path", default="models/Qwen3-4B-Q5_K_M.gguf", help="Path to the model file")
    args = parser.parse_args()

    table = Table(title="Style Diagnostics Initialization", show_header=False)
    table.add_row("Status", "[green]Initialized[/green]")
    table.add_row("Target File", args.file)
    table.add_row("Model Path", args.model_path)
    console.print(table)
    console.print("[bold blue]Style Diagnostics Initialized.[/bold blue]")

    with open(args.file, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Rules
    rules_res = analyze_text_rules(text)
    console.print(f"[bold green]Track A: Heuristics[/bold green]")
    console.print(f"Sentences: {rules_res['sentence_count']}")
    console.print(f"Cliches found: {rules_res['matched_cliches']}")
    
    if not args.model_path or not os.path.exists(args.model_path):
        console.print("[yellow]No model provided. Skipping Track B & C.[/yellow]")
        return
        
    # 2. PPL & Judge
    console.print(f"[bold green]Loading Model...[/bold green]")
    engine = PPLEngine(args.model_path)
    judge = StyleJudge(engine.llm)
    
    table = Table(title="Sentence Diagnostics")
    table.add_column("Sentence", style="cyan", max_width=30)
    table.add_column("PPL", justify="right", style="magenta")
    table.add_column("Issue Type", style="red", max_width=25)
    table.add_column("Explanation (ZH)", style="yellow", max_width=30)
    table.add_column("Suggestion", style="green", max_width=30)
    
    for i, s in enumerate(rules_res["sentences"]):
        diag_rules = rules_res["sentence_diagnostics"][i]
        
        # CLI defaults to "Smart Probe"
        run_ppl = should_run_ppl_heuristic(diag_rules, "Smart Probe")
        
        ppl = None
        was_early_exited = False
        is_suspicious = False
        issue_type = "-"
        explanation = "-"
        suggestion = "-"
        
        if run_ppl:
            # We only run early-exit if the sentence has NO Track A triggers!
            has_track_a_triggers = (
                len(diag_rules.get("cliches_found", [])) > 0 or
                len(diag_rules.get("genitive_chains", [])) > 0 or
                diag_rules.get("nv_ratio", 0.0) > 4.0 or
                diag_rules.get("passive_count", 0) > 0
            )
            
            if not has_track_a_triggers:
                ee_tokens = 6
                ee_lower = 15.0
                ee_upper = 80.0
            else:
                ee_tokens = 0
                ee_lower = 0.0
                ee_upper = float('inf')
                
            ppl, was_early_exited = engine.evaluate_sentence_ppl(s, early_exit_tokens=ee_tokens, early_exit_lower=ee_lower, early_exit_upper=ee_upper)
            
            if was_early_exited:
                issue_type = "SKIP (Early Exit)"
            else:
                is_suspicious = ppl < 15.0 or ppl > 80.0 or has_track_a_triggers
                
                if is_suspicious:
                    diag = judge.diagnose_sentence(s, stats=diag_rules, ppl=ppl)
                    if "error" in diag:
                        console.print(f"[red]LLM Judge Error: {diag['error']}[/red]")
                        console.print(f"[red]Raw LLM output: {diag['raw']}[/red]")
                        
                    issues = diag.get("issues", [])
                    if issues:
                        issue = issues[0]
                        issue_type = f"{issue.get('issue_type', '')} ({issue.get('severity', '')})"
                        explanation = issue.get('explanation_zh', '')
                        suggestion = issue.get('rewrite_suggestion', '')
                    else:
                        suggestion = diag.get("rewrite_suggestion", "-")
        else:
            issue_type = "SKIP (Heuristic)"
            
        ppl_str = f"{ppl:.2f}" if ppl is not None else "N/A"
        
        # Real-time print to console to prevent hanging perception
        console.print(f"[bold cyan]Sentence {i+1}/{len(rules_res['sentences'])}:[/bold cyan] {s[:40]}...")
        console.print(f"  PPL: {ppl_str} | Issue: {issue_type} | Suggestion: {suggestion[:30]}...")
        
        table.add_row(s[:40]+"...", ppl_str, issue_type, explanation, suggestion)
        
    console.print(table)

if __name__ == "__main__":
    main()
