import re
import json

def rule_based_gost_check(reference: str) -> dict:
    """
    Evaluate GOST compliance of a single reference string using rule-based heuristics.
    """
    ref = reference.strip()
    if not ref:
        return {"score": 100, "errors_zh": [], "errors_ru": [], "corrected": ""}
        
    score = 100
    errors_zh = []
    errors_ru = []
    
    # 1. Year check (4 consecutive digits, e.g., 1980-2029)
    year_match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', ref)
    if not year_match:
        score -= 25
        errors_zh.append("缺失合法的出版年份（4位数字，如2022）。")
        errors_ru.append("Отсутствует или некорректен год издания (например, 2022).")
        
    # 2. Pages check
    pages_match = re.search(r'\b([сС]\.?\s+\d+|[pP]\.?\s+\d+|\d+\s*[сС]\.?|\d+\s*[pP]\.?)', ref)
    if not pages_match:
        score -= 15
        errors_zh.append("未检测到页码信息（如 С. 10-15 或 250 с.）。")
        errors_ru.append("Не найдены страницы (например, С. 10–15 или 250 с.).")
        
    # 3. Journal Article Specific checks
    if "//" in ref:
        # Vol/Issue mark check
        vol_issue = re.search(r'\b([тТ]\.?\s*\d+|[вВыыпП\.]+\s*\d+|№\s*\d+|[vV]ol\.?\s*\d+|[nN]o\.?\s*\d+)', ref)
        if not vol_issue:
            score -= 15
            errors_zh.append("作为期刊或会议论文，缺失卷/期号（如 Т. 5, № 2 或 Vol. 5, No. 2）。")
            errors_ru.append("Для статьи в журнале/сборнике не указан том или номер (например, Т. 5, № 2).")
    else:
        # Book/Thesis specific checks
        # City separation colon check (e.g. M. : Nauka or N. Y. : Wiley)
        city_colon = re.search(r'\b([мМ]л?скв[а-я]?|[сС]Пб|[нН]овосиб[а-я]?|[мМ]\.?|[сС]Пб\.?|[кК]иев\.?|[nN]\.?\s*[yY]\.?|[lL]ondon)\s*:\s*', ref)
        if not city_colon and not any(kw in ref.lower() for kw in ["url:", "doi:", "http"]):
            score -= 10
            errors_zh.append("图书/学位论文类文献缺失出版地与出版社之间的冒号分隔符（如 М. : Наука）。")
            errors_ru.append("Для книги/диссертации отсутствует двоеточие перед издательством (например, М. : Наука).")

    # 4. URL/Online reference reference date check
    if any(kw in ref.lower() for kw in ["url:", "http", "doi:"]):
        date_match = re.search(r'([дД]ата\s+обращения|[аА]дрес\s+доступа|[аА]ктивно|[аА]ccessed)', ref)
        if not date_match:
            score -= 15
            errors_zh.append("在线文献/网络链接缺失‘引用日期/访问日期’说明（如 дата обращения: 11.06.2026）。")
            errors_ru.append("Для электронного ресурса отсутствует дата обращения (например, дата обращения: 11.06.2026).")

    # 5. Consecutive spacing error
    if "  " in ref:
        score -= 5
        errors_zh.append("包含多余的连续空格。")
        errors_ru.append("Присутствуют лишние двойные пробелы.")
        
    score = max(40, score)
    
    # Generate a dummy correction suggestions using standard formatting rules
    corrected = ref
    # Simple search and replace for common double spaces
    corrected = re.sub(r'\s+', ' ', corrected)
    # Ensure dashes are long dashes or spaced properly
    corrected = corrected.replace(" - ", " – ")
    
    return {
        "score": score,
        "errors_zh": errors_zh,
        "errors_ru": errors_ru,
        "corrected": corrected
    }

async def check_gost_compliance(
    reference: str,
    engine_type: str = "local",
    api_key: str = "",
    base_url: str = "",
    llm = None
) -> dict:
    """
    Perform GOST compliance check on a single reference.
    Uses LLM (local or cloud) if available, otherwise falls back to rule-based checking.
    """
    use_llm = False
    if llm is not None:
        use_llm = True
    elif engine_type in ("deepseek-v4-pro", "deepseek-v4-flash") and api_key:
        use_llm = True
        
    if not use_llm:
        return rule_based_gost_check(reference)
        
    sys_prompt = """You are a Russian academic publication auditor specializing in bibliography validation against GOST Р 7.0.5-2008 and GOST Р 7.0.100-2018.
Your task is to analyze the following bibliography reference and check if it follows GOST rules (especially correct slashes, dashes, spacing, colons, and required elements like author, title, publisher, year, pages).

Reference:
"{reference}"

Rate the compliance of this reference on a scale from 0 to 100.
Identify any formatting errors, punctuation errors, or missing metadata.
Provide a corrected version conforming to GOST.

You MUST reply strictly in JSON format (no markdown blocks, no think tag in output, just raw JSON) as:
{
  "score": 90,
  "errors_zh": ["Punctuation/Formatting error description in Chinese"],
  "errors_ru": ["Error description in Russian"],
  "corrected": "Corrected reference string conforming to GOST"
}"""

    user_prompt = f"Reference string:\n{reference}"
    
    try:
        raw_text = ""
        if engine_type in ("deepseek-v4-pro", "deepseek-v4-flash"):
            from naturalization_layer.llm_judge import StyleJudge
            judge = StyleJudge(None)
            raw_text = judge._call_deepseek_api(engine_type, api_key, base_url, sys_prompt, user_prompt)
            if raw_text.strip().startswith("```"):
                _, raw_text = judge._clean_json_text(raw_text)
        else:
            prompt = f"<|im_start|>system\n{sys_prompt}\nIMPORTANT: You MUST write your reasoning inside <think>...</think> tags strictly in Chinese (中文/zh-CN). Keep reasoning concise. Write the final JSON object clearly.\n<|im_end|>\n<|im_start|>user\n{user_prompt}\n<|im_end|>\n<|im_start|>assistant\n<think>\n"
            response = llm(prompt, max_tokens=1024, stop=["<|im_end|>"])
            raw_text = response["choices"][0]["text"].strip()
            
            from naturalization_layer.llm_judge import StyleJudge
            judge = StyleJudge(None)
            _, raw_text = judge._clean_json_text(raw_text)
            
        from naturalization_layer.llm_judge import repair_json_string
        repaired = repair_json_string(raw_text)
        res = json.loads(repaired)
        
        return {
            "score": int(res.get("score", 90)),
            "errors_zh": res.get("errors_zh", []),
            "errors_ru": res.get("errors_ru", []),
            "corrected": res.get("corrected", reference)
        }
    except Exception as e:
        print(f"GOST LLM verification failed: {e}. Falling back to rules.")
        
    return rule_based_gost_check(reference)
