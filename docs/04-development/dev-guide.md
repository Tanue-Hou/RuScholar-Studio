# 开发指南

## 1. 环境

| 依赖 | 版本 | 说明 |
| --- | --- | --- |
| Python | 3.10+（开发机实际为 3.13） | `.venv/` 在项目根目录 |
| Node.js | 20+ | 前端 |
| spaCy 模型 | `ru_core_news_sm` | **必须**，`setup.sh` 会装；缺失时规则引擎静默降级 |
| llama-cpp-python | 可选 | Apple Silicon 用 `./install_mac.sh` 编译 Metal 版 |
| GGUF 模型 | Qwen3-8B-Q5_K_M（约 5.5 GB） | 放 `models/`，不入库 |

```bash
./setup.sh                       # 或 ./install_mac.sh
pip install -r requirements-dev.txt   # 测试依赖（pytest）
cp .env.example .env             # 按需填写
```

## 2. 运行

```bash
source .venv/bin/activate
python backend/main.py                    # 后端 + 托管已构建前端
cd frontend && npm run dev                # 前端热更新
python -m mcp_server.server               # MCP
```

## 3. 已知坑（修复前请注意）

| 问题 | 临时规避 | 修复任务 |
| --- | --- | --- |
| ~~`pip install mcp` 会装 2.x~~ | 已在 requirements 中限定 `mcp<2` | RS-0001 ✔ |
| `.env` 不会被自动读取 | 启动前 `set -a; source .env; set +a` | RS-0002 |
| 后端默认 8000，vite 代理到 6666 | 开发模式下 `RUSCHOLAR_PORT=6666 python backend/main.py` | RS-0002 |
| ~~没装 llama-cpp 时测试收集失败~~ | 现在自动跳过 | RS-0001 ✔ |
| `.venv` 是 macOS 生成的，不能跨机器使用 | 每台机器各自建 venv | — |

## 4. 分支与提交

- 主干：`main`（受保护，只通过 PR 合入）
- 任务分支：`agent/<codex|claude|antigravity>/TASK-xxxx-<slug>`；Owner 自己的分支：`owner/<slug>`
- 提交：Conventional Commits，结尾带任务号，例如 `fix(deps): pin mcp<2 (RS-0001)`
- 一个 PR 只做一个任务；PR 描述链接任务卡与评审记录

## 5. 代码规范

**Python**
- 新代码加类型注解；新的数据结构用 pydantic 模型而不是裸 dict
- 用 `logging` 代替 `print`（存量逐步替换）
- 路径一律从项目根解析，不依赖当前工作目录
- 新增模块放哪：算法 → `naturalization_layer/`；Web 与 MCP 共用的流程 → `services/`；路由 → `backend/`；工具适配 → `mcp_server/`
- 禁止 `sys.path.append` 式导入出现在新代码中（存量脚本除外）

**前端**
- TypeScript 严格模式；API 调用集中在 `src/api/`（RS-0007 后）
- 与后端 SSE 字段的类型定义保持一致（见架构文档第 2 节契约）

**数据资产**
- `rules/*.json`、`calibration/*.json` 修改需在任务卡写明依据，并补回归测试

## 6. 新增依赖流程
在任务卡说明理由 → 写入 `requirements.txt`（带上界）或 `package.json` → 评审时单独确认。
