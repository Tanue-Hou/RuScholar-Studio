from llama_cpp import Llama
import json

class StyleJudge:
    def __init__(self, llm_instance: Llama):
        self.llm = llm_instance
        
    def detect_discipline(self, text_snippet: str, engine_type: str = "local", api_key: str = "", base_url: str = "") -> str:
        # Map input engine type to API model names if needed
        api_engine = engine_type
        if "pro" in engine_type:
            api_engine = "deepseek-v4-pro"
        elif "flash" in engine_type:
            api_engine = "deepseek-v4-flash"

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
        
        raw_text = ""
        try:
            if api_engine in ("deepseek-v4-pro", "deepseek-v4-flash"):
                raw_text = self._call_deepseek_api(api_engine, api_key, base_url, sys_prompt, user_prompt)
            else:
                prompt = f"<|im_start|>system\n{sys_prompt}\nIMPORTANT: You MUST write your reasoning inside <think>...</think> tags strictly in Chinese (中文/zh-CN). The reasoning can be detailed. Write the final JSON object clearly.\n<|im_end|>\n<|im_start|>user\n{user_prompt}\n<|im_end|>\n<|im_start|>assistant\n"
                response = self.llm(prompt, max_tokens=1024, stop=["<|im_end|>"])
                raw_text = response["choices"][0]["text"].strip()
                
            _, cleaned_text = self._clean_json_text(raw_text)
            res = json.loads(cleaned_text)
            discipline = res.get("discipline", "UNIVERSAL").upper()
            if discipline in ("SCI_TECH", "AUTOMATION_CONTROL", "AGRI_MED", "HUM_POL_ECON", "ARTS_SPORTS"):
                return discipline
        except Exception as e:
            print(f"Model discipline detection failed or returned invalid result: {e}. Falling back to keywords.")
            
        # Fallback based on simple keyword search (supports both Russian and English)
        text_lower = text_snippet.lower()
        if any(w in text_lower for w in ["управление", "робот", "автоматиз", "регулятор", "динамик", "control", "robot", "automat", "cybernetic", "feedback"]):
            return "AUTOMATION_CONTROL"
        if any(w in text_lower for w in ["биолог", "медиц", "клетк", "терап", "ген", "biolog", "medic", "cell", "gene", "patient", "clinical", "dna", "rna"]):
            return "AGRI_MED"
        if any(w in text_lower for w in ["физик", "хими", "сплав", "материал", "энерг", "physic", "chemic", "material", "alloy", "thermodynamic", "mechanic"]):
            return "SCI_TECH"
        if any(w in text_lower for w in ["эконом", "полити", "гуманитар", "истори", "обществ", "econom", "polit", "social", "humanit", "history", "societ"]):
            return "HUM_POL_ECON"
        if any(w in text_lower for w in ["искусств", "спорт", "культур", "музык", "art", "sport", "cultur", "music", "athlet", "paint"]):
            return "ARTS_SPORTS"
            
        return "UNIVERSAL"

    def diagnose_sentence(self, sentence: str, stats: dict = None, ppl: float = None, context_before: list = None, context_after: list = None, skill_rules: dict = None, engine_type: str = "local", api_key: str = "", base_url: str = "") -> dict:
        if stats is None:
            stats = {}
        if context_before is None: context_before = []
        if context_after is None: context_after = []
            
        trans_warns_str = stats.get("trans_warnings", [])
        trans_warns_bullet = "\n".join([f"  * {w}" for w in trans_warns_str]) if trans_warns_str else "  * [Нет]"
        
        stats_str = f"""- Отношение существительных к глаголам (N/V Ratio): {stats.get('nv_ratio', 'N/A')}
- Количество пассивных оборотов: {stats.get('passive_count', 0)}
- Цепочки существительных в родительном падеже (Genitive Chains): {stats.get('genitive_chains', [])}
- Найденные клише/шаблоны: {stats.get('cliches_found', [])}
- Найденные академические связки: {stats.get('connectors_found', [])}
- Предупреждения о машинном переводе (Translationese Warnings):
{trans_warns_bullet}
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
3. Обязательно укажи конкретную фразу-доказательство (evidence) и объясни причину на русском (explanation_ru) и китайском (explanation_zh) языках. В объяснении обязательно явно сошлись на соответствующее правило (или нарушение правила) из предоставленной базы ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА РЕДАКТУРЫ (PhD Thesis Butler) или лингвистический критерий (например, отношение существительных к глаголам, пассивный залог), если оно применимо к данной ошибке. Объяснение на китайском языке (explanation_zh) должно быть ясным, подробным и информативным.
4. Предложи зрелый академический вариант переписывания (rewrite_suggestion). При переписывании обязательно опирайся на ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА РЕДАКТУРЫ, лингвистические предупреждения и Контекст!
6. В ключе "estimated_perplexity" обязательно укажи численную оценку perplexity предложения (дробное число от 5.0 до 150.0): от 10.0 до 15.0 для гладкого/шаблонного/подозреваемого в ИИ-генерации текста; от 30.0 до 50.0 для естественного академического текста человека; более 80.0 для тяжелого/перегруженного перевода.
7. ВНИМАНИЕ: ОБЯЗАТЕЛЬНО пиши все свои размышления внутри тега <think> (если ты используешь или поддерживаешь его) исключительно на китайском языке (中文/zh-CN). Ни в коем случае не пиши размышления на русском или английском языках. Размышления могут быть подробными. Итоговое объяснение в JSON (explanation_zh) должно быть ясным и информативным.

Ответь СТРОГО в формате JSON:
{{
  "estimated_perplexity": 24.5,
  "issues": [
    {{
      "issue_type": "ai_generated_suspicion", 
      "severity": "high", 
      "evidence": "конкретная подстрока", 
      "explanation_zh": "объяснение на китайском с указанием правила PhD Thesis Butler", 
      "explanation_ru": "объяснение на русском с указанием правила PhD Thesis Butler", 
      "rewrite_suggestion": "академический вариант, учитывающий контекст и правила"
    }}
  ],
  "safe_to_rewrite": true
}}"""

        # Dispatch to appropriate engine
        try:
            if engine_type in ("deepseek-v4-pro", "deepseek-v4-flash"):
                raw_text = self._call_deepseek_api(engine_type, api_key, base_url, sys_prompt, context_str)
            else:
                # Fallback to local
                prompt = f"<|im_start|>system\n{sys_prompt}\nIMPORTANT: You MUST write your reasoning inside <think>...</think> tags strictly in Chinese (中文/zh-CN). Keep your reasoning extremely concise (under 200 words) and focused. Write the final explanation_zh inside the JSON object clearly and informatively.\n<|im_end|>\n<|im_start|>user\n{context_str}\n<|im_end|>\n<|im_start|>assistant\n"
                response = self.llm(prompt, max_tokens=1024, stop=["<|im_end|>"])
                raw_text = response["choices"][0]["text"].strip()
        except Exception as api_err:
            if engine_type == "local":
                explanation_zh = f"由于本地模型推理异常（详情: {str(api_err)}），未能成功获取该句的学术写作风格透视。请稍后再试或切换到云端模型。"
                explanation_ru = f"Ошибка локальной модели ({str(api_err)}). Не удалось выполнить диагностику."
                think_msg = "【本地模型推理异常】由于本地 Llama 引擎运行出错或内存不足，未能完成句子的深度诊断。建议检查后台服务、重新加载模型，或尝试使用云端接口。"
            else:
                explanation_zh = f"由于云端服务连接异常或超频限制（详情: {str(api_err)}），未能成功获取该句的学术写作风格透视。请稍后再试或切换到本地模型。"
                explanation_ru = f"Ошибка подключения к API или превышение лимитов ({str(api_err)}). Не удалось выполнить диагностику."
                think_msg = "【云端 API 响应异常】由于网络连接超时、API 服务暂时受限或请求频率过高，无法获取大模型的实时推理过程。建议检查网络连接、API 密钥可用性，或在本地模式下运行。"
                
            return {
                "issues": [{
                    "issue_type": "api_request_error",
                    "severity": "high",
                    "evidence": "API Connection Failed",
                    "explanation_zh": explanation_zh,
                    "explanation_ru": explanation_ru,
                    "rewrite_suggestion": "-"
                }],
                "think": think_msg,
                "error": f"API request failed: {str(api_err)}",
                "raw": f"API Error: {str(api_err)}",
                "safe_to_rewrite": False
            }
        
        think_content, cleaned_text = self._clean_json_text(raw_text)
        
        parsed_success = False
        res = {}
        parse_err = None
        
        try:
            res = json.loads(cleaned_text)
            parsed_success = True
        except Exception as json_err:
            parse_err = json_err
            # Try ast.literal_eval for single-quoted Python dict style formats
            try:
                import ast
                res = ast.literal_eval(cleaned_text)
                parsed_success = True
            except Exception as ast_err:
                parse_err = ast_err
                # Attempt to repair unclosed braces/brackets (common on token limit cuts)
                try:
                    import ast
                    repaired_text = cleaned_text.strip()
                    open_braces = repaired_text.count("{") - repaired_text.count("}")
                    open_brackets = repaired_text.count("[") - repaired_text.count("]")
                    if open_brackets > 0:
                        repaired_text += "]" * open_brackets
                    if open_braces > 0:
                        repaired_text += "}" * open_braces
                    res = ast.literal_eval(repaired_text)
                    parsed_success = True
                except Exception:
                    pass

        if parsed_success:
            res["think"] = think_content
            if "estimated_perplexity" in res:
                try:
                    res["estimated_perplexity"] = float(res["estimated_perplexity"])
                except:
                    res["estimated_perplexity"] = None
            else:
                res["estimated_perplexity"] = None
            return res
            
        friendly_think = think_content if think_content else "【模型输出解析失败】模型未返回可识别的思维链，或者输出格式损坏。"
        return {
            "issues": [{
                "issue_type": "json_parse_error",
                "severity": "high",
                "evidence": "LLM Format Defect",
                "explanation_zh": f"模型返回的学术写作风格诊断格式损坏，无法解析（原始输出摘要：{cleaned_text[:100]}...）。该句已被安全放行，请继续阅读其他句子。",
                "explanation_ru": "Формат ответа модели поврежден и не может быть обработан.",
                "rewrite_suggestion": "-"
            }],
            "think": friendly_think,
            "error": f"Failed to parse JSON: {str(parse_err)}",
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
            # Raise the exception directly so the caller can handle API errors properly
            raise e
            
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
