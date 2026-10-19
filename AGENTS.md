# AGENTS.md — RuScholar Studio（PHD-Scholar 子项目）工作规则

> 本仓库位于 OneDrive 总项目 **PHD-Scholar** 的 `projects/ruscholar-studio/`。
> **全局规则以总项目根目录的 `../../AGENTS.md` 为准**（机器锁、文档要求、私有内容、冲突副本等），请先读它。
> 本文件只补充 RuScholar 特有的内容：目录、命令、本仓库的任务与流程细节。与根目录规则冲突时，以根目录为准。
> `CLAUDE.md`、`GEMINI.md` 指向本文件。维护人（Owner）：Tanue Hou。

## 1. 项目一句话

RuScholar Studio：面向俄语学位论文 / 学术稿件的 **本地优先、证据链可追溯** 的写作质量审计与风格自然化工作台。
后端 FastAPI + SSE，前端 React/Vite，算法层 `naturalization_layer/`（规则 + 本地 GGUF PPL 探针 + LLM/NLI 判定），并以 MCP（stdio）暴露 17 个 `thesis_*` 工具。

## 2. 开工前必读（按顺序，约 10 分钟）

1. `ai-collab/README.md` —— 协作流程、任务认领、交接规则（**必须遵守**）
2. `ai-collab/board.md` —— 当前任务看板，看清谁在做什么
3. `docs/00-overview/project-overview.md` —— 项目现状与模块地图
4. `docs/02-design/architecture.md` —— 架构、数据流、API 与 MCP 工具
5. 你被分配的 `ai-collab/tasks/TASK-xxxx-*.md` 以及其关联的需求 / 设计文档
6. 最近一份 `ai-collab/handoffs/` 交接单

## 3. 目录地图（放东西前先查这里）

| 路径 | 内容 | 规则 |
| --- | --- | --- |
| `backend/` | FastAPI 入口 `main.py`（Web UI 的 HTTP/SSE API） | 只放路由与装配，不写业务算法 |
| `services/` | 业务编排层：诊断流水线、引文审计、报告、共享状态 | Web 与 MCP 共用的逻辑放这里 |
| `naturalization_layer/` | 算法/领域层：规则引擎、PPL、LLM/NLI 判定、RAG、ГОСТ/ВАК | 不依赖 FastAPI/MCP；`rules/`、`calibration/` 为数据资产 |
| `mcp_server/` | MCP stdio 服务（`python -m mcp_server.server`） | 工具只做参数适配，逻辑下沉到 `services/` |
| `frontend/` | React 19 + Vite 8 + TS 前端 | 构建产物 `dist/` 不入库 |
| `tests/` | pytest 测试；`tests/fixtures/` 测试样例文本 | 新功能必须带测试 |
| `scripts/` | 可复用的运维/诊断脚本（安装、模型校验、CLI 诊断） | 一次性脚本不要放这里 |
| `legacy/` | 已被替代、暂不删除的旧实现（Streamlit 版 UI） | 只读，不再维护 |
| `sites/` | 独立静态站点（上游 PhD Thesis Butler 落地页） | 与主程序无代码依赖 |
| `models/` | 旧位置的本地模型目录（git 忽略）；迁移后模型统一放在总项目 `data/models/`，见第 4 节 | 永远不要提交模型文件 |
| `docs/` | 正式项目文档（需求→设计→计划→开发→测试→发布） | 见 `docs/README.md` |
| `ai-collab/` | 多助手协作区：看板、任务卡、交接单、会话日志、评审记录、模板 | 见 `ai-collab/README.md` |
| `scratch/` | 个人草稿、一次性实验脚本（git 忽略） | 不得被产品代码 import |

## 4. 常用命令

```bash
# 环境（首次）
./setup.sh                      # macOS/Linux；Apple Silicon 用 ./install_mac.sh 启用 Metal
python -m spacy download ru_core_news_sm   # 缺它规则引擎会静默降级，测试会失败

# 模型：迁移后放在总项目 data/models/（在 TASK-0002 统一配置前，先用环境变量指过去）
export RUSCHOLAR_MODEL_PATH="$(pwd)/../../data/models/Qwen3-8B-Q5_K_M.gguf"

# 运行
python backend/main.py          # Web UI + API（端口见 docs/04-development/dev-guide.md 的已知问题）
cd frontend && npm run dev      # 前端热更新（vite 代理 /api → 6666）
python -m mcp_server.server     # MCP stdio 服务

# 测试
pytest -q                       # 不需要本地模型；test_llm_judge 需要 llama-cpp-python
cd frontend && npm run lint && npm run build
```

## 5. 硬性规则（违反即打回）

1. **无任务卡不改业务代码**：任何对 `backend/ services/ naturalization_layer/ mcp_server/ frontend/src/` 的改动必须对应一个 `TASK-xxxx`。纯文档/错别字除外。
2. **先认领再动手**：在 `ai-collab/board.md` 把任务改为 `进行中` 并写上你的助手名，避免两个助手同时改同一处。
3. **一个分支一个任务**：分支名 `agent/<codex|claude|antigravity>/TASK-xxxx-<短描述>`，从 `main` 拉出。
4. **提交信息**用 Conventional Commits：`feat|fix|refactor|docs|test|chore(scope): 描述 (TASK-xxxx)`。
5. **必须跑测试**：提交前 `pytest -q` 通过；动前端则 `npm run lint && npm run build` 通过。不能通过时在交接单里写明原因。
6. **会话结束必须留痕**：写 `ai-collab/logs/` 会话日志；任务未完成必须写 `ai-collab/handoffs/` 交接单。
7. **不越界决策**：涉及架构变更、删除文件、改写 git 历史、新增依赖、对外发布，先写 ADR 或在任务卡里标 `需要 Owner 决策`，等批准。
8. **安全**：不提交 `.env`、API Key、模型文件、用户论文原文；不在日志里粘贴密钥。
9. **评审交叉**：实现者不能评审自己的 PR / 改动；由另一位助手或 Owner 评审，记录在 `ai-collab/reviews/`。
10. **语言**：文档与日志用中文；代码标识符、提交信息用英文；面向用户的诊断文案保持现有中/俄双语格式。
11. **OneDrive 单机写入**：按总项目根目录 `AGENTS.md` 第 3 节第 1 条执行：写文件前在**总项目根目录**运行 `tools/onedrive/session-start.sh <agent>`（Windows 用 `.ps1`）拿机器锁，收工运行 `session-end`。锁被另一台电脑持有时只读不写，并告知 Owner；禁止助手自行强制接管。
