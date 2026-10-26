# 开发指南

## 1. 环境

| 依赖 | 版本 | 说明 |
| --- | --- | --- |
| Python | 3.10+（本机验证 3.13.12） | 可直接用已有本机环境；2026-10-26 Owner 选择 `~/miniforge3/bin/python3` |
| Node.js | `^20.19.0` 或 `>=22.12.0` | 当前 Vite 的 engines；本机验证 Node 26.0.0，CI 为 Node 22 |
| spaCy 模型 | `ru_core_news_sm` | **必须**，`setup.sh` 会装；缺失时规则引擎静默降级 |
| llama-cpp-python | 可选 | Apple Silicon 用 `./install_mac.sh` 编译 Metal 版 |
| GGUF 模型 | Qwen3-8B-Q5_K_M | PHD-Scholar 的 `data/models/` 自动发现，不入库 |

```bash
# 在项目目录中检查本机环境；不必另建 Python 环境
"$HOME/miniforge3/bin/python3" -m pip check
PYTHONDONTWRITEBYTECODE=1 "$HOME/miniforge3/bin/python3" -B scripts/check_backend.py
```

本机依赖已满足时直接运行。首次安装可选项目外的虚拟环境，路径由 `VENV_DIR` 指定；依赖、node_modules 与缓存留在 OneDrive 外。`.env` 使用项目根目录已有文件，模型自动从共享数据目录加载。前端检查与构建在临时目录完成，再将 `dist/` 放回 `frontend/dist/`。

## 2. 运行

```bash
# 从 projects/ruscholar-studio 运行；稳定服务不启用热重载
PYTHONDONTWRITEBYTECODE=1 "$HOME/miniforge3/bin/python3" -B -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# MCP（另一个终端或由客户端启动）
PYTHONDONTWRITEBYTECODE=1 "$HOME/miniforge3/bin/python3" -B -m mcp_server.server
```

浏览器打开 `http://127.0.0.1:8000`。开发热重载仍可运行 `python backend/main.py`；保存任意被监控的 Python 文件会中断进行中的 SSE 请求，运行验收应使用上面的稳定启动命令。

## 3. 已知坑（修复前请注意）

| 问题 | 临时规避 | 修复任务 |
| --- | --- | --- |
| ~~`pip install mcp` 会装 2.x~~ | 已在 requirements 中限定 `mcp<2` | RS-0001 ✔ |
| ~~`.env` 不会被自动读取~~ | 现在由 `services/config.py` 自动读取 | RS-0002 ✔ |
| ~~后端 8000、前端代理 6666~~ | 统一为 8000 | RS-0002 ✔ |
| ~~没装 llama-cpp 时测试收集失败~~ | 现在自动跳过 | RS-0001 ✔ |
| 本机环境不可直接跨设备复制使用 | 每台机器选择已有环境或在 OneDrive 外安装依赖 | — |

## 4. 分支与提交

- 主干：`main`（受保护，只通过 PR 合入）
- 任务分支：`agent/<codex|claude|antigravity>/RS-xxxx-<slug>`；Owner 自己的分支：`owner/<slug>`
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
