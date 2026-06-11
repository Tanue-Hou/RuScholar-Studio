import asyncio
import re
from naturalization_layer.rag_retriever import fetch_openalex_abstract
from services.shared_state import session_references, model_lock

def extract_citation_keys(sentence: str) -> list[str]:
    """
    Extract citation keys (like 1, smith2020) from bracket citations in a sentence.
    Supports range parsing like [4-6] -> ['4', '5', '6'].
    """
    raw_keys = re.findall(r'\[([^\]]+)\]', sentence)
    keys = []
    for rk in raw_keys:
        rk = rk.strip()
        if re.search(r'[a-zA-Zа-яА-ЯёЁ]', rk):
            parts = rk.split(';')
            for part in parts:
                clean_key = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9]', '', part).lower()
                if clean_key:
                    keys.append(clean_key)
        else:
            parts = re.split(r'[,;]', rk)
            for part in parts:
                part = part.strip()
                range_match = re.match(r'^(\d+)\s*[\-–—]\s*(\d+)$', part)
                if range_match:
                    start = int(range_match.group(1))
                    end = int(range_match.group(2))
                    for i in range(start, end + 1):
                        keys.append(str(i))
                else:
                    clean_key = re.sub(r'\D', '', part)
                    if clean_key:
                        keys.append(clean_key)
    return keys

async def perform_nli_citation_audit(
    text_str: str, 
    session_id: str, 
    engine_type: str, 
    api_key: str, 
    base_url: str, 
    citation_judge
) -> list:
    """
    Check if the citation keys in text_str are supported by local/online reference sources.
    """
    keys = extract_citation_keys(text_str)
    if not keys:
        return []
        
    session_ref = session_references.get(session_id, {})
    retrievers = session_ref.get("retrievers", {})
    bibtex_db = session_ref.get("bibtex", {})
    online_cache = session_ref.get("online_cache", {})
    bib_mapping = session_ref.get("bib_mapping", {})
    
    audits = []
    for key in keys:
        key_lower = key.lower()
        # 1. Local RAG first
        if key_lower in retrievers:
            retriever = retrievers[key_lower]
            retrieved = retriever.retrieve(text_str, top_k=3)
            snippets = [r["text"] for r in retrieved]
            source = "local"
            
            # Fetch BibTeX metadata if available for titles
            meta = bibtex_db.get(key_lower, {})
            title = meta.get("title", f"文献 {key}")
            author = meta.get("author", "")
            year = meta.get("year", "")
        else:
            # 2. Check online cache first
            if key_lower in online_cache:
                cache_entry = online_cache[key_lower]
                if cache_entry:
                    snippets = [cache_entry["abstract"]] if cache_entry["abstract"] else []
                    title = cache_entry["title"]
                    author = ""
                    year = ""
                    source = "online"
                else:
                    continue  # Cached retrieval failure
            else:
                # 3. Retrieve online using citation mapping
                query_str = ""
                # Try from BibTeX metadata first if key exists there
                if key_lower in bibtex_db:
                    meta = bibtex_db[key_lower]
                    query_str = f"{meta.get('title', '')} {meta.get('author', '')} {meta.get('year', '')}".strip()
                # Otherwise, fallback to the references list parsed from text
                elif key_lower in bib_mapping:
                    query_str = bib_mapping[key_lower]
                
                # If no search query, we cannot audit
                if not query_str:
                    continue
                    
                online_res = await asyncio.to_thread(fetch_openalex_abstract, query_str)
                
                if online_res:
                    online_cache[key_lower] = online_res
                    snippets = [online_res["abstract"]] if online_res["abstract"] else []
                    title = online_res["title"]
                    author = ""
                    year = ""
                    source = "online"
                else:
                    online_cache[key_lower] = None
                    continue
            
        if not snippets:
            continue
            
        if engine_type == "local":
            async with model_lock:
                nli_res = await asyncio.to_thread(
                    citation_judge.verify_citation,
                    text_str, snippets, engine_type, api_key, base_url
                )
        else:
            nli_res = await asyncio.to_thread(
                citation_judge.verify_citation,
                text_str, snippets, engine_type, api_key, base_url
            )
            
        audits.append({
            "key": key,
            "title": title,
            "author": author,
            "year": year,
            "status": nli_res["status"],
            "explanation_zh": nli_res["explanation_zh"],
            "evidence_snippet": nli_res["evidence_snippet"] if source == "local" else f"[网络学术文献摘要] {nli_res['evidence_snippet'] or snippets[0][:200]}...",
            "think": nli_res.get("think"),
            "source": source
        })
    return audits

