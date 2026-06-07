import pytest
from naturalization_layer.rag_retriever import parse_bibtex, chunk_text, BM25Retriever
from naturalization_layer.nli_judge import NLICitationJudge

def test_parse_bibtex():
    bib_str = """
    @article{smith2020robot,
      author = {Smith, John and Jones, Mary},
      title = {Advanced Robot Navigation Systems},
      journal = {Journal of Robotics},
      year = {2020},
      volume = {12},
      pages = {100-110}
    }
    @inproceedings{ivanov2022control,
      author = {Иванов, И. И.},
      title = {Теория автоматического управления},
      booktitle = {Труды конференции по автоматизации},
      year = {2022}
    }
    """
    entries = parse_bibtex(bib_str)
    assert "smith2020robot" in entries
    assert entries["smith2020robot"]["title"] == "Advanced Robot Navigation Systems"
    assert entries["smith2020robot"]["author"] == "Smith, John and Jones, Mary"
    assert entries["smith2020robot"]["year"] == "2020"

    assert "ivanov2022control" in entries
    assert entries["ivanov2022control"]["title"] == "Теория автоматического управления"
    assert entries["ivanov2022control"]["journal"] == "Труды конференции по автоматизации"
    assert entries["ivanov2022control"]["year"] == "2022"

def test_chunk_text():
    text = "This is a sentence. " * 30  # length is 600 chars
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 200

def test_bm25_retriever():
    corpus = [
        {"text": "Робототехника и искусственный интеллект активно развиваются в последние годы.", "metadata": {"key": "doc1"}},
        {"text": "Методы глубокого обучения показывают высокую точность в задачах компьютерного зрения.", "metadata": {"key": "doc2"}},
        {"text": "Системы автоматического управления требуют устойчивости по Ляпунову.", "metadata": {"key": "doc3"}},
    ]
    retriever = BM25Retriever(corpus)
    
    # Query for control theory keywords
    res1 = retriever.retrieve("автоматическое управление Ляпунов", top_k=1)
    assert len(res1) == 1
    assert res1[0]["metadata"]["key"] == "doc3"
    
    # Query for deep learning / vision keywords
    res2 = retriever.retrieve("компьютерное зрение обучение", top_k=1)
    assert len(res2) == 1
    assert res2[0]["metadata"]["key"] == "doc2"

class MockLlama:
    def __init__(self, expected_response):
        self.expected_response = expected_response

    def __call__(self, prompt, max_tokens=1024, stop=None):
        return {
            "choices": [
                {
                    "text": self.expected_response
                }
            ]
        }

def test_nli_citation_judge_supported():
    mock_response = """
    <think>
    Sentence is supported because the snippet explicitly confirms that robot navigation has advanced.
    </think>
    {
      "status": "SUPPORTED",
      "explanation_zh": "文献片段明确证实了机器人导航系统的先进性，与句子相符。",
      "evidence_snippet": "Advanced Robot Navigation Systems"
    }
    """
    mock_llm = MockLlama(mock_response)
    judge = NLICitationJudge(mock_llm)
    
    res = judge.verify_citation(
        "Робототехническая навигация совершила огромный скачок вперед.",
        ["Advanced Robot Navigation Systems has made significant progress in 2020."]
    )
    assert res["status"] == "SUPPORTED"
    assert "导航系统" in res["explanation_zh"]
    assert res["evidence_snippet"] == "Advanced Robot Navigation Systems"
    assert "navigation has advanced" in res["think"]

def test_nli_citation_judge_contradicted():
    mock_response = """
    <think>
    The sentence claims performance improved by 10x, but reference says it performed similarly. This is a contradiction.
    </think>
    {
      "status": "CONTRADICTED",
      "explanation_zh": "论文声称提升了十倍，但文献表明两者结果类似，存在逻辑冲突。",
      "evidence_snippet": "showed similar results"
    }
    """
    mock_llm = MockLlama(mock_response)
    judge = NLICitationJudge(mock_llm)
    
    res = judge.verify_citation(
        "Наш метод превосходит базовый в 10 раз.",
        ["Our tests showed similar results between the two methods."]
    )
    assert res["status"] == "CONTRADICTED"
    assert "十倍" in res["explanation_zh"]
    assert res["evidence_snippet"] == "showed similar results"

