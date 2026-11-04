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
    mock_llm._scores = np.zeros((10, 100))
    
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
    # Row i predicts token i+1 (= value i+2): give that target a logit of 100,
    # so every target has log-prob ~0 and PPL ~1.0.
    scores = np.zeros((10, 100))
    for i in range(9):
        scores[i, i + 2] = 100.0
    mock_llm._scores = scores
    
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


def test_sequence_nll_matches_reference_loop():
    from naturalization_layer.ppl_engine import sequence_nll
    rng = np.random.default_rng(0)
    scores = rng.normal(size=(6, 50))
    tokens = [0, 3, 7, 11, 2, 49]
    expected = 0.0
    for i in range(5):
        row = scores[i]
        m = max(row)
        log_z = m + math.log(sum(math.exp(x - m) for x in row))
        expected += log_z - row[tokens[i + 1]]
    assert sequence_nll(scores, tokens, 6) == pytest.approx(expected)
