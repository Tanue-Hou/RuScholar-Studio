from llama_cpp import Llama
import json

class StyleJudge:
    def __init__(self, llm_instance: Llama):
        self.llm = llm_instance
        
    def diagnose_sentence(self, sentence: str, stats: dict = None, ppl: float = None) -> dict:
        if stats is None:
            stats = {}
            
        stats_str = f"""- Отношение существительных к глаголам (N/V Ratio): {stats.get('nv_ratio', 'N/A')}
- Количество пассивных оборотов: {stats.get('passive_count', 0)}
- Цепочки существительных в родительном падеже (Genitive Chains): {stats.get('genitive_chains', [])}
- Найденные клише/шаблоны: {stats.get('cliches_found', [])}
- Найденные академические связки: {stats.get('connectors_found', [])}
- Значение perplexity (PPL) предложения: {f'{ppl:.2f}' if ppl is not None else 'N/A'}"""

        prompt = f"""<|im_start|>system
Ты — эксперт по академическому русскому языку и научной редактуре.
Оцени предоставленное предложение на наличие стилистических дефектов, машинного перевода (Translationese) или признаков генерации искусственным интеллектом (AI-generated suspicion).

Тебе предоставляются результаты предварительного лингвистического анализа и статистические показатели (Track A и Track B):
{stats_str}

Правила оценки:
1. Если PPL подозрительно низкий (< 10.0), предложение перегружено штампами (клише) и имеет высокий N/V Ratio, классифицируй как "ai_generated_suspicion" с высокой строгостью (severity = high).
2. Если в предложении много пассивных глаголов на "-ся" или нагромождение родительного падежа, классифицируй как "machine_translation_cliche" или "style_heavy".
3. Обязательно укажи конкретную фразу-доказательство (evidence) и объясни причину на русском и китайском языках.
4. Предложи зрелый академический вариант переписывания (rewrite_suggestion).
5. Если предложение естественное и не требует правок, верни пустой список "issues": [].

Ответь СТРОГО в формате JSON:
{{
  "issues": [
    {{
      "issue_type": "ai_generated_suspicion", 
      "severity": "high", 
      "evidence": "конкретная подстрока", 
      "explanation_zh": "объяснение на китайском", 
      "explanation_ru": "объяснение на русском", 
      "rewrite_suggestion": "академический вариант"
    }}
  ],
  "safe_to_rewrite": true
}}
<|im_end|>
<|im_start|>user
Предложение: {sentence}
<|im_end|>
<|im_start|>assistant
"""
        response = self.llm(prompt, max_tokens=384, stop=["<|im_end|>"])
        raw_text = response["choices"][0]["text"].strip()
        cleaned_text = self._clean_json_text(raw_text)
        try:
            return json.loads(cleaned_text)
        except Exception as e:
            return {
                "issues": [],
                "error": f"Failed to parse JSON: {str(e)}",
                "raw": raw_text,
                "safe_to_rewrite": False
            }
            
    def _clean_json_text(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text
