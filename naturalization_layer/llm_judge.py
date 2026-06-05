from llama_cpp import Llama
import json

class StyleJudge:
    def __init__(self, llm_instance: Llama):
        self.llm = llm_instance
        
    def diagnose_sentence(self, sentence: str) -> dict:
        prompt = f"""<|im_start|>system
Ты — эксперт по академическому русскому языку. Оцени предложение на наличие машинного перевода или шаблонных ИИ-фраз.
Ответь строго в формате JSON:
{{"has_ai_cliche": bool, "syntax_unnatural": bool, "rewrite_suggestion": "строка"}}
<|im_end|>
<|im_start|>user
Предложение: {sentence}
<|im_end|>
<|im_start|>assistant
"""
        response = self.llm(prompt, max_tokens=256, stop=["<|im_end|>"])
        try:
            return json.loads(response["choices"][0]["text"].strip())
        except:
            return {"error": "Failed to parse JSON", "raw": response["choices"][0]["text"]}
