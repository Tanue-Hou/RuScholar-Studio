import spacy
import re

class TextPreprocessor:
    def __init__(self):
        self.patterns = {
            "LATEX": r"\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$",
            "REF": r"\[\s*\d+(?:[\s,;\-–—\d]*)\s*\]",
            "FIG_TBL": r"\b(?:рис|рисунке|рисунках|табл|таблице|таблицах|уравнении|формуле|уравнениях|формулах)\.?\s*\d+(?:\.\d+)*\b",
            "SIMPLE_MATH": r"\b[a-zA-Zα-ωΑ-Ω]\b\s*=\s*[\w\d]+|(?:\b[a-zA-Zα-ωΑ-Ω]\b|\b[a-zA-Zα-ωΑ-Ω]_\w+)\s*(?:[=<>+\-*/\s]{1,3}\s*(?:\d+|\b[a-zA-Zα-ωΑ-Ω]\b|\b[a-zA-Zα-ωΑ-Ω]_\w+))+"
        }

    def protect(self, text: str) -> tuple[str, dict[str, str]]:
        mapping = {}
        protected_text = text
        placeholder_counter = 0
        
        for key, pattern in self.patterns.items():
            def replace_match(match):
                nonlocal placeholder_counter
                ph = f"__PROTECTED_{key}_{placeholder_counter}__"
                mapping[ph] = match.group(0)
                placeholder_counter += 1
                return ph
            
            flags = re.IGNORECASE if key == "FIG_TBL" else 0
            protected_text = re.sub(pattern, replace_match, protected_text, flags=flags)
            
        return protected_text, mapping

    def restore(self, text: str, mapping: dict[str, str]) -> str:
        restored = text
        for ph in sorted(mapping.keys(), key=len, reverse=True):
            restored = restored.replace(ph, mapping[ph])
        return restored

CONNECTORS = [
    r"\bтаким образом\b",
    r"\bследовательно\b",
    r"\bв связи с этим\b",
    r"\bоднако\b",
    r"\bв частности\b",
    r"\bкак правило\b",
    r"\bкроме того\b",
    r"\bв соответствии с\b",
    r"\bс одной стороны\b",
    r"\bс другой стороны\b",
    r"\bв то же время\b",
    r"\bтем не менее\b",
    r"\bиз этого следует, что\b",
    r"\bна основании полученных данных\b",
    r"\bкак показано на\b"
]

CLICHES = [
    r"\bважно отметить, что\b",
    r"\bследует отметить, что\b",
    r"\bследует подчеркнуть, что\b",
    r"\bнеобходимо подчеркнуть, что\b",
    r"\bобращает на себя внимание тот факт, что\b",
    r"\bнеобходимо обратить внимание на то, что\b",
    r"\bисходя из этого, можно утверждать, что\b",
    r"\bв данном контексте\b",
    r"\bв современной науке\b",
    r"\bиграет ключевую роль\b",
    r"\bиграет важную роль\b",
    r"\bявляется неотъемлемой частью\b",
    r"\bширокий спектр\b",
    r"\bкак упоминалось ранее\b",
    r"\bкак было сказано выше\b",
    r"\bс целью повышения эффективности\b",
    r"\bпредставляет собой\b",
    r"\bна сегодняшний день\b",
    r"\bв рамках данного исследования\b",
    r"\bособое внимание уделяется\b"
]

def max_genitive_chain_length(token):
    genitive_children = [
        child for child in token.children
        if child.pos_ in ("NOUN", "PROPN") and "Gen" in child.morph.get("Case", [])
    ]
    if not genitive_children:
        return 0
    return 1 + max(max_genitive_chain_length(child) for child in genitive_children)

def get_genitive_chain_tokens(token):
    chain = [token]
    genitive_children = [
        child for child in token.children
        if child.pos_ in ("NOUN", "PROPN") and "Gen" in child.morph.get("Case", [])
    ]
    if genitive_children:
        best_child = max(genitive_children, key=max_genitive_chain_length)
        chain.extend(get_genitive_chain_tokens(best_child))
    return chain

