import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from naturalization_layer.rules_engine import analyze_text_rules
from naturalization_layer.ppl_engine import PPLEngine
from naturalization_layer.llm_judge import StyleJudge

MODEL_PATH = "models/Qwen3-4B-Q5_K_M.gguf"
if not os.path.exists(MODEL_PATH):
    print("Model not found.")
    sys.exit(0)

# Typical AI-generated academic Russian introduction
text = (
    "В последние годы область машинного обучения переживает бурный рост. "
    "В данном исследовании мы рассматриваем применение нейронных сетей для решения задачи классификации. "
    "Важно отметить, что предложенный подход позволяет значительно повысить эффективность. "
    "Для достижения этой цели были решены следующие задачи: анализ существующих методов, разработка архитектуры и проведение экспериментов. "
    "Полученные результаты подтверждают высокую эффективность предложенного решения."
)

print("Analyzing text...")
rules_res = analyze_text_rules(text)
engine = PPLEngine(MODEL_PATH)
judge = StyleJudge(engine.llm)

for i, s in enumerate(rules_res["sentences"]):
    diag_rules = rules_res["sentence_diagnostics"][i]
    ppl, exited = engine.evaluate_sentence_ppl(s)
    
    # Check what triggers occurred
    is_suspicious = ppl < 15.0 or len(diag_rules["cliches_found"]) > 0 or len(diag_rules["genitive_chains"]) > 0 or diag_rules["nv_ratio"] > 4.0
    
    print(f"\n--- Sentence {i+1} ---")
    print(f"Text: \"{s}\"")
    print(f"PPL: {ppl:.2f}")
    print(f"Clichés: {diag_rules['cliches_found']}")
    print(f"Genitive Chains: {diag_rules['genitive_chains']}")
    print(f"N/V Ratio: {diag_rules['nv_ratio']}")
    print(f"Passive Count: {diag_rules['passive_count']}")
    print(f"Is Suspicious (ppl<15 or rules): {is_suspicious}")
    
    if is_suspicious:
        diag = judge.diagnose_sentence(s, stats=diag_rules, ppl=ppl)
        print(f"LLM Judge issues: {diag.get('issues')}")
