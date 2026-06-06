import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import math
from naturalization_layer.ppl_engine import PPLEngine

@patch("naturalization_layer.ppl_engine.Llama")
def test_ppl_engine_early_exit_mock(mock_llama_class):
    mock_llm = MagicMock()
    mock_llama_class.return_value = mock_llm
    
    # 1. Mock tokenization into 10 tokens
    mock_llm.tokenize.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    # 2. Mock scores so PPL is high (e.g., uniform logits)
    # Logits all equal to 0.0 means PPL will equal vocab size (100 in this case)
    logits = np.zeros(100)
    mock_scores = MagicMock()
    mock_scores.__getitem__.return_value = logits
    mock_llm._scores = mock_scores
    
    engine = PPLEngine("dummy_path")
    
    # Run evaluation with early exit
    ppl, exited = engine.evaluate_sentence_ppl(
        "Это предложение для проверки.", 
        early_exit_tokens=6, 
        early_exit_lower=15.0,
        early_exit_upper=150.0
    )
    
    # Check that it early exited
    assert exited is True
    assert ppl > 30.0
    
    # Verify that eval was called with the first 7 tokens only (BOS + 6 tokens)
    mock_llm.eval.assert_called_once_with([1, 2, 3, 4, 5, 6, 7])

@patch("naturalization_layer.ppl_engine.Llama")
def test_ppl_engine_no_early_exit_mock(mock_llama_class):
    mock_llm = MagicMock()
    mock_llama_class.return_value = mock_llm
    
    # Mock tokenization into 10 tokens
    mock_llm.tokenize.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    # Mock scores so PPL is extremely low (e.g., highly predicted tokens)
    # We want logits where target token has a very high value
    logits = np.zeros(100)
    # To mock: logits[target_token] is high, e.g. 10.0, rest are 0.0
    # Let's just mock exponential sum and max logit behavior:
    # If exp_sum is small, nll is small, so ppl is low (e.g. 1.05)
    mock_scores = MagicMock()
    # We can customize __getitem__ to return logits that make exp_sum sum up to a high value at target_token
    # For simplicity, let's make target token have logit 100, others 0.
    # exp(100) / exp(100) = 1.0 log prob = 0.0, ppl = exp(0) = 1.0.
    def get_logits(key):
        i = key[0] if isinstance(key, tuple) else key
        res = np.zeros(100)
        # the target token is i + 1, so tokens[i+1]
        target = i + 2 # token index
        if target < 100:
            res[target] = 100.0
        return res
        
    mock_scores.__getitem__.side_effect = get_logits
    mock_llm._scores = mock_scores
    
    engine = PPLEngine("dummy_path")
    
    # Run evaluation with early exit bounds set
    # Since PPL will be near 1.0, it should NOT early exit because PPL < 15.0.
    ppl, exited = engine.evaluate_sentence_ppl(
        "Это предложение для проверки.", 
        early_exit_tokens=6, 
        early_exit_lower=15.0,
        early_exit_upper=80.0
    )
    
    # Check that it did NOT early exit
    assert exited is False
    assert ppl < 5.0
    
    # Verify that eval was called twice: once for prefix, then again for the full sequence after failing prefix check
    assert mock_llm.eval.call_count == 2