def test_extract_bibliography_mapping():
    from naturalization_layer.citation_integrity import extract_bibliography_mapping
    text = """
    Some research draft content.
    Another sentence.
    
    Список литературы
    [1] Smith J. Advanced robotics navigation. 2020.
    2. Ivanov I.
       Theory of control. 2022.
    """
    mapping = extract_bibliography_mapping(text)
    assert "1" in mapping
    assert mapping["1"] == "Smith J. Advanced robotics navigation. 2020."
    assert "2" in mapping
    assert "Theory of control" in mapping["2"]

def test_reconstruct_abstract():
    from naturalization_layer.rag_retriever import reconstruct_abstract
    inverted_index = {
        "The": [0],
        "robots": [1, 3],
        "are": [2],
        "cool.": [4]
    }
    abstract = reconstruct_abstract(inverted_index)
    assert abstract == "The robots are robots cool."

from unittest.mock import patch, MagicMock
import json

@patch("urllib.request.urlopen")
def test_fetch_openalex_abstract(mock_urlopen):
    from naturalization_layer.rag_retriever import fetch_openalex_abstract
    mock_response = MagicMock()
    mock_json = {
        "results": [
            {
                "display_name": "Test Academic Paper Title",
                "abstract_inverted_index": {
                    "This": [0],
                    "is": [1],
                    "an": [2],
                    "abstract.": [3]
                },
                "open_access": {
                    "is_oa": True
                },
                "best_oa_location": {
                    "pdf_url": "https://example.com/paper.pdf"
                }
            }
        ]
    }
    mock_response.read.return_value = json.dumps(mock_json).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response
    
    res = fetch_openalex_abstract("Test Academic Paper")
    assert res is not None
    assert res["title"] == "Test Academic Paper Title"
    assert res["abstract"] == "This is an abstract."
    assert res["is_oa"] is True
    assert res["pdf_url"] == "https://example.com/paper.pdf"

def test_check_title_similarity():
    from naturalization_layer.rag_retriever import check_title_similarity
    # High similarity case
    sim1 = check_title_similarity("Vasilyev et al. 2023 Deep learning for NLP", "Deep Learning for NLP: A Review")
    # query_words: {"vasilyev", "2023", "deep", "learning", "nlp"}
    # title_words: {"deep", "learning", "nlp", "review"} (stopwords 'for', 'a' removed)
    # intersection: {"deep", "learning", "nlp"} (3 words)
    # sim = 3 / 4 = 0.75
    assert sim1 == 0.75
    assert sim1 >= 0.45
    
    # Low similarity case
    sim2 = check_title_similarity("Vasilyev 2023 control theory", "Deep Learning for NLP: A Review")
    assert sim2 < 0.45

def test_extract_citation_keys_dash():
    from backend.main import extract_citation_keys
    # Test standard hyphen range
    assert extract_citation_keys("See [4-6] for details.") == ["4", "5", "6"]
    # Test en-dash range
    assert extract_citation_keys("See [4–6] for details.") == ["4", "5", "6"]
    # Test em-dash range
    assert extract_citation_keys("See [4—6] for details.") == ["4", "5", "6"]

def test_nli_citation_judge_hallucinated_evidence():
    mock_response = """
    {
      "status": "SUPPORTED",
      "explanation_zh": "模型支持论点。",
      "evidence_snippet": "This is a hallucinated rewrite of snippet"
    }
    """
    mock_llm = MockLlama(mock_response)
    judge = NLICitationJudge(mock_llm)
    
    res = judge.verify_citation(
        "Робототехническая навигация совершила огромный скачок вперед.",
        ["Advanced Robot Navigation Systems has made significant progress in 2020."]
    )
    assert res["status"] == "SUPPORTED"
    # Because evidence_snippet was not in the original snippet, it should be wrapped with [模型摘要]
    assert res["evidence_snippet"].startswith("[模型摘要]")

def test_nli_citation_judge_failed_neutral():
    # Simulate an error in LLM call
    class BadLlama:
        def __call__(self, *args, **kwargs):
            raise RuntimeError("API Timeout")
            
    judge = NLICitationJudge(BadLlama())
    res = judge.verify_citation(
        "Робототехническая навигация совершила огромный скачок вперед.",
        ["Advanced Robot Navigation Systems has made significant progress in 2020."]
    )
    assert res["status"] == "AUDIT_FAILED"
    assert "审计异常" in res["explanation_zh"]


