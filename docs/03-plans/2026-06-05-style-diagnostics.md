# Style Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local CLI tool in Python that analyzes Russian academic text for translationese, uniformity, and clichés using rule-based heuristics and a quantized Qwen 3 4B model via llama.cpp.

**Architecture:** The tool is built as a command-line interface. It uses `spacy` for Russian text segmentation. Track A applies Regex and statistical heuristics. Track B uses `llama-cpp-python` to evaluate sequence log-probabilities (PPL) and variance. Finally, anomalous sentences are evaluated by Qwen 3 via structured JSON zero-shot prompting to provide rewrite suggestions.

**Tech Stack:** Python 3.10+, `llama-cpp-python` (Metal/CUDA), `spacy` (ru_core_news_sm), `rich` (for CLI UI), `pydantic`.

---

### Task 1: Environment Setup & Foundation

**Files:**
- Create: `requirements.txt`
- Create: `scripts/style_diagnostics.py`
- Create: `naturalization_layer/__init__.py`

- [ ] **Step 1: Write `requirements.txt`**

```text
llama-cpp-python>=0.2.75
spacy>=3.7.0
rich>=13.7.0
pydantic>=2.7.0
```

- [ ] **Step 2: Install dependencies and download Spacy model**

Run: `pip install -r requirements.txt && python -m spacy download ru_core_news_sm`
Expected: Installation completes successfully.

- [ ] **Step 3: Create base CLI scaffold**

```python
# scripts/style_diagnostics.py
import argparse
from rich.console import Console

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Russian Style Diagnostics & Naturalization Engine")
    parser.add_argument("--input", required=True, help="Path to input markdown or text file")
    parser.add_argument("--model", required=False, help="Path to Qwen 3 GGUF model")
    args = parser.parse_args()

    console.print(f"[bold blue]Initializing Diagnostics for:[/bold blue] {args.input}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Verify the CLI scaffold**

Run: `python scripts/style_diagnostics.py --input dummy.txt`
Expected: Output showing "Initializing Diagnostics for: dummy.txt"

- [ ] **Step 5: Commit**

```bash
git add requirements.txt scripts/style_diagnostics.py naturalization_layer/__init__.py
git commit -m "feat: initialize style diagnostics CLI scaffold"
```

### Task 2: Track A - Rule-Based Heuristics (Zero-Model)

**Files:**
- Create: `naturalization_layer/rules_engine.py`
- Create: `tests/test_rules_engine.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_rules_engine.py
from naturalization_layer.rules_engine import analyze_text_rules

