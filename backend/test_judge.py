import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from naturalization_layer.ppl_engine import PPLEngine
from naturalization_layer.llm_judge import StyleJudge

engine = PPLEngine("../models/Qwen3-4B-Q5_K_M.gguf")
judge = StyleJudge(engine.llm)

sentence = "Современные алгоритмы должны обеспечивать гарантированные границы безопасности при совершении предельных манёвров."
ctx_before = ["С введением стандартов задачи вышли за рамки."]
ctx_after = ["В предельных режимах динамика связана."]
skill_rules = {
    "do_rules": ["Использовать безличные конструкции"],
    "dont_rules": ["Использовать метафоры"]
}

res = judge.diagnose_sentence(sentence, ppl=10.5, context_before=ctx_before, context_after=ctx_after, skill_rules=skill_rules)
print(json.dumps(res, indent=2, ensure_ascii=False))
