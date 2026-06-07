from llama_cpp import Llama
import json
import urllib.request
import re

class NLICitationJudge:
    def __init__(self, llm_instance: Llama):
        self.llm = llm_instance

    def verify_citation(self, sentence: str, snippets: list[str], engine_type: str = "local", api_key: str = "", base_url: str = "") -> dict:
        """
        Verify if the sentence is logically supported by the snippets.
        Returns a dict:
          {
            "status": "SUPPORTED" | "CONTRADICTED" | "NOT_ENOUGH_INFO",
            "explanation_zh": "Chinese logic review explanation",
            "evidence_snippet": "Snippet quote"
          }
        """
        if not snippets:
            return {
                "status": "NOT_ENOUGH_INFO",
                "explanation_zh": "文献引用审计：未检索到相关文献片段，无法进行真实性支撑核验。",
                "evidence_snippet": ""
            }

        api_engine = engine_type
        if "pro" in engine_type:
            api_engine = "deepseek-v4-pro"
        elif "flash" in engine_type:
            api_engine = "deepseek-v4-flash"

        sys_prompt = """You are an academic citation auditor. Your task is to verify if a given claim (sentence) from a research paper is logically supported by the provided snippets retrieved from the cited reference.
You must classify the relationship into exactly one of three categories:
- SUPPORTED: The snippets contain direct logical proof or strongly imply the truth of the claim.
- CONTRADICTED: The snippets directly contradict or refute the claim (e.g., claim says 'A increases B' but snippet says 'A decreases B' or 'A does not affect B').
- NOT_ENOUGH_INFO: The snippets do not contain enough information to prove or disprove the claim, or talk about an unrelated topic (weak or irrelevant citation).

You must return a JSON object containing exactly the following keys:
{
  "status": "SUPPORTED" | "CONTRADICTED" | "NOT_ENOUGH_INFO",
  "explanation_zh": "A short, concise Chinese explanation of the logical alignment or mismatch.",
  "evidence_snippet": "The most relevant short quote/snippet from the provided reference text that supports your judgment. If NOT_ENOUGH_INFO, this can be empty."
}"""

        snippets_str = "\n".join([f"- Snippet {i+1}: {s}" for i, s in enumerate(snippets)])
        user_prompt = f"""Claim (sentence in draft):
"{sentence}"

Retrieved Reference Snippets:
{snippets_str}"""

        raw_text = ""
        try:
            if api_engine in ("deepseek-v4-pro", "deepseek-v4-flash"):
                raw_text = self._call_deepseek_api(api_engine, api_key, base_url, sys_prompt, user_prompt)
            else:
                # Local GGUF mode
                prompt = f"<|im_start|>system\n{sys_prompt}\nIMPORTANT: You MUST write your reasoning inside <think>...</think> tags strictly in Chinese (中文/zh-CN). The reasoning can be detailed. Write the final JSON object clearly.\n<|im_end|>\n<|im_start|>user\n{user_prompt}\n<|im_end|>\n<|im_start|>assistant\n"
                response = self.llm(prompt, max_tokens=1024, stop=["<|im_end|>"])
                raw_text = response["choices"][0]["text"].strip()

            think_content, cleaned_text = self._clean_json_text(raw_text)
            res = json.loads(cleaned_text)
            
            status = res.get("status", "NOT_ENOUGH_INFO").upper()
            if status not in ("SUPPORTED", "CONTRADICTED", "NOT_ENOUGH_INFO"):
                status = "NOT_ENOUGH_INFO"

            evidence_snippet = res.get("evidence_snippet", "").strip()
            if evidence_snippet:
                evidence_snippet = evidence_snippet.strip('"').strip("'").strip()
                
            if evidence_snippet:
                is_valid = False
                # 1. Strict substring match
                for s in snippets:
                    if evidence_snippet in s:
                        is_valid = True
                        break
                # 2. Normalized substring match (ignoring punctuation and case)
                if not is_valid:
                    def normalize_text(text: str) -> str:
                        return re.sub(r'[^a-zA-Z0-9а-яА-ЯёЁ]', '', text).lower()
                    norm_ev = normalize_text(evidence_snippet)
                    if norm_ev:
                        for s in snippets:
                            if norm_ev in normalize_text(s):
                                is_valid = True
                                break
                
                if not is_valid:
                    evidence_snippet = f"[模型摘要] {evidence_snippet}"

            return {
                "status": status,
                "explanation_zh": res.get("explanation_zh", "未给出逻辑说明。"),
                "evidence_snippet": evidence_snippet,
                "think": think_content if think_content else None
            }
        except Exception as e:
            print(f"NLI citation verification failed: {e}")
            return {
                "status": "AUDIT_FAILED",
                "explanation_zh": f"审计异常：由于大模型服务或网络连接故障，未能完成引用关联分析 (异常信息: {str(e)[:40]}).",
                "evidence_snippet": ""
            }

    def _call_deepseek_api(self, model: str, api_key: str, base_url: str, sys_prompt: str, user_prompt: str) -> str:
        # Resolve base URL
        url = "https://api.deepseek.com/v1/chat/completions"
        if base_url:
            url = base_url.rstrip("/") + "/chat/completions"
        
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
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            content = res_json["choices"][0]["message"].get("content", "")
            reasoning = res_json["choices"][0]["message"].get("reasoning_content", "")
            if reasoning:
                return f"<think>{reasoning}</think>\n{content}"
            return content

    def _clean_json_text(self, text: str) -> tuple[str, str]:
        text = text.strip()
        think_content = ""
        
        # Extract <think> content if present
        think_match = re.search(r'<think>(.*?)</think>', text, flags=re.DOTALL)
        if think_match:
            think_content = think_match.group(1).strip()
            text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        else:
            if text.startswith("<think>"):
                parts = text.split("</think>")
                if len(parts) == 1:
                    think_content = text[7:].strip()
                    text = "{}"
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
            
        json_start = text.find("{")
        json_end = text.rfind("}")
        if json_start != -1 and json_end != -1 and json_end > json_start:
            text = text[json_start:json_end+1]
            
        return think_content, text
