from llama_cpp import Llama
import json

class StyleJudge:
    def __init__(self, llm_instance: Llama):
        self.llm = llm_instance
        
    def detect_discipline(self, text_snippet: str, engine_type: str = "local", api_key: str = "", base_url: str = "") -> str:
        sys_prompt = """You are an academic classifier. Your task is to analyze the provided text snippet from a research paper or thesis and classify it into exactly one of the following academic discipline clusters:
- SCI_TECH (Physical sciences, engineering, chemistry, physics, excluding automation)
- AUTOMATION_CONTROL (Automation, control theory, robotics, systems engineering, cybernetics)
- AGRI_MED (Agriculture, biology, medicine, life sciences)
- HUM_POL_ECON (Humanities, political science, economics, social sciences)
- ARTS_SPORTS (Arts, sports, culture, music)
- UNIVERSAL (General academic introduction, multidisciplinary, or if unclear)

You must return a JSON object containing exactly one key "discipline" with the category name:
{"discipline": "CLUSTER_NAME"}"""

        user_prompt = f"Text snippet (first 1000 chars):\n{text_snippet[:1000]}"
        
        if engine_type in ("deepseek-v4-pro", "deepseek-v4-flash"):
            raw_text = self._call_deepseek_api(engine_type, api_key, base_url, sys_prompt, user_prompt)
        else:
            prompt = f"<|im_start|>system\n{sys_prompt}\n<|im_end|>\n<|im_start|>user\n{user_prompt}\n<|im_end|>\n<|im_start|>assistant\n"
            response = self.llm(prompt, max_tokens=128, stop=["<|im_end|>"])
            raw_text = response["choices"][0]["text"].strip()
            
        _, cleaned_text = self._clean_json_text(raw_text)
        try:
            res = json.loads(cleaned_text)
            discipline = res.get("discipline", "UNIVERSAL").upper()
            if discipline in ("SCI_TECH", "AUTOMATION_CONTROL", "AGRI_MED", "HUM_POL_ECON", "ARTS_SPORTS", "UNIVERSAL"):
                return discipline
            return "UNIVERSAL"
        except:
            # Fallback based on simple keyword search if LLM fails or returns garbage
            text_lower = text_snippet.lower()
            if any(w in text_lower for w in ["управление", "робот", "автоматиз", "регулятор", "динамик"]):
                return "AUTOMATION_CONTROL"
            if any(w in text_lower for w in ["биолог", "медиц", "клетк", "терап", "ген"]):
                return "AGRI_MED"
            if any(w in text_lower for w in ["физик", "хими", "сплав", "материал", "энерг"]):
                return "SCI_TECH"
            if any(w in text_lower for w in ["эконом", "полити", "гуманитар", "истори", "обществ"]):
                return "HUM_POL_ECON"
            return "UNIVERSAL"

    def diagnose_sentence(self, sentence: str, stats: dict = None, ppl: float = None, context_before: list = None, context_after: list = None, skill_rules: dict = None, engine_type: str = "local", api_key: str = "", base_url: str = "") -> dict:
        if stats is None:
            stats = {}
        if context_before is None: context_before = []
        if context_after is None: context_after = []
            
        stats_str = f"""- Отношение существительных к глаголам (N/V Ratio): {stats.get('nv_ratio', 'N/A')}
- Количество пассивных оборотов: {stats.get('passive_count', 0)}
- Цепочки существительных в родительном падеже (Genitive Chains): {stats.get('genitive_chains', [])}
- Найденные клише/шаблоны: {stats.get('cliches_found', [])}
- Найденные академические связки: {stats.get('connectors_found', [])}
- Значение perplexity (PPL) предложения: {f'{ppl:.2f}' if ppl is not None else 'N/A'}"""

        ctx_b = " ".join(context_before)
        ctx_a = " ".join(context_after)
        context_str = f"""Контекст до: {ctx_b if ctx_b else "[Нет]"}
Целевое предложение: {sentence}
Контекст после: {ctx_a if ctx_a else "[Нет]"}"""

        skill_str = ""
        if skill_rules:
            do_rules = "\\n".join([f"- {r}" for r in skill_rules.get("do_rules", [])])
            dont_rules = "\\n".join([f"- {r}" for r in skill_rules.get("dont_rules", [])])
            skill_str = f"""\nОБЯЗАТЕЛЬНЫЕ ПРАВИЛА РЕДАКТУРЫ (Из базы PhD Thesis Butler):
Что нужно делать (Do):
{do_rules}
Что ЗАПРЕЩЕНО делать (Don't):
{dont_rules}\n"""

        sys_prompt = f"""Ты — эксперт по академическому русскому языку и научной редактуре.
Оцени предоставленное Целевое Предложение на наличие стилистических дефектов, машинного перевода (Translationese) или признаков генерации ИИ.
Всегда учитывай контекст (предложения до и после), чтобы твои варианты переписывания (rewrite_suggestion) органично вписывались в абзац, не ломали логику и сохраняли связность.

Тебе предоставляются результаты предварительного лингвистического анализа и статистические показатели (Track A и Track B):
{stats_str}
{skill_str}
Правила оценки:
1. ВНИМАНИЕ: Низкий PPL (< 15.0) указывает на повышенную предсказуемость текста (Predictability Risk). Это сигнал возможной шаблонности или машинного письма. Пожалуйста, проанализируй, является ли стиль естественным для научной статьи, и предложи улучшения, если ритм слишком монотонный. Не делай поспешных выводов о 100% авторе-роботе только по одному этому признаку.
2. Высокий PPL (> 80.0) указывает на неестественность, плохой перевод или грамматическую перегруженность. Если также много пассивного залога или нагромождение родительного падежа, классифицируй как "machine_translation_cliche" или "style_heavy".
3. Обязательно укажи конкретную фразу-доказательство (evidence) и объясни причину на русском и китайском языках.
4. Предложи зрелый академический вариант переписывания (rewrite_suggestion). При переписывании опирайся на ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА РЕДАКТУРЫ и Контекст!
5. Если предложение действительно естественное и живое, верни пустой список "issues": [].

Ответь СТРОГО в формате JSON:
{{
  "issues": [
    {{
      "issue_type": "ai_generated_suspicion", 
      "severity": "high", 
      "evidence": "конкретная подстрока", 
      "explanation_zh": "объяснение на китайском", 
      "explanation_ru": "объяснение на русском", 
      "rewrite_suggestion": "академический вариант, учитывающий контекст"
    }}
  ],
  "safe_to_rewrite": true
}}"""

        # Dispatch to appropriate engine
        if engine_type in ("deepseek-v4-pro", "deepseek-v4-flash"):
            raw_text = self._call_deepseek_api(engine_type, api_key, base_url, sys_prompt, context_str)
        else:
            # Fallback to local
            prompt = f"<|im_start|>system\n{sys_prompt}\n<|im_end|>\n<|im_start|>user\n{context_str}\n<|im_end|>\n<|im_start|>assistant\n"
            response = self.llm(prompt, max_tokens=1024, stop=["<|im_end|>"])
            raw_text = response["choices"][0]["text"].strip()
        
        think_content, cleaned_text = self._clean_json_text(raw_text)
        
        try:
            res = json.loads(cleaned_text)
            res["think"] = think_content
            return res
        except Exception as e:
            return {
                "issues": [{
                    "issue_type": "json_parse_error",
                    "severity": "high",
                    "evidence": "LLM Output Error",
                    "explanation_zh": f"模型返回的格式损坏，无法解析。原始输出摘要：{cleaned_text[:100]}...",
                    "explanation_ru": "Ошибка парсинга JSON",
                    "rewrite_suggestion": "N/A"
                }],
                "think": think_content,
                "error": f"Failed to parse JSON: {str(e)}",
                "raw": raw_text,
                "safe_to_rewrite": False
            }
            
    def _call_deepseek_api(self, model: str, api_key: str, base_url: str, sys_prompt: str, user_prompt: str) -> str:
        import urllib.request
        import urllib.error
        
        if not base_url:
            base_url = "https://api.deepseek.com/v1"
            
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                content = res_json["choices"][0]["message"].get("content", "")
                reasoning = res_json["choices"][0]["message"].get("reasoning_content", "")
                if reasoning:
                    return f"<think>{reasoning}</think>\n{content}"
                return content
        except Exception as e:
            # Inject the error as raw text so it gets caught by json parse error
            return f"<think>API Call Failed</think>\nAPI Error: {str(e)}"
            
    def _clean_json_text(self, text: str) -> tuple[str, str]:
        text = text.strip()
        think_content = ""
        import re
        
        # Extract <think> content if present
        think_match = re.search(r'<think>(.*?)</think>', text, flags=re.DOTALL)
        if think_match:
            think_content = think_match.group(1).strip()
            text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        else:
            # Maybe it didn't close the think tag?
            if text.startswith("<think>"):
                parts = text.split("</think>")
                if len(parts) == 1:
                    # Unclosed think tag
                    think_content = text[7:].strip()
                    text = "{}" # Return empty JSON to trigger parse error or empty issues
                else:
                    think_content = parts[0][7:].strip()
                    text = parts[1].strip()

        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            
        # Sometimes Qwen prefixes with "Вот JSON:"
        json_start = text.find("{")
        json_end = text.rfind("}")
        if json_start != -1 and json_end != -1 and json_end > json_start:
            text = text[json_start:json_end+1]
            
        return think_content, text
