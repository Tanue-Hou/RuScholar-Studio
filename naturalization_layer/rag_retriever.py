import re
import math
from collections import Counter

def parse_bibtex(bibtex_str: str) -> dict:
    """
    Parses a BibTeX string and returns a dictionary mapping cite_key -> metadata.
    """
    entries = {}
    chunks = bibtex_str.split('@')
    for chunk in chunks:
        if not chunk.strip():
            continue
        match = re.match(r'^([a-zA-Z0-9_-]+)\s*\{\s*([a-zA-Z0-9_.:-]+)\s*,\s*(.*)$', chunk, re.DOTALL)
        if match:
            entry_type = match.group(1).lower()
            cite_key = match.group(2)
            body = match.group(3)
            
            fields = {}
            # Regex to find key = value where value can be enclosed in {} or "" or plain text
            field_matches = re.finditer(r'([a-zA-Z0-9_-]+)\s*=\s*(?:\{([^{}]*)\}|"([^"]*)"|([a-zA-Z0-9_-]+))', body)
            for fm in field_matches:
                k = fm.group(1).lower()
                val = fm.group(2) or fm.group(3) or fm.group(4)
                if val:
                    fields[k] = val.strip()
            
            entries[cite_key] = {
                "type": entry_type,
                "title": fields.get("title", ""),
                "author": fields.get("author", ""),
                "year": fields.get("year", ""),
                "journal": fields.get("journal", "") or fields.get("booktitle", "")
            }
    return entries

def chunk_text(text: str, chunk_size=500, overlap=100) -> list[str]:
    """
    Splits text into overlapping chunks of a given character size.
    """
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        # Move forward by (chunk_size - overlap)
        next_start = start + chunk_size - overlap
        if next_start >= len(text) or next_start <= start:
            break
        start = next_start
    return chunks

def stem_russian_word(word: str) -> str:
    """
    A simplified Russian light stemmer to strip common noun, adjective, and verb suffixes.
    """
    if len(word) <= 3:
        return word
        
    endings = [
        "ческого", "ческому", "ческих", "ческими", "ческом",
        "ческое", "ческая", "ческие", "ческий", "ческую", "ческой",
        "ующими", "ующего", "ующему", "ующих", "ующем",
        "тельного", "тельному", "тельных", "тельным", "тельном",
        "ание", "ания", "анию", "анием", "ании",
        "ение", "ения", "ению", "ением", "ении",
        "ать", "еть", "ить", "овать", "ывать", "ировать",
        "ского", "скому", "ских", "скими", "ском",
        "ного", "ному", "ных", "ным", "ном", "ное", "ная", "ные", "ный", "ную", "ной",
        "ову", "ова", "ове", "овом", "овы",
        "ого", "ему", "ому", "ыми", "ями", "ях", "ом", "ой", "ей", "ем", "ах", "их", "ых",
        "ие", "ия", "ию", "ии", "ием", "ией", "иями", "иях",
        "ое", "ая", "ее", "ый", "ий", "ые", "ов", "ев",
        "а", "е", "и", "й", "о", "у", "ы", "ь", "я"
    ]
    
    endings.sort(key=len, reverse=True)
    
    for ending in endings:
        if word.endswith(ending):
            stemmed = word[:-len(ending)]
            if len(stemmed) >= 3:
                return stemmed
    return word

