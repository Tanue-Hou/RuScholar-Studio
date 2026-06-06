import pytest
from unittest.mock import MagicMock, patch
from naturalization_layer.llm_judge import StyleJudge

def test_detect_discipline_engine_mapping_cloud_pro():
    mock_llm = MagicMock()
    judge = StyleJudge(mock_llm)
    
    # Mock the _call_deepseek_api method to verify it is called with mapped engine
    with patch.object(judge, '_call_deepseek_api') as mock_api:
        mock_api.return_value = '{"discipline": "AUTOMATION_CONTROL"}'
        
        res = judge.detect_discipline("text", engine_type="hybrid-pro", api_key="test_key", base_url="test_url")
        
        assert res == "AUTOMATION_CONTROL"
        mock_api.assert_called_once()
        # Verify it mapped "hybrid-pro" to "deepseek-v4-pro"
        args, kwargs = mock_api.call_args
        assert args[0] == "deepseek-v4-pro"

def test_detect_discipline_engine_mapping_cloud_flash():
    mock_llm = MagicMock()
    judge = StyleJudge(mock_llm)
    
    with patch.object(judge, '_call_deepseek_api') as mock_api:
        mock_api.return_value = '{"discipline": "SCI_TECH"}'
        
        res = judge.detect_discipline("text", engine_type="cloud-flash", api_key="test_key", base_url="test_url")
        
        assert res == "SCI_TECH"
        mock_api.assert_called_once()
        args, kwargs = mock_api.call_args
        assert args[0] == "deepseek-v4-flash"

def test_detect_discipline_local_prompt_and_tokens():
    mock_llm = MagicMock()
    mock_llm.return_value = {
        "choices": [
            {
                "text": '{"discipline": "AGRI_MED"}'
            }
        ]
    }
    judge = StyleJudge(mock_llm)
    
    res = judge.detect_discipline("Клеточная биология и ДНК.", engine_type="local")
    
    assert res == "AGRI_MED"
    mock_llm.assert_called_once()
    
    # Verify the local model call arguments
    args, kwargs = mock_llm.call_args
    prompt = args[0]
    
    # Verify max_tokens is 1024
    assert kwargs.get("max_tokens") == 1024
    
    # Verify Chinese think instruction is in prompt
    assert "You MUST write your reasoning inside <think>...</think> tags strictly in Chinese" in prompt
