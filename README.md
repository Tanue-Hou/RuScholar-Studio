# RuScholar Studio 🎓

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Node Version](https://img.shields.io/badge/node-18%2B-green)](https://nodejs.org/)

**RuScholar Studio** (formerly *PhD Thesis Butler*) is a professional-grade, privacy-first academic writing quality audit and style naturalization workspace designed specifically for Russian dissertations, manuscripts, and research papers. It provides a hybrid diagnostic workflow that runs locally or in the cloud.

---

### Language / Язык / 语言

[English](README.md) · [Русский](README_RU.md) · [简体中文](README_ZH.md)

---

## 📸 Web UI Cockpit

Below is the visual dashboard showing the hybrid diagnostics workflow in action:

![Web UI Diagnostics](docs/assets/webui-diagnostics.png)

> [!NOTE]
> The Web UI highlights stylistic and evidence anomalies in real-time. Sentences are color-coded (yellow for warning, red for high risk) based on rule violations, perplexity (PPL) anomalies, and citation verification results. This is designed to serve as a **review assistant and evidence tracer**, not an automated verdict of plagiarism or AI generation.

---

## 🌟 Key Features

*   **No Black-Box AI Scores**: Avoids the "AI detection score" trap. Instead of a single arbitrary percentage, the system produces transparent risk indices, grammar statistics, and verifiable citation evidence.
*   **Russian-Specific Rhetoric Heuristics**: Custom-tailored rules analyzing nominalization (noun/verb ratio), passive voice bloat, long genitive chains (noun stacking), missing predicate verbs, and translationese patterns typical of Russian academic prose.
*   **Local-First Privacy**: Supports local GGUF model execution (`Qwen3-4B`), offline physical perplexity (PPL) probing, and local PDF/BibTeX database RAG, ensuring your unpublished draft stays safe on your machine.
*   **LLM-as-NLI Judge Citation Audit**: Automatically checks the logical support of in-text citations against reference sources, classifying relations as *Entailment (Supported)*, *Contradiction*, or *Neutral (Not Enough Info)*.
*   **FastMCP Stdio Daemon**: Built-in support for the Model Context Protocol (MCP), allowing AI agents like Claude Code, Cursor, and Claude Desktop to interact directly with your manuscript library.
*   **Hybrid & Cloud Scalability**: Choose from fully offline CPU/GPU diagnostics, hybrid execution (local PPL probe + cloud DeepSeek reasoning), or pure cloud mode.

---

## 🧠 Upstream Skill Relationship

RuScholar Studio is the engineering and visualization runtime built on top of the **PhD Thesis Butler** (`phd-thesis-butler`) custom agent skill.

```
+-----------------------------------------------------------+
|          PhD Thesis Butler Skill (Upstream Brain)         |
|  - 16.7K Russian-first templates from 2,118 papers       |
|  - Academic discipline rules and outline blueprints       |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|             RuScholar Studio (Engineering Layer)          |
|  - Web UI Dashboard         - FastMCP Server Daemon       |
|  - Local PPL / NLI Probes   - PDF Parser / RAG Retriever  |
+-----------------------------------------------------------+
```

| Dimension | PhD Thesis Butler Skill | RuScholar Studio |
| :--- | :--- | :--- |
| **Role** | AI assistant writing skill | Runnable, deployable audit desktop workspace |
| **Core Asset** | 16,722 templates across 5 academic clusters | Diagnostic server, Web UI, MCP server, report generator |
| **Tasks** | Outlining, writing templates, rhetoric suggestions | Style risk checking, PPL estimation, NLI audit, RAG |
| **How it runs** | Loaded by Codex/Hermes/Claude agent | Run as a FastAPI/React application or stdio service |
| **Relationship** | Upstream knowledge base & writing paradigm | Downstream execution framework & verification layer |

---

## 🛠️ System Requirements

| Resource | Minimum | Recommended |
| :--- | :--- | :--- |
| **Python** | 3.9+ | 3.10+ |
| **Node.js** | 18+ | 20+ |
| **RAM** | 8 GB (for cloud-only mode) | 16 GB+ (for local model mode) |
| **Disk Space** | 500 MB (source and dependencies) | 4 GB (includes 2.7 GB local GGUF model) |
| **OS** | macOS / Windows / Linux | macOS Apple Silicon (with Metal acceleration) |

---

## 🚀 Quick Start

### 1. Installation

Clone the repository and run the setup script:

**macOS / Linux**:
```bash
git clone https://github.com/Tanue-Hou/RuScholar-Studio.git
cd RuScholar-Studio
chmod +x setup.sh
./setup.sh
```
*   To download the local GGUF model during setup: `DOWNLOAD_MODEL=1 ./setup.sh`
*   To compile `llama-cpp-python` with Metal acceleration on macOS: `INSTALL_LLAMA_METAL=1 ./setup.sh`

**Windows (PowerShell)**:
```powershell
.\setup.ps1
```
*   To download the model: `.\setup.ps1 -DownloadModel`

### 2. Local Model Setup

To use the `local` or `hybrid` modes offline, the system utilizes the **Qwen3-4B-Q5_K_M GGUF** model (approx. 2.7 GB). By default, it looks for the model file at:
```
models/Qwen3-4B-Q5_K_M.gguf
```

You can download it manually or let the setup script/MCP tool handle it.
To download via CLI:
```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

---

## 💻 Running the Web UI

To start the single-port integrated server (where FastAPI hosts the pre-built React frontend):

```bash
source .venv/bin/activate
python backend/main.py
```
Open **`http://localhost:8000`** in your browser.

### Development Mode (with Hot Reload)
If you want to modify the React frontend:
```bash
# Terminal 1: Starts Backend API
source .venv/bin/activate
python backend/main.py

# Terminal 2: Starts Frontend Dev Server
cd frontend
npm run dev
```
Open the dev server port printed in the terminal (usually `http://localhost:5173`).

---

## 🔌 MCP Integration

To let AI clients (like Claude Desktop, Claude Code, or Cursor) audit your documents and bibliography directly:

### 1. Claude Desktop
Add the server config to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "ruscholar-studio": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "<YOUR_CLONE_PATH>/RuScholar-Studio"
    }
  }
}
```

### 2. Claude Code
Run the following command:
```bash
claude mcp add ruscholar-studio python -m mcp_server.server --cwd "<YOUR_CLONE_PATH>/RuScholar-Studio"
```

### Available Tools:
1.  `analyze_manuscript`: Audits style, translationese, and perplexity (PPL) of paragraphs.
2.  `audit_citations`: Cross-checks in-text brackets citations against the bibliography.
3.  `retrieve_evidence`: Search snippets from local PDF/BibTeX caches or OpenAlex.
4.  `suggest_revision`: Generates context-aware rewriting proposals.
5.  `export_report`: Exports the audit checklist as a Markdown/JSON report.
6.  `check_model_installed`: Verifies local model status.
7.  `download_model_tool`: Automatically downloads the Qwen GGUF model.
8.  `register_references`: Registers BibTeX databases and/or local PDF paths.
9.  `clear_references`: Clears reference database for the session.
10. `list_references`: Lists all registered references in the session.

---

## ⚙️ Configuration Variables

Create a `.env` file in the root directory by copying `.env.example`:
```bash
cp .env.example .env
```

| Env Variable | Default | Description |
| :--- | :--- | :--- |
| `DEEPSEEK_API_KEY` | *(Empty)* | API key for DeepSeek cloud judge models. |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | Custom endpoint for cloud judge APIs. |
| `RUSCHOLAR_MODEL_PATH` | `models/Qwen3-4B-Q5_K_M.gguf` | Path to the local GGUF model file. |
| `RUSCHOLAR_MODEL_URL` | `https://modelscope.cn/models/Qwen/Qwen3-4B-GGUF/...` | URL to download the model from. |
| `RUSCHOLAR_RULES_PATH` | `naturalization_layer/rules/polishing_rules_v5.json` | Path to the custom skill JSON rules. |
| `RUSCHOLAR_GPU_LAYERS` | `-1` | Number of model layers offloaded to GPU (-1 for max, 0 for CPU). |
| `RUSCHOLAR_HOST` | `0.0.0.0` | Binding host for backend API. |
| `RUSCHOLAR_PORT` | `8000` | Binding port for backend API. |

---

## 🧪 Testing

Run the full automated test suite to verify services, RAG retrievers, and MCP stdio interfaces:

```bash
pytest -v
```

---

## 📝 GitHub Release & Packaging Guide

When packaging and preparing a release to GitHub, ensure that heavy binary assets are ignored via git:

*   **Ignored Files**: GGUF model files (`models/*.gguf`), node modules (`frontend/node_modules/`), production build artifacts (`frontend/dist/`), temporary cache folders (`.pytest_cache/`, `scratch/`), and virtual environments (`.venv/`) are excluded automatically via `.gitignore`.
*   **Required Files**: Ensure that `__init__.py` files in `services/`, `mcp_server/`, `backend/`, and `tests/` are committed so Python packaging and imports run smoothly.

---

## 🤝 Contribution & License

Contributions, issues, and feature requests are welcome. Feel free to open a pull request.
This project is licensed under the **MIT License**.
