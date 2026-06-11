# RuScholar Studio MCP Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Register and deploy the local RuScholar Studio MCP server in Google Antigravity.

**Architecture:** Copy `.env.example` to `.env` in the repository root to configure local GGUF model paths and GPU layers, then update the global `~/.gemini/config/mcp_config.json` registry with the server's command, args, cwd, and PYTHONPATH environment variable.

**Tech Stack:** Python 3.13, MCP, JSON, Dotenv

---

### Task 1: Create project `.env` file

**Files:**
- Create: `/Users/tanue/Documents/antigravity/friendly-lavoisier/.env`

- [ ] **Step 1: Copy environment template to `.env`**
  Write the content matching `.env.example` to `/Users/tanue/Documents/antigravity/friendly-lavoisier/.env`.
  Content:
  ```ini
  # Optional cloud judge provider
  DEEPSEEK_API_KEY=
  DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

  # Local model and rule resources
  RUSCHOLAR_MODEL_PATH=models/Qwen3-4B-Q5_K_M.gguf
  RUSCHOLAR_MODEL_URL=https://modelscope.cn/models/Qwen/Qwen3-4B-GGUF/resolve/master/Qwen3-4B-Q5_K_M.gguf
  RUSCHOLAR_RULES_PATH=naturalization_layer/rules/polishing_rules_v5.json

  # llama.cpp GPU offload. Use -1 for full offload, 0 for CPU-only fallback.
  RUSCHOLAR_GPU_LAYERS=-1

  # Web UI
  RUSCHOLAR_HOST=0.0.0.0
  RUSCHOLAR_PORT=8000
  ```

- [ ] **Step 2: Commit `.env` configuration**
  (Note: `.env` is typically gitignored. Let's make sure it is not added to git so we keep it local).
  Verify that `.env` is not tracked by git:
  Run: `git status --ignored`
  Expected: `.env` is in the list of ignored files.

---

### Task 2: Register MCP server in Antigravity config

**Files:**
- Modify: `/Users/tanue/.gemini/config/mcp_config.json`

- [ ] **Step 1: Write MCP server configuration to `mcp_config.json`**
  Write the JSON block to register the server:
  ```json
  {
    "mcpServers": {
      "ruscholar-studio": {
        "command": "/Users/tanue/miniforge3/bin/python3",
        "args": [
          "-m",
          "mcp_server.server"
        ],
        "cwd": "/Users/tanue/Documents/antigravity/friendly-lavoisier",
        "env": {
          "PYTHONPATH": "/Users/tanue/Documents/antigravity/friendly-lavoisier"
        }
      }
    }
  }
  ```

---

### Task 3: Verify MCP server startup

**Files:**
- None

- [ ] **Step 1: Run verification command**
  Test running the MCP server standalone in stdio mode to ensure no module loading issues or setup errors.
  Run: `PYTHONPATH=. /Users/tanue/miniforge3/bin/python3 -m mcp_server.server`
  Wait for: The process to start and wait for JSON-RPC input (no errors printed).
  Then stop the command manually (Ctrl+C).
