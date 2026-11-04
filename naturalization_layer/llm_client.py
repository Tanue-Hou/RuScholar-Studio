"""
Shared LLM plumbing for the judges (StyleJudge, NLICitationJudge).

Before this module existed, each judge carried its own copy of the cloud API
call, the <think>/JSON cleaning and the engine-name mapping.
"""
import json
import os
import re
import urllib.request

DEFAULT_CLOUD_BASE_URL = "https://api.deepseek.com/v1"

# Model names accepted by the cloud (OpenAI-compatible) code path.
CLOUD_MODELS = ("deepseek-v4-pro", "deepseek-v4-flash", "deepseek-flash")


def resolve_cloud_model(engine_type: str) -> str:
    """
    Judge-level mapping: "*pro*" -> deepseek-v4-pro, "*flash*" -> deepseek-flash,
    anything else (e.g. "local") is returned unchanged. Callers then use
    is_cloud_model() to decide between the cloud API and the local GGUF model.
    """
    if "pro" in engine_type:
        return "deepseek-v4-pro"
    if "flash" in engine_type:
        return "deepseek-flash"
    return engine_type


def cloud_model_for(engine_type: str) -> str:
    """Pipeline-level mapping for non-local modes (hybrid-*/cloud-*): flash or pro."""
    return "deepseek-flash" if "flash" in engine_type else "deepseek-v4-pro"


def is_cloud_model(model: str) -> bool:
    return model in CLOUD_MODELS


def call_openai_compatible(model: str, api_key: str, base_url: str, sys_prompt: str, user_prompt: str,
                           timeout: float = None) -> str:
    """
    POST a JSON-mode chat completion and return the content. DeepSeek's
    `reasoning_content` (if any) is wrapped in <think>...</think> in front.
    Falls back to DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL from the environment.
    """
    api_key = (api_key or "").strip() or os.getenv("DEEPSEEK_API_KEY", "")
    base_url = (base_url or "").strip() or os.getenv("DEEPSEEK_BASE_URL", "") or DEFAULT_CLOUD_BASE_URL
    if timeout is None:
        timeout = float(os.getenv("RUSCHOLAR_CLOUD_TIMEOUT", "30"))

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
    with urllib.request.urlopen(req, timeout=timeout) as response:
        res_json = json.loads(response.read().decode("utf-8"))
    message = res_json["choices"][0]["message"]
    content = message.get("content", "")
    reasoning = message.get("reasoning_content", "")
    if reasoning:
        return f"<think>{reasoning}</think>\n{content}"
    return content


def build_qwen_prompt(sys_prompt: str, user_prompt: str, assistant_prefix: str = "") -> str:
    """ChatML prompt for the local Qwen GGUF model."""
    return (
        f"<|im_start|>system\n{sys_prompt}\n<|im_end|>\n"
        f"<|im_start|>user\n{user_prompt}\n<|im_end|>\n"
        f"<|im_start|>assistant\n{assistant_prefix}"
    )


def complete_local(llm, prompt: str, max_tokens: int = 1024) -> str:
    response = llm(prompt, max_tokens=max_tokens, stop=["<|im_end|>"])
    return response["choices"][0]["text"].strip()


def clean_json_text(text: str) -> tuple[str, str]:
    """
    Split model output into (think_content, json_text): extracts <think>
    reasoning (closed, unclosed or missing opening tag), strips code fences
    and any prose around the outermost {...}.
    """
    text = text.strip()
    think_content = ""

    think_match = re.search(r'<think>(.*?)</think>', text, flags=re.DOTALL)
    if think_match:
        think_content = think_match.group(1).strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    elif text.startswith("<think>"):
        parts = text.split("</think>")
        if len(parts) == 1:
            # Unclosed think tag: no JSON can follow.
            think_content = text[7:].strip()
            text = "{}"
        else:
            think_content = parts[0][7:].strip()
            text = parts[1].strip()
    elif "</think>" in text:
        # Prompt pre-filled "<think>\n", so only the closing tag is in the output.
        parts = text.split("</think>", 1)
        think_content = parts[0].strip()
        text = parts[1].strip()

    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # Sometimes Qwen prefixes the JSON with prose such as "Вот JSON:".
    json_start = text.find("{")
    json_end = text.rfind("}")
    if json_start != -1 and json_end != -1 and json_end > json_start:
        text = text[json_start:json_end + 1]

    return think_content, text
