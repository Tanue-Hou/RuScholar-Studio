import pytest
from unittest.mock import MagicMock
from naturalization_layer.gost_validator import rule_based_gost_check, check_gost_compliance

def test_rule_based_gost_check_compliant():
    ref = "Иванов И.И. Алгоритмы оптимизации // Вестник компьютерных технологий. 2022. Т. 5, № 2. С. 10–15."
    res = rule_based_gost_check(ref)
    assert res["score"] == 100
    assert len(res["errors_zh"]) == 0

def test_rule_based_gost_check_missing_elements():
    ref = "Иванов И.И. Алгоритмы оптимизации // Вестник компьютерных технологий."
    res = rule_based_gost_check(ref)
    assert res["score"] < 100
    # Deductions: -25 (no year), -15 (no pages), -15 (no vol/issue) -> 45
    assert res["score"] == 45
    assert any("年份" in err for err in res["errors_zh"])
    assert any("页码" in err for err in res["errors_zh"])
    assert any("卷/期" in err for err in res["errors_zh"])

@pytest.mark.anyio
async def test_check_gost_compliance_fallback():
    ref = "Иванов И.И. Алгоритмы оптимизации // Вестник компьютерных технологий."
    mock_llm = MagicMock(side_effect=Exception("LLM failure"))
    
    res = await check_gost_compliance(ref, llm=mock_llm)
    assert res["score"] == 45
    assert len(res["errors_zh"]) > 0
