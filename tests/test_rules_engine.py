from naturalization_layer.rules_engine import analyze_text_rules

def test_analyze_text_rules():
    text = "Это тестовое предложение. Важно отметить, что оно короткое."
    result = analyze_text_rules(text)
    assert result["sentence_count"] == 2
    assert result["cliche_matches"] == 1
    assert "важно отметить, что" in result["matched_cliches"]
