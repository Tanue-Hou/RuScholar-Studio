import os
import pytest
from unittest.mock import MagicMock
from naturalization_layer.llm_judge import StyleJudge
from llama_cpp import Llama

MODEL_PATH = "models/Qwen3-4B-Q5_K_M.gguf"

def test_style_judge_mock():
    mock_llm = MagicMock()
    mock_llm.return_value = {
        "choices": [
            {
                "text": '{"issues": [{"issue_type": "ai_generated_suspicion", "severity": "high", "evidence": "test", "explanation_zh": "test", "explanation_ru": "test", "rewrite_suggestion": "test"}], "safe_to_rewrite": true}'
            }
        ]
    }
    
    judge = StyleJudge(mock_llm)
    res = judge.diagnose_sentence("Это тестовое предложение.")
    assert "issues" in res
    assert res["safe_to_rewrite"] is True
    assert res["issues"][0]["issue_type"] == "ai_generated_suspicion"

@pytest.mark.skipif(not os.path.exists(MODEL_PATH), reason="Real model not found")
def test_style_judge_real():
    llm = Llama(model_path=MODEL_PATH, n_gpu_layers=-1, n_ctx=2048, verbose=False)
    judge = StyleJudge(llm)
    
    sentence = "Важно отметить, что оценка параметров играет ключевую роль."
    stats = {
        "nv_ratio": 5.0,
        "passive_count": 0,
        "genitive_chains": ["оценка параметров"],
        "cliches_found": ["важно отметить, что", "играет ключевую роль"],
        "connectors_found": []
    }
    res = judge.diagnose_sentence(sentence, stats=stats, ppl=5.2)
    assert "issues" in res
    assert "safe_to_rewrite" in res
    assert isinstance(res["issues"], list)

def test_repair_json_string():
    from naturalization_layer.llm_judge import repair_json_string
    
    # 1. Truncated value inside string
    truncated = '{"issues": [{"issue_type": "ai_cliche", "rewrite_suggestion": "Это пример'
    repaired = repair_json_string(truncated)
    assert repaired == '{"issues": [{"issue_type": "ai_cliche", "rewrite_suggestion": "Это пример"}]}'
    
    # 2. Literal newline inside string
    newline_in_str = '{"issues": [{"explanation": "Первое предложение.\nВторое предложение."}]}'
    repaired = repair_json_string(newline_in_str)
    # Check that it escaped the literal newline to \n
    # Note that in python string representation, \n is a single char, and double backslash n is two chars.
    # The source string newline_in_str has a literal newline. The output should have escaped backslash + n.
    assert "\\n" in repaired
    
    # 3. Trailing comma
    trailing_comma = '{"safe_to_rewrite": true,}'
    repaired = repair_json_string(trailing_comma)
    assert repaired == '{"safe_to_rewrite": true}'
    
    # 4. Empty string
    assert repair_json_string("") == "{}"

