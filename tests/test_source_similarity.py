import pytest
from naturalization_layer.source_similarity import calculate_ngram_similarity, check_source_similarity

def test_ngram_similarity():
    text1 = "Интеллектуальное управление мобильными роботами осуществляют"
    text2 = "Интеллектуальное управление мобильными роботами осуществляется"
    sim = calculate_ngram_similarity(text1, text2)
    assert sim > 0.6

def test_check_source_similarity():
    # 1. No citation when text is highly similar -> citation gap
    sent_no_cit = "Оценка коэффициента сцепления дорожного покрытия основана на использовании нейронной сети для классификации состояний дороги."
    res = check_source_similarity(sent_no_cit, has_citation=False)
    assert res is not None
    assert res["issue_type"] == "citation_gap"
    assert res["severity"] == "high"

    # 2. Citation is present when text is similar -> semantic paraphrase warning
    res_with_cit = check_source_similarity(sent_no_cit, has_citation=True)
    assert res_with_cit is not None
    assert res_with_cit["issue_type"] == "semantic_plagiarism_risk"
    assert res_with_cit["severity"] == "medium"
    
    # 3. Text not matching anything in database -> None
    res_none = check_source_similarity("Это совершенно уникальное предложение, которого нет в базе данных.", has_citation=False)
    assert res_none is None
