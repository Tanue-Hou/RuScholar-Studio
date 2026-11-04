# CI 与本地自动化测试（RS-0004）

## 测试入口

- 后端：用本机独立虚拟环境运行 `python -B scripts/check_backend.py`。自动收集仅限 tests/，真实 GGUF/Metal 用例标 local_model，默认排除。
- 前端：在 OneDrive 外的构建/测试副本执行 `npm ci && npm run lint && npm run test:config && npm run test:api && npm run build`。配置测试默认调用 python3，可用 PYTHON_FOR_TESTS 指定解释器。
- pytest 默认也排除 local_model，避免本机恰有 GGUF 时误触发推理；自动测试不下载私有数据，不把规则/Mock 结果当成真实模型推理验收。

## 依赖唯一来源

| 文件 | 用途 |
| --- | --- |
| requirements-core.txt | 共享 Web/MCP/规则依赖，唯一维护来源 |
| requirements.txt | core + local；旧 Streamlit 仅在 legacy 中保留 |
| requirements-local.txt | 可选 llama-cpp 原生推理依赖 |
| requirements-test.txt | pytest、httpx、pyflakes 与 Ruff 工具，dev/CI 复用 |
| requirements-dev.txt | 完整本机开发环境 |
| requirements-ci.txt | core + test，无本地模型编译或旧界面依赖 |

CI 虚拟环境安装 `pip install -r requirements-ci.txt`，再执行 `pip install --no-deps -e .`、MCP 注册检查、`python -m spacy download ru_core_news_sm`、`pip check` 和后端测试入口。完整模型验证另在有模型的设备上显式运行 `pytest tests/ -m local_model`，不混入日常 CI。

## GitHub Actions

`.github/workflows/ci.yml` 在 main/agent 分支 push、main 的 pull request 或手动触发时运行：

1. Python 3.10/3.12 两个后端 job：干净安装、俄语模型、依赖一致性、无 GGUF 自动测试。
2. Node 22 前端 job：按锁文件安装、严格 lint、TS/Python 配置行为测试、API 取消/引用契约测试、TypeScript/Vite build。
3. Python 历史 lint/格式欠账只报告，不阻断；不自动批量格式化业务代码。前端 lint 必须通过。

工作流只读仓库权限，不持久保存 checkout 凭据，不需要业务密钥。使用 GitHub 官方 [checkout](https://github.com/actions/checkout)、[setup-python](https://github.com/actions/setup-python)、[setup-node](https://github.com/actions/setup-node)。

## 验证边界

- 本机已用两个全新临时环境验证 Python 3.10.20 / 3.12.13，每个 73 passed / 1 deselected；pip check 通过，未安装 llama-cpp。
- spaCy 模型安装使用与工作流一致的官方命令。初次测试收集误入手工 scripts/test_ppl_distribution.py，已用 testpaths=tests 限定真正自动测试，未补装无关手工实验依赖。
- 真正的 GitHub Ubuntu job、远端 PR 检查状态必须等获准推送并运行后确认；本轮没有推送，不宣称远端绿灯。
- Windows/Metal 实机验收仍独立管理。
- 本机全新 npm ci、严格 lint、配置行为 8/8、TypeScript/Vite 构建均通过；原锁文件 7 项依赖告警在既有版本范围内更新后为 0，未使用 force。
- Python 历史 Ruff 欠账为 213 项和 46 个待格式化文件，本轮只报告；后续以小任务逐步治理，不为 CI 一次性改写全部业务代码。

## RS-0016 本地复核（2026-11-04）

Python 3.13.12：111 passed / 1 deselected，pip check 通过。前端 lint、配置 8/8、API 4/4 与构建通过；源码和安装包 MCP 均列出 17 工具并实际调用。此次未重新运行 Python 3.10/3.12 的干净环境矩阵，GitHub CI 仍未运行。旧版依赖零告警记录只代表当时锁文件；本次 npm 官方 bulk audit 仍报告 1 项 moderate（开发依赖 minimatch），未作强制跨主版本替换。详细证据与限制见 [本地审查记录](../../collab/reviews/2026-11-04-RS-0016-local-review.md)。

## 远端已验证（2026-11-04，RS-0017）

Owner 授权发布后，[PR #1](https://github.com/Tanue-Hou/RuScholar-Studio/pull/1) 的 [CI #2](https://github.com/Tanue-Hou/RuScholar-Studio/actions/runs/41823277142) 已通过：Frontend quality、Backend Python 3.10、Backend Python 3.12 全部 success；包含干净依赖安装、MCP 注册、spaCy 安装、pip check、自动测试及前端 lint/config/API/build。此前“远端未运行”描述保留为历史时间点，不代表当前状态。Windows、GGUF 实机和诊断准确率仍是独立验证。