def analyze_text_rules(text: str) -> dict:
    preprocessor = TextPreprocessor()
    protected_text, mapping = preprocessor.protect(text)
    
    # Identify bibliography section start
    lower_text = text.lower()
    bib_headers = ["список литературы", "литература", "references", "библиографический список"]
    bib_start = -1
    for header in bib_headers:
        idx = lower_text.rfind(header)
        if idx != -1:
            bib_start = idx
            break
            
    try:
        nlp = spacy.load("ru_core_news_sm")
        doc = nlp(protected_text)
        sentences_doc = list(doc.sents)
    except Exception:
        class MockSent:
            def __init__(self, t):
                self.text = t
                self.is_punct = False
            def __iter__(self):
                class MockToken:
                    def __init__(self, w):
                        self.text = w
                        self.pos_ = "NOUN" if w.istitle() else "VERB"
                        self.morph = {}
                        self.children = []
                        self.dep_ = "nmod"
                    def __getattr__(self, name):
                        return None
                return iter([MockToken(w) for w in self.text.split()])
        sentences_doc = [MockSent(s.strip()) for s in protected_text.split(". ") if s.strip()]

    sentences_restored = []
    sentence_diagnostics = []
    
    total_cliches_count = 0
    all_matched_cliches = set()
    
    search_pos = 0
    for sent in sentences_doc:
        sent_text_protected = sent.text
        sent_text_restored = preprocessor.restore(sent_text_protected, mapping)
        sentences_restored.append(sent_text_restored)
        
        is_bibliography = False
        if bib_start != -1:
            char_pos = text.find(sent_text_restored, search_pos)
            if char_pos != -1:
                search_pos = char_pos + len(sent_text_restored)
                if char_pos >= bib_start:
                    is_bibliography = True
            else:
                if search_pos >= bib_start:
                    is_bibliography = True
        
        sent_text_restored_lower = sent_text_restored.lower()
        cliches_found = []
        for cliche in CLICHES:
            if re.search(cliche, sent_text_restored_lower):
                cliches_found.append(cliche.replace(r"\b", "").replace("\\", ""))
                total_cliches_count += 1
                all_matched_cliches.add(cliche.replace(r"\b", "").replace("\\", ""))
                
        connectors_found = []
        for conn in CONNECTORS:
            if re.search(conn, sent_text_restored_lower):
                connectors_found.append(conn.replace(r"\b", "").replace("\\", ""))
                
        words_count = 0
        nouns_count = 0
        verbs_count = 0
        passive_count = 0
        genitive_chains = []
        
        is_spacy_sent = not hasattr(sent, 'is_punct')
        if is_spacy_sent:
            for token in sent:
                if token.is_punct or token.is_space:
                    continue
                if token.text.startswith("__PROTECTED_"):
                    continue
                
                words_count += 1
                
                if token.pos_ in ("NOUN", "PROPN"):
                    nouns_count += 1
                    depth = max_genitive_chain_length(token)
                    if depth >= 2:
                        chain_tokens = get_genitive_chain_tokens(token)
                        indices = [x.i for x in chain_tokens]
                        min_i, max_i = min(indices), max(indices)
                        span = token.doc[min_i:max_i+1]
                        span_restored = preprocessor.restore(span.text, mapping)
                        genitive_chains.append(span_restored)
                        
                elif token.pos_ in ("VERB", "AUX"):
                    verbs_count += 1
                    is_passive = (
                        "Pass" in token.morph.get("Voice", []) or 
                        ("Mid" in token.morph.get("Voice", []) and token.text.endswith(("ся", "сь")))
                    )
                    if is_passive:
                        passive_count += 1
        else:
            words_count = len([w for w in sent_text_protected.split() if not w.startswith("__PROTECTED_")])
            nouns_count = words_count // 2
            verbs_count = max(1, words_count // 5)
            
        nv_ratio = nouns_count / max(1, verbs_count)
        
        total_tokens = len([t for t in sent if not t.is_punct]) if is_spacy_sent else len(sent_text_protected.split())
        protected_tokens_count = len([t for t in sent if t.text.startswith("__PROTECTED_")]) if is_spacy_sent else len([w for w in sent_text_protected.split() if w.startswith("__PROTECTED_")])
        is_protected = (protected_tokens_count / max(1, total_tokens)) > 0.5 if total_tokens > 0 else False
        
        sentence_diagnostics.append({
            "original_text": sent_text_restored,
            "word_count": words_count,
            "verbs_count": verbs_count,
            "nv_ratio": round(nv_ratio, 2),
            "passive_count": passive_count,
            "genitive_chains": list(set(genitive_chains)),
            "cliches_found": cliches_found,
            "connectors_found": connectors_found,
            "is_protected": is_protected,
            "is_bibliography": is_bibliography
        })

    lengths = [len([t for t in s if not getattr(t, 'is_punct', False)]) for s in sentences_doc]
    variance = 0.0
    mean_len = 0.0
    if len(lengths) > 0:
        mean_len = sum(lengths) / len(lengths)
    if len(lengths) > 1:
        variance = sum((x - mean_len) ** 2 for x in lengths) / len(lengths)
        
    global_metrics = {
        "average_sentence_length": round(mean_len, 2),
        "sentence_length_variance": round(variance, 2),
        "total_cliches": total_cliches_count,
        "connector_density": round(sum(len(d["connectors_found"]) for d in sentence_diagnostics) / max(1, len(sentences_doc)), 2)
    }

    return {
        "sentence_count": len(sentences_doc),
        "cliche_matches": total_cliches_count,
        "matched_cliches": list(all_matched_cliches),
        "length_variance": variance,
        "sentences": sentences_restored,
        "sentence_diagnostics": sentence_diagnostics,
        "global_metrics": global_metrics
    }

def should_run_ppl_heuristic(
    diag_rules: dict, 
    mode: str, 
    min_words: int = 6, 
    smart_words: int = 12, 
    fast_words: int = 18
) -> bool:
    """
    Determine whether to run PPL and LLM evaluation on a sentence based on rules and length.
    """
    if diag_rules.get("is_protected", False):
        return False
        
    # Count words using the pre-calculated true word count
    word_count = diag_rules.get("word_count", len(diag_rules.get("original_text", "").split()))
    
    # Absolute minimum word count
    if word_count < min_words:
        return False
        
    if mode == "Deep Scan":
        return True
    elif mode == "Smart Probe":
        return word_count >= smart_words or len(diag_rules.get("cliches_found", [])) > 0
    elif mode == "Fast Check":
        return word_count >= fast_words or len(diag_rules.get("cliches_found", [])) > 0
        
    return False
