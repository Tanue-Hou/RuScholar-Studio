import pytest
from unittest.mock import MagicMock
from naturalization_layer.llm_judge import StyleJudge

def test_detect_discipline_mock_local():
    mock_llm = MagicMock()
    mock_llm.return_value = {
        "choices": [
            {
                "text": '{"discipline": "AUTOMATION_CONTROL"}'
            }
        ]
    }
    
    judge = StyleJudge(mock_llm)
    # 1. Successful JSON parsing
    res = judge.detect_discipline("Это текст про регуляторы и управление роботами.", engine_type="local")
    assert res == "AUTOMATION_CONTROL"
    
    # 2. JSON parsing failure should fall back to keyword matching
    mock_llm.return_value = {
        "choices": [
            {
                "text": 'garbage text'
            }
        ]
    }
    res_fallback = judge.detect_discipline("Это текст про управление роботами.", engine_type="local")
    assert res_fallback == "AUTOMATION_CONTROL"

    res_fallback_agri = judge.detect_discipline("Клеточная терапия биологических систем.", engine_type="local")
    assert res_fallback_agri == "AGRI_MED"

    res_fallback_sci = judge.detect_discipline("Физические свойства сплавов при высоких температурах.", engine_type="local")
    assert res_fallback_sci == "SCI_TECH"

    res_fallback_hum = judge.detect_discipline("Политический курс и экономическое развитие общества.", engine_type="local")
    assert res_fallback_hum == "HUM_POL_ECON"

    res_fallback_universal = judge.detect_discipline("Что-то неопределенное.", engine_type="local")
    assert res_fallback_universal == "UNIVERSAL"