def extract_claims(text: str) -> list[dict]:
    """
    Extract academic claims from body text and classify claim types.
    """
    from naturalization_layer.rules_engine import analyze_text_rules
    rules_res = analyze_text_rules(text)
    sentences = rules_res.get("sentences", [])
    
    claims = []
    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
            
        keys = extract_citation_keys(s_clean)
        s_lower = s_clean.lower()
        if keys:
            claim_type = "cited_assertion"
        elif any(w in s_lower for w in ["показывает", "доказывает", "следовательно", "таким образом", "в результате", "предложено", "разработано", "поэтому", "вывод", "иллюстрирует"]):
            claim_type = "scientific_inference"
        else:
            claim_type = "general_statement"
            
        claims.append({
            "sentence": s_clean,
            "claim_type": claim_type,
            "citation_keys": keys
        })
    return claims

def classify_evidence_need(claim: str) -> dict:
    """
    Assess if a claim needs support (e.g. axiom vs citation needed).
    """
    claim_lower = claim.lower()
    
    keys = extract_citation_keys(claim)
    if keys:
        return {
            "claim": claim,
            "need_level": "already_supported",
            "reason_zh": "该断言已包含文献引用，无需额外关联。",
            "reason_ru": "Утверждение уже содержит ссылку на литературу."
        }
        
    from naturalization_layer.russian_lemmatizer import lemmatize_sentence
    claim_lemmas = lemmatize_sentence(claim_lower)
    
    common_knowledge_lemmas = ["известный", "очевидный", "аксиома", "общепризнанный", "правило", "классический"]
    if any(w in claim_lemmas for w in common_knowledge_lemmas):
        return {
            "claim": claim,
            "need_level": "low",
            "reason_zh": "常识或公理化表述，通常不需要引文支持。",
            "reason_ru": "Общеизвестный факт или аксиома, не требующая подтверждения."
        }
        
    novel_lemmas = ["предложить", "разработать", "создать", "впервые", "новизна", "получить", "автор", "работа"]
    if any(w in claim_lemmas for w in novel_lemmas):
        return {
            "claim": claim,
            "need_level": "medium",
            "reason_zh": "描述本工作的新方法或新成果，需引文进行横向对比，但属于自主结论。",
            "reason_ru": "Описание нового научного вклада; требует сравнения с аналогами, но является собственным выводом."
        }
        
    empirical_lemmas = ["потому", "вследствие", "показывать", "доказывать", "превосходить", "увеличивать", "снижать", "эксперимент", "свойство"]
    if any(w in claim_lemmas for w in empirical_lemmas):
        return {
            "claim": claim,
            "need_level": "high",
            "reason_zh": "包含因果推论或实验事实断言，强烈建议添加文献或实验数据支撑。",
            "reason_ru": "Содержит причинно-следственную связь или экспериментальный факт; рекомендуется добавить ссылку."
        }
        
    return {
        "claim": claim,
        "need_level": "medium",
        "reason_zh": "一般性学术叙述，可能需要背景文献支撑。",
        "reason_ru": "Стандартное академическое утверждение, может потребоваться контекстная ссылка."
    }

async def bind_evidence(claim: str, references: list[str], session_id: str) -> dict:
    """
    Perform local/online RAG and bind matching snippets for the given claim and reference keys.
    """
    if not references:
        return {
            "claim": claim,
            "bound_references": []
        }
        
    session_ref = session_references.get(session_id, {})
    retrievers = session_ref.get("retrievers", {})
    bibtex_db = session_ref.get("bibtex", {})
    online_cache = session_ref.get("online_cache", {})
    bib_mapping = session_ref.get("bib_mapping", {})
    
    bound_references = []
    for key in references:
        key_lower = key.lower()
        snippets = []
        source = "unknown"
        title = f"文献 {key}"
        author = ""
        year = ""
        
        if key_lower in retrievers:
            retriever = retrievers[key_lower]
            retrieved = retriever.retrieve(claim, top_k=3)
            snippets = [r["text"] for r in retrieved]
            source = "local"
            
            meta = bibtex_db.get(key_lower, {})
            title = meta.get("title", title)
            author = meta.get("author", "")
            year = meta.get("year", "")
        else:
            if key_lower in online_cache:
                cache_entry = online_cache[key_lower]
                if cache_entry:
                    snippets = [cache_entry["abstract"]] if cache_entry["abstract"] else []
                    title = cache_entry["title"]
                    source = "online"
            else:
                query_str = ""
                if key_lower in bibtex_db:
                    meta = bibtex_db[key_lower]
                    query_str = f"{meta.get('title', '')} {meta.get('author', '')} {meta.get('year', '')}".strip()
                elif key_lower in bib_mapping:
                    query_str = bib_mapping[key_lower]
                    
                if query_str:
                    online_res = await asyncio.to_thread(fetch_openalex_abstract, query_str)
                    if online_res:
                        online_cache[key_lower] = online_res
                        snippets = [online_res["abstract"]] if online_res["abstract"] else []
                        title = online_res["title"]
                        source = "online"
                    else:
                        online_cache[key_lower] = None
                        
        bound_references.append({
            "citation_key": key,
            "title": title,
            "author": author,
            "year": year,
            "source": source,
            "snippets": snippets
        })
        
    return {
        "claim": claim,
        "bound_references": bound_references
    }

