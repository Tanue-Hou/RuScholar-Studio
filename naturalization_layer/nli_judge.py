try:
    from llama_cpp import Llama
except ImportError:
    Llama = None
import json
import re

from naturalization_layer.llm_client import (
    build_qwen_prompt, call_openai_compatible, clean_json_text, complete_local,
    is_cloud_model, resolve_cloud_model,
)

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

        api_engine = resolve_cloud_model(engine_type)
        if not is_cloud_model(api_engine) and self.llm is None:
            return {
                "status": "AUDIT_FAILED",
                "explanation_zh": "本地模型未安装或未能加载，已跳过引用逻辑核验。可下载本地模型，或切换到混合/云端模式。",
                "evidence_snippet": ""
            }

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
            if is_cloud_model(api_engine):
                raw_text = self._call_deepseek_api(api_engine, api_key, base_url, sys_prompt, user_prompt)
            else:
                # Local GGUF mode
                prompt = build_qwen_prompt(
                    sys_prompt + "\nIMPORTANT: You MUST write your reasoning inside <think>...</think> tags strictly in Chinese (中文/zh-CN). The reasoning can be detailed. Write the final JSON object clearly.",
                    user_prompt,
                )
                raw_text = complete_local(self.llm, prompt)

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

    # Kept as methods so tests (and callers) can patch them per instance.
    def _call_deepseek_api(self, model: str, api_key: str, base_url: str, sys_prompt: str, user_prompt: str) -> str:
        return call_openai_compatible(model, api_key, base_url, sys_prompt, user_prompt)

    def _clean_json_text(self, text: str) -> tuple[str, str]:
        return clean_json_text(text)
