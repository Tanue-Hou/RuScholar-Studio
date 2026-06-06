from llama_cpp import Llama
import json

class StyleJudge:
    def __init__(self, llm_instance: Llama):
        self.llm = llm_instance
        
    def diagnose_sentence(self, sentence: str, stats: dict = None, ppl: float = None, context_before: list = None, context_after: list = None, skill_rules: dict = None) -> dict:
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

        # Build context block
        ctx_b = " ".join(context_before)
        ctx_a = " ".join(context_after)
        context_str = f"""Контекст до: {ctx_b if ctx_b else "[Нет]"}
Целевое предложение: {sentence}
Контекст после: {ctx_a if ctx_a else "[Нет]"}"""

        # Build skill rules block
        skill_str = ""
        if skill_rules:
            do_rules = "\\n".join([f"- {r}" for r in skill_rules.get("do_rules", [])])
            dont_rules = "\\n".join([f"- {r}" for r in skill_rules.get("dont_rules", [])])
            skill_str = f"""\nОБЯЗАТЕЛЬНЫЕ ПРАВИЛА РЕДАКТУРЫ (Из базы PhD Thesis Butler):
Что нужно делать (Do):
{do_rules}
Что ЗАПРЕЩЕНО делать (Don't):
{dont_rules}\n"""

        prompt = f"""<|im_start|>system
Ты — эксперт по академическому русскому языку и научной редактуре.
Оцени предоставленное Целевое Предложение на наличие стилистических дефектов, машинного перевода (Translationese) или признаков генерации ИИ.
Всегда учитывай контекст (предложения до и после), чтобы твои варианты переписывания (rewrite_suggestion) органично вписывались в абзац, не ломали логику и сохраняли связность.

Тебе предоставляются результаты предварительного лингвистического анализа и статистические показатели (Track A и Track B):
{stats_str}
{skill_str}
Правила оценки:
1. ВНИМАНИЕ: Низкий PPL (< 15.0) — это абсолютный математический признак машинной генерации (AI-generated). Если переданный тебе PPL < 15.0, ты ОБЯЗАН классифицировать это предложение как "ai_generated_suspicion" (severity = high), даже если в нем нет других клише.
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
}}
<|im_end|>
<|im_start|>user
{context_str}
<|im_end|>
<|im_start|>assistant
"""
        response = self.llm(prompt, max_tokens=1024, stop=["<|im_end|>"])
        raw_text = response["choices"][0]["text"].strip()
        
        think_content, cleaned_text = self._clean_json_text(raw_text)
        
        try:
            res = json.loads(cleaned_text)
            res["think"] = think_content
            return res
        except Exception as e:
            # Fallback to returning the error as a flagged issue so it shows up in UI
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
