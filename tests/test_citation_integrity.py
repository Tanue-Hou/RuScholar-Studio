import pytest
from naturalization_layer.citation_integrity import (
    parse_citations_in_text,
    parse_bibliography_numbers,
    check_citation_integrity
)

def test_parse_citations_in_text():
    text = "Некоторые данные [1], а также алгоритмы [2, 3] и даже целые диапазоны [5-7] используются в работе."
    citations = parse_citations_in_text(text)
    assert citations == {1, 2, 3, 5, 6, 7}

def test_parse_bibliography():
    text = """
    Введение в мобильную робототехнику.
    Список литературы:
    1. Иванов И.И. Теория систем.
    [2] Петров П.П. Автоматизация.
    3. Сидоров С.С. Физика.
    """
    entries = parse_bibliography_numbers(text)
    assert entries == {1, 2, 3}

def test_check_citation_integrity():
    # 1. Complete reference list
    text_ok = """
    Методы сцепления дорожного покрытия [1] и управление [2] описаны.
    References:
    1. Иванов И.И.
    2. Петров П.П.
    """
    res = check_citation_integrity(text_ok)
    assert res["has_bibliography"] is True
    assert len(res["warnings"]) == 0
    
    # 2. Missing reference (citation gap / hallucination) and unused reference
    text_anomaly = """
    Оценка сцепления [1] и регуляторы [3] в работе.
    Список литературы:
    1. Иванов И.И.
    [2] Петров П.П.
    """
    res_anomaly = check_citation_integrity(text_anomaly)
    assert res_anomaly["has_bibliography"] is True
    
    # [3] is cited in text but missing in bibliography
    missing_warning = [w for w in res_anomaly["warnings"] if w["issue_type"] == "citation_missing_bibliography"]
    assert len(missing_warning) == 1
    assert missing_warning[0]["evidence"] == "[3]"
    
    # [2] is in bibliography but unused in text
    unused_warning = [w for w in res_anomaly["warnings"] if w["issue_type"] == "citation_unused_bibliography"]
    assert len(unused_warning) == 1
    assert unused_warning[0]["evidence"] == "[2]"
