import spacy
import re

CLICHES = [r"важно отметить, что", r"таким образом", r"в заключение"]

def analyze_text_rules(text: str) -> dict:
    try:
        nlp = spacy.load("ru_core_news_sm")
        doc = nlp(text)
        sentences = list(doc.sents)
    except Exception:
        # fallback for testing if model isn't installed
        class MockSent:
            def __init__(self, t): self.text = t; self.is_punct = False
            def __iter__(self): return iter([MockSent(w) for w in self.text.split()])
        sentences = [MockSent(s) for s in text.split(". ") if s]

    cliche_matches = 0
    matched = []
    text_lower = text.lower()
    
    for cliche in CLICHES:
        if re.search(cliche, text_lower):
            cliche_matches += 1
            matched.append(cliche.replace('\\', ''))
            
    lengths = [len([t for t in s if not getattr(t, 'is_punct', False)]) for s in sentences]
    variance = 0.0
    if len(lengths) > 1:
        mean = sum(lengths) / len(lengths)
        variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
            
    return {
        "sentence_count": len(sentences),
        "cliche_matches": cliche_matches,
        "matched_cliches": matched,
        "length_variance": variance,
        "sentences": [getattr(s, 'text', str(s)) for s in sentences]
    }
