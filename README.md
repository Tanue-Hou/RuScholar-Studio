# RuScholar Studio

Evidence-driven Russian academic writing diagnostics, citation auditing, and manuscript review for Web UI and MCP-based AI agents. This project grew out of the earlier PhD Thesis Butler skill and now packages the same research-writing logic as a cloneable local application.

![Web UI diagnostics](docs/assets/webui-diagnostics.png)

The Web UI screenshot shows the hybrid diagnostic workflow: Russian manuscript text on the left, sentence-level highlights in the document, and discipline, perplexity, style risk, predictability risk, translationese risk, redundancy risk, and sentence reasoning on the right. Highlighted spans are review signals, not final misconduct judgments.

## Features

- Russian academic style diagnostics for cliches, connector overuse, passive voice, nominalization, genitive chains, and translationese.
- Local perplexity scoring with a GGUF model and early-exit heuristics for lower latency.
- Discipline-aware thresholds and writing rules from repository-local calibration assets.
- Citation integrity checks for in-text citations and bibliography entries.
- Local RAG evidence retrieval with BM25, plus optional OpenAlex-assisted evidence lookup.
- LLM/NLI citation judge for claim-evidence entailment, contradiction, or insufficient evidence.
- Two first-class entry points: Web UI for manual review and MCP tools for Claude, Codex, Cursor, and other agents.

## Reliability Position

RuScholar Studio is an audit assistant, not an automatic accusation engine.

Strong signals include citation-list mismatches, missing bibliography items, retrievable evidence snippets, and agreement between rule-based style flags and PPL anomalies. Signals that require human review include low PPL as AI suspicion, high PPL as translation risk, OpenAlex abstract-only evidence, and LLM/NLI judgments. Treat every result as a risk signal with an evidence trail.

## Requirements

- Python 3.9 or newer.
- Node.js 20 or newer.
- 16GB RAM recommended for the local 4B GGUF model.
- The default model is Qwen3-4B-Q5_K_M GGUF, around 2.7GB.
- Apple Silicon users should prefer a Metal-enabled `llama-cpp-python`; CPU-only machines can set `THESIS_BUTLER_GPU_LAYERS=0`.

## Quick Start

```bash
git clone <YOUR_REPOSITORY_URL>
cd ruscholar-studio
./setup.sh
```

Download the local model during setup:

```bash
DOWNLOAD_MODEL=1 ./setup.sh
```

Compile/install Metal support on Apple Silicon:

```bash
INSTALL_LLAMA_METAL=1 ./setup.sh
```

Windows:

```powershell
.\setup.ps1
```

## Manual Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download ru_core_news_sm

cd frontend
npm install
npm run build
cd ..
```

Download the local model:

```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

## Run the Web UI

```bash
source .venv/bin/activate
python backend/main.py
```

Open `http://localhost:8000`. Host and port are configurable:

```bash
THESIS_BUTLER_HOST=127.0.0.1 THESIS_BUTLER_PORT=8010 python backend/main.py
```

## MCP Server

Run the MCP server:

```bash
python -m mcp_server.server
```

Example client configuration:

```json
{
  "mcpServers": {
    "ruscholar-studio": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/YOUR_CLONE_PATH/ruscholar-studio"
    }
  }
}
```

Available MCP tools:

- `analyze_manuscript`
- `audit_citations`
- `retrieve_evidence`
- `suggest_revision`
- `export_report`
- `check_model_installed`
- `download_model_tool`
- `register_references`
- `clear_references`
- `list_references`

## Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Common variables:

- `DEEPSEEK_API_KEY`: optional cloud judge key.
- `DEEPSEEK_BASE_URL`: OpenAI-compatible DeepSeek endpoint.
- `THESIS_BUTLER_MODEL_PATH`: local GGUF model path.
- `THESIS_BUTLER_MODEL_URL`: model download URL.
- `THESIS_BUTLER_RULES_PATH`: repository or custom rule file path.
- `THESIS_BUTLER_GPU_LAYERS`: `-1` for GPU offload, `0` for CPU-only.

## Tests

```bash
pytest -q
cd frontend && npm run build
```

## Repository Notes

Model files, `.env`, `frontend/dist/`, and `node_modules/` are intentionally ignored. The repository does include `naturalization_layer/rules/polishing_rules_v5.json` and `docs/assets/webui-diagnostics.png` because they are required for out-of-the-box documentation and rule loading.

