import pytest
from naturalization_layer.translationese_risk import run_translationese_checks

def test_translationese_noun_stacking():
    # nv_ratio > 4.5
    stats = {"nv_ratio": 5.2, "word_count": 10, "verbs_count": 1}
    warnings = run_translationese_checks("Тестовое предложение с существительными.", stats)
    assert len(warnings) == 1
    assert warnings[0]["issue_type"] == "translationese_noun_stacking"

def test_translationese_verb_deficiency():
    # word_count > 8, verbs_count == 0
    stats = {"nv_ratio": 2.0, "word_count": 12, "verbs_count": 0}
    warnings = run_translationese_checks("Это очень длинное предложение без каких-либо глаголов и действий.", stats)
    assert len(warnings) == 1
    assert warnings[0]["issue_type"] == "translationese_verb_deficiency"

def test_style_formula_unexplained():
    # contains protected math but no explanation keywords
    stats = {"nv_ratio": 1.5, "word_count": 10, "verbs_count": 2}
    warnings = run_translationese_checks("Рассмотрим формулу __PROTECTED_LATEX_0__ в нашей текущей работе.", stats)
    assert len(warnings) == 1
    assert warnings[0]["issue_type"] == "style_formula_unexplained"
    
    # with explanation keywords -> no warnings
    warnings_ok = run_translationese_checks("Рассмотрим __PROTECTED_LATEX_0__, где X обозначает вектор параметров.", stats)
    assert len(warnings_ok) == 0
