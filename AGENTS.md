# RuScholar Studio（RS）— 助手须知

俄语学位论文的写作质量审计与风格自然化工作台：FastAPI + SSE 后端、React/Vite 前端、算法层 `naturalization_layer/`（规则 + 本地 GGUF 的 PPL + LLM/NLI 判定），并以 MCP 提供 17 个 `thesis_*` 工具。本文件是在 RS 工作时唯一必读的规则文件。

## 开工只读这些
1. 本文件
2. [看板](collab/board.md)
3. 自己的任务卡 `collab/tasks/RS-xxxx-*.md`
4. 该任务最近一份交接单 `collab/handoffs/`（如有）

不要读：其他项目、`../../hub/`、`collab/archive/`、`collab/logs/` 里的旧日志、`scratch/`、`legacy/`。需要背景时再按下面"资料"按需读。

## 全局必知（全文见 ../../AGENTS.md）
- 拿锁：在 PHD-Scholar 根目录运行 `tools/onedrive/session-start.sh RS <助手> RS-xxxx`；收工 `tools/onedrive/session-end.sh RS <助手> --session <会话号>`（会话号开工时打印）。锁在别人手上就只读。
- 一个任务一个分支：`agent/<助手>/RS-xxxx-<描述>`；提交信息带任务号；任务卡上没有 Owner 批准不开工。
- 日志：`collab/logs/YYYY-MM-DD-<助手>@<机器>-RS-xxxx.md`（≤ 25 行，写原因、验证、遗留、提交号）。换人或换设备写 `collab/handoffs/`。
- 不改其他项目；不提交私有内容；看到 OneDrive 冲突副本就停。

## 目录
| 路径 | 内容 |
| --- | --- |
| `backend/` | FastAPI 入口 `main.py`：只放路由与装配 |
| `services/` | 业务编排（诊断流水线、引文审计、报告、共享状态），Web 与 MCP 共用 |
| `naturalization_layer/` | 算法层；`rules/`、`calibration/` 是数据资产 |
| `mcp_server/` | MCP stdio 服务，工具只做参数适配 |
| `frontend/` | React 19 + Vite 8 + TS |
| `tests/` | pytest；样例在 `tests/fixtures/` |
| `scripts/` | 可复用脚本；`legacy/` 旧 Streamlit UI（只读）；`sites/` 落地页 |
| `docs/` | 正式文档（总览、PRD、架构、ADR、路线图、开发与测试指南） |
| `collab/` | 本项目看板、任务、日志、交接、评审 |

## 命令
```bash
# 环境装在 OneDrive 之外
VENV_DIR="$HOME/.venvs/ruscholar" ./setup.sh     # Apple Silicon：INSTALL_LLAMA_METAL=1
python -m spacy download ru_core_news_sm          # 必需，缺了规则引擎会静默降级
# 模型自动从 ../../data/models/ 查找；配置写在项目根目录 .env（参考 .env.example）

python backend/main.py           # 后端 + 已构建前端
cd frontend && npm run dev       # 前端代理读取根 .env；缺省端口 8000
python -m mcp_server.server      # MCP

pytest -q                        # 默认排除真实模型；Mock 测试不依赖 llama-cpp
python -B scripts/check_backend.py # CI 同一入口；排除真实模型，用 requirements-ci.txt 环境即可
cd frontend && npm run lint && npm run build
cd frontend && npm run test:config  # 实际 TS/Python 配置一致性；可设置 PYTHON_FOR_TESTS
```
前后端只读根 `.env`，shell 变量优先，空端口回退 8000。运行依赖与构建缓存放本机，不在 OneDrive 安装；本轮测试/构建使用临时副本与既有本机依赖。

## 数据与私有边界
- 远端是**公开仓库**：`scratch/`、模型、论文原文、`.env` 永不提交。
- 模型在 `../../data/models/`（自动查找），草稿在 `../../data/private/ruscholar-scratch/`。

## Git
- 仓库根：本目录；开发主干 `main`；新工作从 main 建任务分支；旧 feature/master 与任务分支保留供追溯；远端 `Tanue-Hou/RuScholar-Studio`（公开）。
- 当前提交负责人：持有 RS 锁的助手。推送远端需 Owner 批准。

## 资料（需要时再读）
- [当前开发定型基线](docs/00-overview/development-baseline.md)
- [CI 与测试入口](docs/05-testing/ci.md)
- 项目总览与现状评估：`docs/00-overview/project-overview.md`
- 架构、API、SSE 字段契约、MCP 工具：`docs/02-design/architecture.md`
- 开发与测试指南：`docs/04-development/dev-guide.md`、`docs/05-testing/test-strategy.md`
- 路线图：`docs/03-plans/roadmap.md`