class BM25Retriever:
    def __init__(self, corpus: list[dict], k1=1.5, b=0.75):
        """
        corpus is a list of dict: [{"text": str, "metadata": dict}]
        """
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.doc_count = len(corpus)
        
        self.doc_tokens = [self._tokenize(doc["text"]) for doc in corpus]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_len = sum(self.doc_lengths) / self.doc_count if self.doc_count > 0 else 1.0
        
        self.df = Counter()
        for doc_t in self.doc_tokens:
            unique_tokens = set(doc_t)
            for token in unique_tokens:
                self.df[token] += 1
                
        self.doc_tfs = [Counter(tokens) for tokens in self.doc_tokens]
        
    def _tokenize(self, text: str) -> list[str]:
        # Lowercase, find all alphanumeric words, and apply Russian morphological lemmatizer
        from naturalization_layer.russian_lemmatizer import lemmatize_word
        words = re.findall(r'[a-zA-Z0-9а-яА-ЯёЁ]+', text.lower())
        return [lemmatize_word(w) for w in words]
        
    def _idf(self, word: str) -> float:
        df = self.df.get(word, 0)
        # BM25 standard IDF with positive floor protection
        val = (self.doc_count - df + 0.5) / (df + 0.5)
        return math.log(max(val, 1e-5) + 1.0)
        
    def retrieve(self, query: str, top_k=3) -> list[dict]:
        if not self.corpus:
            return []
            
        q_tokens = self._tokenize(query)
        if not q_tokens:
            # If query is empty, return top_k docs from corpus with 0 score
            return [{"text": doc["text"], "metadata": doc["metadata"], "score": 0.0} for doc in self.corpus[:top_k]]
            
        scores = []
        for i in range(self.doc_count):
            score = 0.0
            dl = self.doc_lengths[i]
            tf_dict = self.doc_tfs[i]
            
            for q_t in q_tokens:
                tf = tf_dict.get(q_t, 0)
                if tf > 0:
                    idf = self._idf(q_t)
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (dl / self.avg_doc_len))
                    score += idf * (numerator / denominator)
            scores.append((score, i))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, idx in scores[:top_k]:
            if score > 0.0:
                results.append({
                    "text": self.corpus[idx]["text"],
                    "metadata": self.corpus[idx]["metadata"],
                    "score": score
                })
        return results

def reconstruct_abstract(inverted_index: dict) -> str:
    """
    Reconstructs the original abstract string from OpenAlex's abstract_inverted_index.
    """
    if not inverted_index:
        return ""
    max_idx = 0
    for positions in inverted_index.values():
        if positions:
            max_idx = max(max_idx, max(positions))
    tokens = [""] * (max_idx + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            if pos < len(tokens):
                tokens[pos] = word
    return " ".join([t for t in tokens if t])

def check_title_similarity(query_str: str, retrieved_title: str) -> float:
    """
    Check if the retrieved title core words overlap sufficiently with the query string.
    """
    import re
    from naturalization_layer.russian_lemmatizer import lemmatize_word
    def get_words(text: str) -> set[str]:
        words = re.findall(r'[a-zA-Z0-9а-яА-ЯёЁ]{3,}', text.lower())
        stopwords = {
            'the', 'and', 'for', 'with', 'from', 'journal', 'proceedings', 'conference',
            'arxiv', 'preprint', 'volume', 'issue', 'pages', 'editorial', 'letter',
            'analysis', 'study', 'research', 'paper', 'method', 'methods', 'using', 'based'
        }
        return set(lemmatize_word(w) for w in words if w not in stopwords)

    query_words = get_words(query_str)
    title_words = get_words(retrieved_title)
    
    if not title_words:
        return 0.0
        
    intersection = title_words.intersection(query_words)
    return len(intersection) / len(title_words)

def fetch_openalex_abstract(query_str: str, api_key: str = "") -> dict:
    """
    Queries the OpenAlex REST API to find a work matching query_str.
    Returns a dict containing:
      {
        "title": str,
        "abstract": str,
        "is_oa": bool,
        "pdf_url": str
      }
    or None if not found, failed, or similarity check fails.
    """
    import urllib.request
    import urllib.parse
    import json
    
    if not query_str.strip():
        return None
        
    base_url = "https://api.openalex.org/works"
    params = {
        "search": query_str,
        "per_page": 1
    }
    if api_key:
        params["api_key"] = api_key
        
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"
    
    headers = {
        "User-Agent": "ThesisButlerCitationAudit/1.0 (mailto:tanue.writing@gmail.com)"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            results = data.get("results", [])
            if not results:
                return None
                
            work = results[0]
            title = work.get("display_name", "")
            
            # Verify similarity between the expected query and the retrieved title
            sim = check_title_similarity(query_str, title)
            if sim < 0.45:
                print(f"OpenAlex result title mismatch (similarity {sim:.2f} < 0.45). Query: '{query_str}', Got: '{title}'")
                return None
                
            abstract_inverted = work.get("abstract_inverted_index")
            abstract = reconstruct_abstract(abstract_inverted) if abstract_inverted else ""
            
            is_oa = work.get("open_access", {}).get("is_oa", False)
            pdf_url = work.get("best_oa_location", {}).get("pdf_url") or ""
            
            return {
                "title": title,
                "abstract": abstract,
                "is_oa": is_oa,
                "pdf_url": pdf_url
            }
    except Exception as e:
        print(f"OpenAlex request failed for query '{query_str}': {e}")
        return None

