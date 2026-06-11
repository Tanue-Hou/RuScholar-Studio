import pytest
from unittest.mock import MagicMock
from naturalization_layer.vak_specialty_mapper import load_vak_nomenclature, keyword_map_vak_specialty, map_vak_specialty

def test_load_vak_nomenclature():
    nomenclature = load_vak_nomenclature()
    assert len(nomenclature) > 0
    assert any(spec["code"] == "2.3.1" for spec in nomenclature)
    assert any(spec["code"] == "1.2.2" for spec in nomenclature)

def test_keyword_map_vak_specialty_systems():
    # Keywords matching 2.3.1
    topic = "Системный анализ и управление процессом обработки информации в распределенных вычислительных системах"
    abstract = "В работе исследуются алгоритмы принятия решений и методы системного анализа."
    keywords = "системный анализ, управление, принятие решений"
    
    result = keyword_map_vak_specialty(topic, abstract, keywords)
    assert result["code"] == "2.3.1"
    assert result["confidence"] > 0.0
    assert "системный анализ" in result["reasoning_zh"] or "2.3.1" in result["reasoning_zh"]

def test_keyword_map_vak_specialty_modeling():
    # Keywords matching 1.2.2
    topic = "Математическое моделирование и численные методы расчета прочностных характеристик"
    abstract = "Разработан комплекс программ для численного эксперимента и построения математических моделей."
    keywords = "математическое моделирование, численные методы, комплекс программ"
    
    result = keyword_map_vak_specialty(topic, abstract, keywords)
    assert result["code"] == "1.2.2"
    assert result["confidence"] > 0.0

@pytest.mark.anyio
async def test_map_vak_specialty_llm_fallback():
    # Test that when LLM fails, it fallback gracefully to keyword mapping
    mock_llm = MagicMock(side_effect=Exception("LLM execution error"))
    
    topic = "Математическое моделирование"
    result = await map_vak_specialty(topic, llm=mock_llm)
    assert result["code"] == "1.2.2"
    assert "эвристическая" in result["reasoning_ru"] or "систем" in result["reasoning_zh"]