def test_analyze_text_rules():
    text = "Это тестовое предложение. Важно отметить, что оно короткое."
    result = analyze_text_rules(text)
    assert result["sentence_count"] == 2
    assert result["cliche_matches"] == 1
    assert "Важно отметить, что" in result["matched_cliches"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_rules_engine.py -v`
Expected: FAIL with ModuleNotFoundError or ImportError

- [ ] **Step 3: Write minimal implementation**

```python
# naturalization_layer/rules_engine.py
import spacy
import re

try:
    nlp = spacy.load("ru_core_news_sm")
except OSError:
    pass # Tests might skip or mock this, assume loaded

CLICHES = [r"важно отметить, что", r"таким образом", r"в заключение"]

def analyze_text_rules(text: str) -> dict:
    nlp = spacy.load("ru_core_news_sm")
    doc = nlp(text)
    sentences = list(doc.sents)
    
    cliche_matches = 0
    matched = []
    text_lower = text.lower()
    
    for cliche in CLICHES:
        if re.search(cliche, text_lower):
            cliche_matches += 1
            matched.append(cliche.replace('\\', ''))
            
    lengths = [len([t for t in s if not t.is_punct]) for s in sentences]
    variance = 0.0
    if len(lengths) > 1:
        mean = sum(lengths) / len(lengths)
        variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
            
    return {
        "sentence_count": len(sentences),
        "cliche_matches": cliche_matches,
        "matched_cliches": matched,
        "length_variance": variance,
        "sentences": [s.text for s in sentences]
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_rules_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add naturalization_layer/rules_engine.py tests/test_rules_engine.py
git commit -m "feat: implement Track A rule-based heuristics"
```

### Task 3: Track B - PPL & Logits Engine (Llama.cpp)

**Files:**
- Create: `naturalization_layer/ppl_engine.py`

- [ ] **Step 1: Write the Llama.cpp evaluator wrapper**

```python
# naturalization_layer/ppl_engine.py
from llama_cpp import Llama
import math

class PPLEngine:
    def __init__(self, model_path: str):
        # n_gpu_layers=-1 delegates all layers to Metal/CUDA
        # logits_all=True is required to evaluate existing prompt
        self.llm = Llama(model_path=model_path, n_gpu_layers=-1, logits_all=True, verbose=False)
        
    def evaluate_sentence_ppl(self, sentence: str) -> float:
        """
        Evaluate PPL of a sentence without generating new tokens.
        """
        tokens = self.llm.tokenize(sentence.encode("utf-8"), add_bos=True)
        if len(tokens) <= 1:
            return 0.0
            
        self.llm.reset()
        self.llm.eval(tokens)
        
        # Calculate NLL
        nll = 0.0
        for i in range(len(tokens) - 1):
            logits = self.llm._scores[i, :]
            # Simple softmax log prob for the next token
            max_logit = max(logits)
            exp_sum = sum(math.exp(l - max_logit) for l in logits)
            log_probs = [l - max_logit - math.log(exp_sum) for l in logits]
            
            target_token = tokens[i + 1]
            nll -= log_probs[target_token]
            
        return math.exp(nll / (len(tokens) - 1))
```

- [ ] **Step 2: Commit**

```bash
git add naturalization_layer/ppl_engine.py
git commit -m "feat: implement Llama PPL evaluation engine"
```

### Task 4: Stylistic LLM Judge

**Files:**
- Create: `naturalization_layer/llm_judge.py`

- [ ] **Step 1: Write LLM Judge Logic**

```python
# naturalization_layer/llm_judge.py
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
```

- [ ] **Step 2: Commit**

```bash
git add naturalization_layer/llm_judge.py
git commit -m "feat: add zero-shot stylistic LLM judge"
```

### Task 5: Integration

**Files:**
- Modify: `scripts/style_diagnostics.py:1-20`

- [ ] **Step 1: Wire it all together**

```python
import argparse
from rich.console import Console
from rich.table import Table
import os

from naturalization_layer.rules_engine import analyze_text_rules
from naturalization_layer.ppl_engine import PPLEngine
from naturalization_layer.llm_judge import StyleJudge

console = Console()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", required=False)
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Rules
    rules_res = analyze_text_rules(text)
    console.print(f"[bold green]Track A: Heuristics[/bold green]")
    console.print(f"Sentences: {rules_res['sentence_count']}")
    console.print(f"Cliches found: {rules_res['matched_cliches']}")
    
    if not args.model or not os.path.exists(args.model):
        console.print("[yellow]No model provided. Skipping Track B & C.[/yellow]")
        return
        
    # 2. PPL & Judge
    console.print(f"[bold green]Loading Model...[/bold green]")
    engine = PPLEngine(args.model)
    judge = StyleJudge(engine.llm)
    
    table = Table(title="Sentence Diagnostics")
    table.add_column("Sentence", style="cyan", max_width=40)
    table.add_column("PPL", justify="right", style="magenta")
    table.add_column("Suggestion", style="green", max_width=40)
    
    for s in rules_res["sentences"]:
        ppl = engine.evaluate_sentence_ppl(s)
        # Mock trigger: evaluate if PPL is suspiciously low or it contains cliches
        if ppl < 10.0 or rules_res['cliche_matches'] > 0:
            diag = judge.diagnose_sentence(s)
            suggestion = diag.get("rewrite_suggestion", "")
        else:
            suggestion = "-"
        table.add_row(s[:50]+"...", f"{ppl:.2f}", suggestion)
        
    console.print(table)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add scripts/style_diagnostics.py
git commit -m "feat: integrate rules, PPL, and LLM judge into CLI"
```

### Task 6: Document Parsers (PDF & DOCX)

**Files:**
- Create: `naturalization_layer/document_parser.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Write `naturalization_layer/document_parser.py`**

```python
import docx
from pypdf import PdfReader
import os

def parse_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def parse_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text

def parse_document(file_path: str) -> str:
    _, ext = os.path.splitext(file_path.lower())
    if ext == ".docx":
        return parse_docx(file_path)
    elif ext == ".pdf":
        return parse_pdf(file_path)
    elif ext in [".txt", ".md"]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file format: {ext}")
```

- [ ] **Step 2: Append new dependencies to `requirements.txt`**

```text
python-docx>=1.1.0
pypdf>=4.0.0
streamlit>=1.32.0
```

- [ ] **Step 3: Commit**

```bash
git add naturalization_layer/document_parser.py requirements.txt
git commit -m "feat: add PDF and DOCX document parser and update requirements"
```

### Task 7: Streamlit Web UI & Model Downloader

**Files:**
- Create: `naturalization_layer/model_downloader.py`
- Create: `scripts/web_app.py`

- [ ] **Step 1: Write the Model Downloader helper**

```python
# naturalization_layer/model_downloader.py
import os
import urllib.request
from rich.console import Console

console = Console()

MODEL_URL = "https://modelscope.cn/api/v1/models/qwen/Qwen2.5-3B-Instruct-GGUF/repo/files?path=qwen2.5-3b-instruct-q5_k_m.gguf"
# Fallback to HF mirror: "https://hf-mirror.com/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q5_k_m.gguf"

def download_model(dest_path: str):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    if os.path.exists(dest_path):
        return
        
    console.print(f"[yellow]Downloading Qwen GGUF model to {dest_path}...[/yellow]")
    urllib.request.urlretrieve(MODEL_URL, dest_path)
    console.print("[green]Download complete![/green]")
```

- [ ] **Step 2: Write `scripts/web_app.py`**

```python
# scripts/web_app.py
import streamlit as st
import os
import tempfile
from naturalization_layer.document_parser import parse_document
from naturalization_layer.rules_engine import analyze_text_rules
from naturalization_layer.ppl_engine import PPLEngine
from naturalization_layer.llm_judge import StyleJudge
from naturalization_layer.model_downloader import download_model

st.set_page_config(page_title="Academic Russian Naturalizer", layout="wide")
st.title("🇷🇺 Academic Russian Style Diagnostics & Naturalization")

# Configuration
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "qwen2.5-3b-instruct-q5_k_m.gguf")

# Sidebar for Model Status
st.sidebar.header("Model Management")
if not os.path.exists(MODEL_PATH):
    st.sidebar.warning("Model file not found locally.")
    if st.sidebar.button("Download Qwen 3B GGUF Model (3.2GB)"):
        with st.spinner("Downloading model from ModelScope... Please wait."):
            download_model(MODEL_PATH)
        st.sidebar.success("Model downloaded successfully!")
else:
    st.sidebar.success("Qwen 3B GGUF Model is loaded.")

# File Uploader
uploaded_file = st.file_uploader("Upload draft (PDF, DOCX, TXT, MD)", type=["pdf", "docx", "txt", "md"])

if uploaded_file is not None:
    # Save to temp file to read
    with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split(".")[-1]) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
        
    try:
        text = parse_document(tmp_path)
    finally:
        os.unlink(tmp_path)
        
    st.info(f"Loaded {len(text)} characters from {uploaded_file.name}")
    
    # Run Rules Heuristics
    rules_res = analyze_text_rules(text)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Track A: Structural Diagnostics")
        st.metric("Sentence Count", rules_res["sentence_count"])
        st.metric("Cliché Detections", rules_res["cliche_matches"])
        if rules_res["matched_cliches"]:
            st.write("Matched clichés:", rules_res["matched_cliches"])
            
    # LLM Diagnostics if model exists
    if os.path.exists(MODEL_PATH):
        st.subheader("🧠 Track B & C: Model PPL & Academic Rewriting")
        if st.button("Run Deep Analysis"):
            engine = PPLEngine(MODEL_PATH)
            judge = StyleJudge(engine.llm)
            
            results = []
            for s in rules_res["sentences"]:
                ppl = engine.evaluate_sentence_ppl(s)
                suggestion = "-"
                # Check for low PPL (unnatural smoothness)
                if ppl < 10.0 or any(c in s.lower() for c in rules_res["matched_cliches"]):
                    diag = judge.diagnose_sentence(s)
                    suggestion = diag.get("rewrite_suggestion", "-")
                results.append({"Sentence": s, "PPL": f"{ppl:.2f}", "Rewrite Suggestion": suggestion})
                
            st.table(results)
    else:
        st.warning("Please download the Qwen model in the sidebar to enable deep PPL and rewrite suggestions.")
```

- [ ] **Step 3: Commit**

```bash
git add naturalization_layer/model_downloader.py scripts/web_app.py
git commit -m "feat: implement Streamlit Web App and Model Downloader"
```

