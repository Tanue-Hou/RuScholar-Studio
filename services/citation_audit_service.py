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
