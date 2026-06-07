import re

def parse_bibliography_numbers(text: str) -> set[int]:
    """
    Find references listed in the bibliography section at the end of the document.
    Bibliography sections typically start with 'Список литературы', 'Литература', 'References', etc.
    """
    lower_text = text.lower()
    bib_headers = ["список литературы", "литература", "references", "библиографический список"]
    
    bib_start = -1
    for header in bib_headers:
        idx = lower_text.rfind(header)
        if idx != -1:
            bib_start = idx
            break
            
    if bib_start == -1:
        return set()
        
    bib_section = text[bib_start:]
    # Match patterns like [1], 1., [1] Иванов, etc.
    numbers = set()
    matches = re.findall(r'(?:^|\n)\s*(?:\[(\d+)\]|(\d+)\.\s+)', bib_section)
    for m in matches:
        num_str = m[0] or m[1]
        if num_str:
            numbers.add(int(num_str))
    return numbers

def extract_bibliography_mapping(text: str) -> dict[str, str]:
    """
    Parses the bibliography section at the end of the text,
    and returns a mapping from reference number/key (as str) to the full reference line.
    """
    lower_text = text.lower()
    bib_headers = ["список литературы", "литература", "references", "библиографический список"]
    
    bib_start = -1
    for header in bib_headers:
        idx = lower_text.rfind(header)
        if idx != -1:
            bib_start = idx
            break
            
    if bib_start == -1:
        return {}
        
    bib_section = text[bib_start:]
    lines = bib_section.split('\n')
    
    mapping = {}
    current_key = None
    current_text = []
    
    pattern = r'^\s*(?:\[([a-zA-Z0-9_.-]+)\]|([0-9]+)\.\s+)'
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Skip header line itself
        if any(h in stripped.lower() for h in bib_headers) and len(stripped) < 30:
            continue
            
        match = re.match(pattern, line)
        if match:
            if current_key and current_text:
                mapping[current_key] = " ".join(current_text).strip()
            
            key = match.group(1) or match.group(2)
            content = line[match.end():].strip()
            current_key = key.lower()
            current_text = [content]
        else:
            if current_key:
                current_text.append(stripped)
                
    if current_key and current_text:
        mapping[current_key] = " ".join(current_text).strip()
        
    return mapping

def parse_citations_in_text(text: str) -> set[int]:
    """
    Find all citation numbers used in the document text, e.g. [1], [2, 3], [4-7].
    """
    # Remove the bibliography section if exists, so we only look at text citations
    lower_text = text.lower()
    bib_headers = ["список литературы", "литература", "references", "библиографический список"]
    bib_start = -1
    for header in bib_headers:
        idx = lower_text.rfind(header)
        if idx != -1:
            bib_start = idx
            break
            
    body_text = text[:bib_start] if bib_start != -1 else text
    
    citations = set()
    # Find patterns like [1], [1, 2], [1-3], [1, 2, 4-6]
    bracket_matches = re.findall(r'\[\s*(\d+(?:[\s,;\-–—\d]*))\s*\]', body_text)
    
    for match in bracket_matches:
        # Split by comma or semicolon
        parts = re.split(r'[,;]', match)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Check if it is a range like 1-3
            range_match = re.match(r'^(\d+)\s*[\-–—]\s*(\d+)$', part)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2))
                for num in range(start, end + 1):
                    citations.add(num)
            elif part.isdigit():
                citations.add(int(part))
                
    return citations

def check_citation_integrity(text: str) -> dict:
    """
    Run integrity checks on citations vs bibliography:
    - Missing bibliography entries (hallucinated citations)
    - Unused references (listed in bibliography but never cited in text)
    """
    citations = parse_citations_in_text(text)
    bib_entries = parse_bibliography_numbers(text)
    
    warnings = []
    
    # If there is no bibliography section detected, we cannot check consistency
    if not bib_entries:
        return {
            "has_bibliography": False,
            "citations_count": len(citations),
            "warnings": []
        }
        
    # 1. Hallucinated / missing bibliography entries
    missing_entries = citations - bib_entries
    for missing in missing_entries:
        warnings.append({
            "issue_type": "citation_missing_bibliography",
            "severity": "high",
            "evidence": f"[{missing}]",
            "explanation_zh": f"文献引用 [{missing}] 在文末参考文献列表中未找到，疑似格式错误或文献幻觉。",
            "explanation_ru": f"Ссылка [{missing}] приведена в тексте, но отсутствует в списке литературы.",
            "rewrite_suggestion": f"Добавьте библиографическое описание для источника [{missing}] в список литературы."
        })
        
    # 2. Unused references
    unused_entries = bib_entries - citations
    for unused in unused_entries:
        warnings.append({
            "issue_type": "citation_unused_bibliography",
            "severity": "low",
            "evidence": f"[{unused}]",
            "explanation_zh": f"参考文献列表中的条目 [{unused}] 在正文中从未被引用。",
            "explanation_ru": f"Источник [{unused}] присутствует в списке литературы, но не цитируется в тексте.",
            "rewrite_suggestion": f"Проверьте, не забыли ли вы процитировать источник [{unused}], или удалите его из списка."
        })
        
    return {
        "has_bibliography": True,
        "citations_count": len(citations),
        "bibliography_count": len(bib_entries),
        "warnings": warnings
    }
