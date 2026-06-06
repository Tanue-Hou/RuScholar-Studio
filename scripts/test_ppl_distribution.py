import sys
import os
import docx2txt
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from naturalization_layer.ppl_engine import PPLEngine
from naturalization_layer.rules_engine import analyze_text_rules

def main():
    docx_path = "/Users/tanue/Library/Group Containers/UBF8T346G9.OneDriveSyncClientSuite/OneDrive.noindex/OneDrive/1科研工作/投稿/基于路面附着系数评估的未知情况下车辆状态评估/5.15学术会议/ОЦЕНКА КОЭФФИЦИЕНТА СЦЕПЛЕНИЯ ДОРОЖНОГО ПОКРЫТИЯ НА ОСНОВЕ АДАПТИВНОГО РАСШИРЕННОГО НАБЛЮДАТЕЛЯ С ИСПОЛЬЗОВАНИЕМ РЕКУРЕНТНОЙ НЕЙРОННОЙ СЕТИ.docx"
    model_path = "models/Qwen3-4B-Q5_K_M.gguf"
    
    print(f"Reading document: {docx_path}")
    try:
        text = docx2txt.process(docx_path)
    except Exception as e:
        print(f"Error reading docx: {e}")
        return

    print("Analyzing text structure...")
    rules_res = analyze_text_rules(text)
    sentences = rules_res["sentences"]
    diagnostics = rules_res["sentence_diagnostics"]
    
    print(f"Found {len(sentences)} sentences. Loading model...")
    engine = PPLEngine(model_path)
    
    print("Evaluating PPL for each sentence. This may take a moment...")
    results = []
    
    # Let's take the first 50 sentences to get a solid sample without waiting forever
    sample_size = min(len(sentences), 50)
    
    for i in range(sample_size):
        sent = sentences[i].strip()
        if len(sent.split()) < 5:
            continue
            
        ppl, _ = engine.evaluate_sentence_ppl(sent, early_exit_tokens=0, early_exit_threshold=0.0)
        
        diag = diagnostics[i]
        cliches = diag.get("cliches_found", [])
        nv_ratio = diag.get("nv_ratio", 0.0)
        
        print(f"--- Sentence {i+1} ---")
        print(f"PPL: {ppl:.2f} | Words: {len(sent.split())} | Cliches: {len(cliches)}")
        print(f"Text: {sent[:100]}...")
        
        results.append({
            "index": i+1,
            "ppl": round(ppl, 2),
            "words": len(sent.split()),
            "cliches": cliches,
            "nv_ratio": nv_ratio,
            "text": sent
        })
        
    # Print sorted by PPL
    print("\n\n--- RESULTS SORTED BY PPL ---")
    results.sort(key=lambda x: x["ppl"])
    for r in results:
        cliche_str = " | CLICHE" if r["cliches"] else ""
        print(f"[{r['ppl']:>6.2f}] {r['text'][:80]}...{cliche_str}")

if __name__ == '__main__':
    main()
