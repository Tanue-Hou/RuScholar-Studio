from naturalization_layer.rules_engine import analyze_text_rules

def test_analyze_text_rules():
    text = "Это тестовое предложение. Важно отметить, что оно короткое."
    result = analyze_text_rules(text)
    assert result["sentence_count"] == 2
    assert result["cliche_matches"] == 1
    assert "важно отметить, что" in result["matched_cliches"]

def test_analyze_text_rules_advanced():
    text = (
        "Это тестовое предложение [1] с формулой $x = y + 1$. "
        "Оценка коэффициента сцепления дорожного покрытия основана на использовании нейронной сети. "
        "В данной работе создается новая модель, которая используется для оценки. "
        "Важно отметить, что метод является эффективным."
    )
    result = analyze_text_rules(text)
    
    # 1. Protection check
    assert result["sentence_count"] == 4
    # The formulas/citations must be restored in the final sentences list
    assert "[1]" in result["sentences"][0]
    assert "$x = y + 1$" in result["sentences"][0]
    
    # 2. Genitive chain check
    diag1 = result["sentence_diagnostics"][1]
    assert len(diag1["genitive_chains"]) > 0
    
    # 3. Passive voice check
    diag2 = result["sentence_diagnostics"][2]
    assert diag2["passive_count"] == 2
    
    # 4. N/V Ratio check
    assert diag1["nv_ratio"] > 4.0
    
    # 5. Cliches check
    diag3 = result["sentence_diagnostics"][3]
    assert "важно отметить, что" in diag3["cliches_found"]

def test_should_run_ppl_heuristic():
    from naturalization_layer.rules_engine import should_run_ppl_heuristic
    
    # 1. Protected sentence
    assert should_run_ppl_heuristic({"is_protected": True, "original_text": "Formula"}, "Deep Scan") is False
    
    # 2. Very short sentence (< min_words)
    diag = {"is_protected": False, "original_text": "Это короткое предложение.", "cliches_found": []}
    assert should_run_ppl_heuristic(diag, "Deep Scan", min_words=6) is False
    
    # 3. Deep Scan (length >= min_words)
    diag_long = {"is_protected": False, "original_text": "Это предложение длиной ровно шесть слов теперь.", "cliches_found": []}
    assert should_run_ppl_heuristic(diag_long, "Deep Scan", min_words=6) is True
    
    # 4. Smart Probe
    # Below smart_words, no clichés -> False
    diag_smart_no = {"is_protected": False, "original_text": "Это короткое предложение из пяти слов.", "cliches_found": []}
    assert should_run_ppl_heuristic(diag_smart_no, "Smart Probe", min_words=3, smart_words=10) is False
    # Below smart_words, with clichés -> True
    diag_smart_yes_cliche = {"is_protected": False, "original_text": "Это короткое предложение из пяти слов.", "cliches_found": ["важно отметить"]}
    assert should_run_ppl_heuristic(diag_smart_yes_cliche, "Smart Probe", min_words=3, smart_words=10) is True
    # Above smart_words -> True
    diag_smart_yes_len = {"is_protected": False, "original_text": "Это предложение длиной ровно одиннадцать слов в данном контексте и оно длинное.", "cliches_found": []}
    assert should_run_ppl_heuristic(diag_smart_yes_len, "Smart Probe", min_words=3, smart_words=10) is True

def test_analyze_text_rules_bibliography():
    text = (
        "Это основное предложение научной статьи. "
        "Второй абзац текста. "
        "References\n"
        "[1] Smith J. AI research paper. 2025.\n"
        "[2] Ivanov I. Russian NLP model. 2026."
    )
    result = analyze_text_rules(text)
    assert result["sentence_diagnostics"][0]["is_bibliography"] is False
    assert result["sentence_diagnostics"][1]["is_bibliography"] is False
    
    smith_found = False
    ivanov_found = False
    for diag in result["sentence_diagnostics"]:
        txt = diag["original_text"]
        if "Smith" in txt:
            assert diag["is_bibliography"] is True
            smith_found = True
        if "Ivanov" in txt:
            assert diag["is_bibliography"] is True
            ivanov_found = True
            
    assert smith_found is True
    assert ivanov_found is True
