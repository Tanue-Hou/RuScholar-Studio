import os
import json
import re
from naturalization_layer.russian_lemmatizer import lemmatize_sentence

def load_vak_nomenclature() -> list[dict]:
    """
    Load the VAK nomenclature JSON database.
    """
    # Try various relative locations to be robust
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules", "vak_passports_nomenclature.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "naturalization_layer", "rules", "vak_passports_nomenclature.json"),
        "/Users/tanue/Documents/antigravity/friendly-lavoisier/naturalization_layer/rules/vak_passports_nomenclature.json"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError("Could not locate vak_passports_nomenclature.json database.")

def keyword_map_vak_specialty(topic: str, abstract: str = "", keywords: str = "") -> dict:
    """
    Fallback rule-based classification using Russian lemmatization and word overlap.
    """
    nomenclature = load_vak_nomenclature()
    
    # 1. Lemmatize and clean input words
    combined_input = f"{topic} {abstract} {keywords}".lower()
    input_lemmas_str = lemmatize_sentence(combined_input)
    # Extract words of length > 2
    input_lemmas = set(w for w in re.findall(r'[а-яА-ЯёЁa-zA-Z0-9]+', input_lemmas_str) if len(w) > 2)
    
    best_code = None
    best_score = -9999
    best_specialty = None
    
    for spec in nomenclature:
        # 2. Lemmatize positive description
        pos_text = f"{spec['name_ru']} {spec['passport_summary']}".lower()
        pos_lemmas_str = lemmatize_sentence(pos_text)
        pos_lemmas = set(w for w in re.findall(r'[а-яА-ЯёЁa-zA-Z0-9]+', pos_lemmas_str) if len(w) > 2)
        
        # 3. Lemmatize negative (out of scope) description
        neg_text = " ".join(spec.get("out_of_scope", [])).lower()
        neg_lemmas_str = lemmatize_sentence(neg_text)
        neg_lemmas = set(w for w in re.findall(r'[а-яА-ЯёЁa-zA-Z0-9]+', neg_lemmas_str) if len(w) > 2)
        # Prevent false negative penalty for words that are part of the positive definition
        neg_lemmas = neg_lemmas - pos_lemmas
        
        # 4. Calculate score
        pos_intersection = input_lemmas.intersection(pos_lemmas)
        neg_intersection = input_lemmas.intersection(neg_lemmas)
        
        # Score calculation: weight positives higher, penalize negatives heavily
        score = len(pos_intersection) - 2 * len(neg_intersection)
        
        if score > best_score:
            best_score = score
            best_code = spec["code"]
            best_specialty = spec

    # Default fallback to the first one (2.3.1) if no matches found
    if best_specialty is None or best_score <= 0:
        best_specialty = nomenclature[0]
        best_code = best_specialty["code"]
        best_score = 0
        
    return {
        "code": best_code,
        "confidence": min(0.9, 0.3 + (best_score * 0.1)),
        "reasoning_zh": f"由于模型不可用，系统启动了基于俄语词形还原的分词相似度匹配机制。在输入特征中，发现了与 {best_specialty['name_zh']} ({best_code}) 专业的高度词汇重合度，故将其推荐为目标专业。",
        "reasoning_ru": f"Ввиду недоступности модели была активирована эвристическая классификация на основе лемматизации слов. Выбран код {best_code} ({best_specialty['name_ru']}) из-за наибольшего пересечения терминов."
    }

async def map_vak_specialty(
    topic: str,
    abstract: str = "",
    keywords: str = "",
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = "",
    llm = None
) -> dict:
    """
    Determine the matching VAK specialty code for a dissertation.
    Uses LLM (local or cloud) if available, otherwise falls back to keyword-based matching.
    """
    nomenclature = load_vak_nomenclature()
    
    use_llm = False
    if llm is not None:
        use_llm = True
    elif engine_type in ("deepseek-v4-pro", "deepseek-v4-flash") and api_key:
        use_llm = True
        
    if not use_llm:
        return keyword_map_vak_specialty(topic, abstract, keywords)
        
    # Build prompt for LLM classification
    sys_prompt = """You are an expert academic advisor specialized in the Russian Higher Attestation Commission (ВАК) nomenclature of scientific specialties.
Your task is to classify a PhD dissertation topic/abstract/keywords into one of the following VAK specialty codes.

Available VAK Specialty Codes:
"""
    for spec in nomenclature:
        sys_prompt += f"- Code: {spec['code']}\n  Name (RU): {spec['name_ru']}\n  Name (ZH): {spec['name_zh']}\n  Passport Summary: {spec['passport_summary']}\n"
        if spec.get("out_of_scope"):
            sys_prompt += "  Out of Scope (Что не входит в паспорт специальности):\n"
            for o in spec["out_of_scope"]:
                sys_prompt += f"    * {o}\n"
        sys_prompt += "\n"

    sys_prompt += """
Analyze the details of the dissertation and find the closest matching VAK specialty code. Pay special attention to the "out_of_scope" fields (что не входит в паспорт специальности) to avoid misclassification (academic derailment/出轨).

You MUST reply strictly in JSON format (no markdown blocks, no think tag in output, just raw JSON) as:
{
  "code": "e.g., 2.3.1",
  "confidence": 0.0 to 1.0,
  "reasoning_zh": "Why this code was selected and why other similar codes were rejected, in Chinese.",
  "reasoning_ru": "The same reasoning, in Russian."
}"""

    user_prompt = f"Dissertation Details:\n- Topic: {topic}\n- Abstract: {abstract}\n- Keywords: {keywords}"
    
    try:
        raw_text = ""
        if engine_type in ("deepseek-v4-pro", "deepseek-v4-flash"):
            from naturalization_layer.llm_judge import StyleJudge
            judge = StyleJudge(None)
            raw_text = judge._call_deepseek_api(engine_type, api_key, base_url, sys_prompt, user_prompt)
            # Remove any markdown wrapping
            if raw_text.strip().startswith("```"):
                _, raw_text = judge._clean_json_text(raw_text)
        else:
            # Local Llama model
            prompt = f"<|im_start|>system\n{sys_prompt}\nIMPORTANT: You MUST write your reasoning inside <think>...</think> tags strictly in Chinese (中文/zh-CN). Keep reasoning concise. Write the final JSON object clearly.\n<|im_end|>\n<|im_start|>user\n{user_prompt}\n<|im_end|>\n<|im_start|>assistant\n<think>\n"
            response = llm(prompt, max_tokens=1024, stop=["<|im_end|>"])
            raw_text = response["choices"][0]["text"].strip()
            
            from naturalization_layer.llm_judge import StyleJudge
            judge = StyleJudge(None)
            _, raw_text = judge._clean_json_text(raw_text)
            
        from naturalization_layer.llm_judge import repair_json_string
        repaired = repair_json_string(raw_text)
        res = json.loads(repaired)
        
        # Verify the returned code is valid
        matched_code = res.get("code")
        valid_codes = [s["code"] for s in nomenclature]
        if matched_code in valid_codes:
            return {
                "code": matched_code,
                "confidence": float(res.get("confidence", 0.8)),
                "reasoning_zh": res.get("reasoning_zh", "未提供中文解释。"),
                "reasoning_ru": res.get("reasoning_ru", "Нет объяснения.")
            }
    except Exception as e:
        print(f"VAK specialty classification failed: {e}. Falling back to keywords.")
        
    return keyword_map_vak_specialty(topic, abstract, keywords)
