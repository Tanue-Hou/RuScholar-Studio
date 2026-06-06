import re

def calculate_ngram_similarity(text1: str, text2: str, n: int = 3) -> float:
    """
    Calculate character-level n-gram overlap cosine similarity.
    """
    def get_ngrams(text):
        clean = re.sub(r'\W+', '', text.lower())
        return set(clean[i:i+n] for i in range(len(clean)-n+1))
    
    ngrams1 = get_ngrams(text1)
    ngrams2 = get_ngrams(text2)
    if not ngrams1 or not ngrams2:
        return 0.0
    return len(ngrams1 & ngrams2) / len(ngrams1 | ngrams2)

# Sample database mimicking user's reference library / DisserCat database
MOCK_REFERENCES = [
    {
        "title": "Оценка коэффициентов сцепления дорожного покрытия на основе нейронной сети",
        "author": "Иванов И.И.",
        "text": "Оценка коэффициента сцепления дорожного покрытия основана на использовании нейронной сети для классификации состояний дороги."
    },
    {
        "title": "Интеллектуальное управление мобильными роботами в неопределенных средах",
        "author": "Петров П.П.",
        "text": "Интеллектуальное управление мобильными роботами осуществляется за счет интеграции нечеткой логики и генетических алгоритмов."
    }
]

def check_source_similarity(sentence: str, has_citation: bool) -> dict | None:
    """
    Check if a sentence has high similarity to known reference fragments.
    If yes, flag integrity risk:
    - citation_gap (high similarity but no citation marker like [1])
    - semantic_plagiarism_risk (high similarity with citation marker present)
    """
    for ref in MOCK_REFERENCES:
        sim = calculate_ngram_similarity(sentence, ref["text"])
        if sim > 0.45: # High similarity threshold
            if not has_citation:
                return {
                    "issue_type": "citation_gap",
                    "severity": "high",
                    "evidence": sentence[:50] + "...",
                    "explanation_zh": f"发现文献引用缺失：与 {ref['author']} 的文献《{ref['title']}》高度相似（匹配度 {int(sim*100)}%），但未标记引用符号。",
                    "explanation_ru": f"Пропуск цитирования: высокая схожесть с работой {ref['author']} ({int(sim*100)}%), ссылка отсутствует.",
                    "rewrite_suggestion": f"Добавьте ссылку на источник: [{ref['author']}, {ref['title']}]"
                }
            else:
                return {
                    "issue_type": "semantic_plagiarism_risk",
                    "severity": "medium",
                    "evidence": sentence[:50] + "...",
                    "explanation_zh": f"存在疑似学术改写痕迹：与 {ref['author']} 的文献《{ref['title']}》相似度达 {int(sim*100)}%，注意重构句子以提高原创性。",
                    "explanation_ru": f"Подозрение на глубокий парафраз работы {ref['author']} (сходство {int(sim*100)}%).",
                    "rewrite_suggestion": "Попробуйте переформулировать ключевые утверждения своими словами или добавьте собственный комментарий."
                }
    return None
