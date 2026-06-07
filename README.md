# PhD Thesis Butler / RuScholar Studio

**Version: v5.2.0-alpha**  
**Languages:** **English** | [中文](README_ZH.md) | [Русский](README_RU.md)

Evidence-driven academic writing quality auditing for dissertations, manuscripts, and research papers. The project continues the original **PhD Thesis Butler** skill and packages it as **RuScholar Studio**: a local research-writing workbench with a Web UI and MCP tools for AI agents.

The system avoids the simplistic "AI detection score" framing. Instead, it uses a traceable architecture built from a **local rule engine, local PPL probing, local/online evidence retrieval, and LLM-as-NLI citation auditing**. Results should be treated as review signals and evidence trails, not automatic misconduct verdicts.

Version naming follows the source rule asset lineage: `polishing_rules_v5.json` is currently at rules version `5.1.3`; this repository adds Web UI, MCP, shared services, GitHub setup scripts, and trilingual documentation on top of that line, so the release is named `v5.2.0-alpha`.

![Web UI diagnostics](docs/assets/webui-diagnostics.png)

The Web UI shows the hybrid diagnostic workflow: Russian manuscript text on the left, sentence-level highlights in the document, and discipline, average PPL, style risk, predictability risk, translationese risk, redundancy risk, and sentence reasoning on the right. Yellow and red highlights mark review candidates, not final conclusions.

## Requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| Python | 3.9+ | 3.10+ |
| Node.js | 18+ | 20+ |
| RAM | 8 GB for cloud-only mode | 16 GB for local model mode |
| Disk | 500 MB for source and dependencies | 4 GB including the 2.7 GB GGUF model |
| OS | macOS / Linux / Windows | macOS Apple Silicon with Metal |

Apple Silicon users can use Metal acceleration. Linux and Windows users can avoid local model compilation by using `cloud-pro` or `cloud-flash`.

## Quick Start

```bash
git clone https://github.com/Tanue-Hou/RuScholar-Studio.git
cd RuScholar-Studio
chmod +x setup.sh
./setup.sh
```

Download the local model during setup:

```bash
DOWNLOAD_MODEL=1 ./setup.sh
```

Force Metal-enabled installation on Apple Silicon:

```bash
INSTALL_LLAMA_METAL=1 ./setup.sh
```

Windows:

```powershell
.\setup.ps1
```

## Local Model

To protect manuscript privacy, the local PPL probe and local NLI/style judge can use **Qwen3-4B-Q5_K_M GGUF**. The model is around 2.7 GB and defaults to:

```text
models/Qwen3-4B-Q5_K_M.gguf
```

Manual download:

```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

You can also let an MCP client call `download_model_tool`. Without the local model, `local` and `hybrid` modes are unavailable, but cloud-only modes still work.

## Web UI

Run the bundled backend and built frontend:

```bash
source .venv/bin/activate
python backend/main.py
```

Open `http://localhost:8000`.

Development mode:

```bash
# Terminal 1
python backend/main.py

# Terminal 2
cd frontend
npm run dev
```

Override host and port:

```bash
THESIS_BUTLER_HOST=127.0.0.1 THESIS_BUTLER_PORT=8010 python backend/main.py
```

## MCP Integration

The project supports **MCP (Model Context Protocol)** so Claude Code, Cursor, Claude Desktop, Codex, and other agents can call local audit tools directly.

Start the MCP server:

```bash
python -m mcp_server.server
```

Claude Desktop example:

```json
{
  "mcpServers": {
    "thesis-butler": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/YOUR_CLONE_PATH/RuScholar-Studio"
    }
  }
}
```

Claude Code example:

```bash
claude mcp add thesis-butler python -m mcp_server.server --cwd "/YOUR_CLONE_PATH/RuScholar-Studio"
```

Available MCP tools:

| # | Tool | Purpose |
|---|------|---------|
| 1 | `analyze_manuscript` | Diagnose academic style, translationese, noun stacking, and PPL risk |
| 2 | `audit_citations` | Cross-check in-text citations and bibliography entries |
| 3 | `retrieve_evidence` | Retrieve evidence snippets from local references or OpenAlex |
| 4 | `suggest_revision` | Generate context-aware academic revision suggestions |
| 5 | `export_report` | Export Markdown or JSON audit reports |
| 6 | `check_model_installed` | Verify local model presence and size |
| 7 | `download_model_tool` | Download the local GGUF model |
| 8 | `register_references` | Register BibTeX text and/or local PDF paths |
| 9 | `clear_references` | Clear a session reference library |
| 10 | `list_references` | List a session reference library |

## Diagnostic Architecture

The system uses a multi-track decision process:

1. **Track A: Rule and style structure**  
   Detects noun/verb ratio, passive constructions, genitive chains, connector overuse, academic cliches, and translationese.

2. **Track B: Probabilistic signal**  
   Computes sentence perplexity with a local GGUF model and uses early-exit heuristics to reduce inference cost.

3. **Track C: Citation consistency**  
   Checks bidirectional gaps between in-text citations and bibliography entries, with local BM25 retrieval and optional OpenAlex evidence lookup.

4. **Track D: LLM/NLI evidence audit**  
   Classifies claim-evidence relationships as entailed, contradicted, or not enough information.

High-risk citation issues are surfaced first. Style and PPL anomalies trigger context-aware judge analysis. The system keeps explanations, metrics, and source snippets available for human review.

## Modes

| Mode | Local PPL | LLM Judge | Use Case |
|------|-----------|-----------|----------|
| `local` | Yes | Local Qwen | Fully offline and privacy-preserving |
| `hybrid-pro` | Yes | DeepSeek Pro | Local probability probe plus cloud deep analysis |
| `hybrid-flash` | Yes | DeepSeek Flash | Local probability probe plus fast cloud analysis |
| `cloud-pro` | No | DeepSeek Pro | Cloud-only deep diagnostics |
| `cloud-flash` | No | DeepSeek Flash | Cloud-only fast diagnostics |

## Configuration

```bash
cp .env.example .env
```

Common variables:

- `DEEPSEEK_API_KEY`: optional cloud judge key.
- `DEEPSEEK_BASE_URL`: OpenAI-compatible DeepSeek endpoint.
- `THESIS_BUTLER_MODEL_PATH`: local GGUF model path.
- `THESIS_BUTLER_MODEL_URL`: model download URL.
- `THESIS_BUTLER_RULES_PATH`: discipline-specific writing rule path.
- `THESIS_BUTLER_GPU_LAYERS`: `-1` for GPU offload, `0` for CPU-only.

## Verification

```bash
pytest -q
cd frontend && npm run build
```

The test suite covers the rule engine, PPL engine, LLM judge, citation auditing, RAG/NLI, service layer, and MCP stdio integration.

## Contributing and License

Issues and pull requests are welcome. The project is released under the MIT License.
