import re

def calculate_translationese_risk(nv_ratios: list, passive_counts: list, genitive_chain_counts: list) -> float:
    """
    Calculate final document-level Translationese Risk percentage.
    """
    if not nv_ratios:
        return 0.0
        
    trans_scores = []
    for nv, pas, gen in zip(nv_ratios, passive_counts, genitive_chain_counts):
        nv_score = min(2.0, max(0.0, nv - 1.5)) / 2.0
        pas_score = min(1.0, pas * 0.5)
        gen_score = min(1.0, gen * 0.5)
        trans_scores.append((nv_score + pas_score + gen_score) / 3.0)
        
    return round((sum(trans_scores) / len(trans_scores)) * 100, 1)

def run_translationese_checks(sent_text: str, stats: dict) -> list[dict]:
    """
    Run sentence-level checks for advanced Translationese:
    1. Noun stacking: nv_ratio > 4.5
    2. Verb deficiency: sent has 0 verbs and > 8 words (excluding math/citations)
    3. Formula parameter explanation: sent contains protected LaTeX formula but misses explanation words (где, обозначает, выражает, при этом)
    """
    warnings = []
    
    # 1. Noun stacking
    nv_ratio = stats.get("nv_ratio", 0.0)
    if nv_ratio > 4.5:
        warnings.append({
            "issue_type": "translationese_noun_stacking",
            "severity": "medium",
            "evidence": f"Ratio NOUN/VERB = {nv_ratio}",
            "explanation_zh": "名词堆叠率过高（名词与动词比值 > 4.5），可能导致学术句式臃肿和翻译腔。",
            "explanation_ru": "Избыточное нагромождение существительных (отношение существительных к глаголам > 4.5).",
            "rewrite_suggestion": "Попробуйте заменить некоторые отглагольные существительные на личные глаголы."
        })
        
    # 2. Verb deficiency (no verb but long sentence)
    word_count = stats.get("word_count", 0)
    passive_count = stats.get("passive_count", 0)
    # To determine if there are verbs, check stats or do a simple morph check.
    # Spacy rule engine populates stats: word_count, passive_count. Let's pass verb count in stats.
    # In rules_engine.py we calculate verb count: verbs_count. Let's make sure it is in stats.
    verbs_count = stats.get("verbs_count", 0)
    if verbs_count == 0 and word_count > 8:
        warnings.append({
            "issue_type": "translationese_verb_deficiency",
            "severity": "medium",
            "evidence": sent_text[:40] + "...",
            "explanation_zh": "句子中缺少谓语动词（词数 > 8 但无动词），导致句子结构不完整，呈现典型的名词化机器翻译特征。",
            "explanation_ru": "Отсутствие смыслового глагола (сказуемого) в длинном предложении (более 8 слов).",
            "rewrite_suggestion": "Добавьте личную форму глагола для выражения действия."
        })
        
    # 3. Formula parameter explanation
    # If the sentence contains a protected LaTeX match and doesn't explain its elements
    if "__PROTECTED_LATEX_" in sent_text:
        sent_lower = sent_text.lower()
        explanation_keywords = ["где", "обозначает", "выражает", "при этом", "определяется как"]
        if not any(k in sent_lower for k in explanation_keywords):
            warnings.append({
                "issue_type": "style_formula_unexplained",
                "severity": "low",
                "evidence": "[Формула без пояснений]",
                "explanation_zh": "公式中缺少参数说明（例如缺少 'где ... обозначает ...' 结构）。",
                "explanation_ru": "В формуле отсутствует расшифровка условных обозначений параметров (где... обозначает...).",
                "rewrite_suggestion": "Добавьте поясняющую конструкцию: ', где X — это...'"
            })
            
    return warnings
