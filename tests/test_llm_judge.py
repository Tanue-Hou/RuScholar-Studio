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
