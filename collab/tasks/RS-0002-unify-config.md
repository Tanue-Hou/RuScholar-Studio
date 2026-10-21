# RS-0002：统一配置管理（.env、端口、模型名）

| 字段 | 值 |
| --- | --- |
| 状态 | 待验收（Owner 直接授权 Codex 收尾，定向测试通过，不再转交助手评审） |
| 分支 | agent/codex/RS-0002-port-final（整合前序任务分支与 feature 文档） |
| 优先级 | P0 |
| 负责人 | claude@mac（前序）；codex@mac（本轮收尾） |
| 验收人 | Owner（本轮按直接指令修复并自测，不再转交助手评审） |
| 关联需求 | 技术债 |

## 背景
- 代码中没有任何 `load_dotenv()` 调用，`.env` 实际**不会被读取**，只有手动 export 才生效。
- 后端默认端口 8000（`backend/main.py`），`.env` 写 6666，`frontend/vite.config.ts` 代理到 6666，README 写 8000 —— 三处不一致，按 README 启动时前端开发模式连不上后端。
- `services/shared_state.py` 默认 Qwen3-8B，README、`scripts/style_diagnostics.py`、`scripts/manual_test_judge.py` 仍写 Qwen3-4B。
- 规则/校准文件路径在 `backend/main.py` 与 `services/diagnostic_service.py` 各自重复加载。

## 要做的事
- [ ] 新建 `services/config.py`（pydantic-settings 或 python-dotenv）集中读取全部 `RUSCHOLAR_*` 与 `DEEPSEEK_*` 变量
- [ ] 后端、MCP、脚本统一从 config 取值；删除重复的规则/校准加载
- [ ] 端口统一（建议 Owner 决定 8000 还是 6666），vite 代理与 README 同步
- [ ] README 中模型名、下载命令同步到 8B

## 影响范围
`services/shared_state.py`、`backend/main.py`、`services/diagnostic_service.py`、`mcp_server/server.py`、`frontend/vite.config.ts`、`README.md`、`scripts/*`

## 验收标准
- [ ] 只改 `.env` 即可切换端口和模型路径，Web 与 MCP 都生效
- [ ] `pytest -q` 通过

## 验证记录

## Owner 决定（2026-10-21 11:19）
- 端口统一为 **8000**：后端默认、`.env.example`、`frontend/vite.config.ts` 代理、README 一致。
- 实施批准：Owner 授权"先完成现有工作"。

## 验证记录（2026-10-21，claude@mac）
- 新增 `services/config.py`：读取 `.env`（已存在的环境变量优先）、相对路径按项目根目录解析、模型按 环境变量 → `models/` → `../../data/models/`（先 8B 后 4B）查找、端口默认 8000。
- 端口统一 8000（`.env.example`、vite 代理、脚本、文档）；README（中俄英）与脚本中的旧 4B 默认值改为 8B。
- `pytest -q`：61 passed, 1 skipped（新增 6 个配置测试）。
- 端到端：从 `/tmp` 启动后端，找到 `../../data/models` 中的 8B 模型，`/api/check_model` 返回 true；Vite 开发服务器把 `/api` 代理到 8000 成功。

## 评审（codex，2026-10-21）与修复
- 问题 1：前端代理写死 8000，后端读 `.env`（现有 6666）→ 请求失败。修复：`frontend/vite.config.ts` 读取同一份项目根 `.env` 的 `RUSCHOLAR_PORT`（环境变量优先，默认 8000）。
- 问题 2：旧 `.env` 的 `RUSCHOLAR_MODEL_PATH` 指向已不存在的项目内模型，挡住 `data/models` 的查找。修复：配置的文件不存在时警告并改用自动查找到的模型。
- 修复提交 `b212dd5`；新增 3 个测试，共 64 passed / 1 skipped；tsc、vite build 通过。
- 端到端：旧 `.env`（6666 + 失效模型路径）与无 `.env`（8000）两种情况下，后端与 Vite 代理端口一致，`/api/check_model` 均找到 `../../data/models` 中的模型。
- 本机 `.env` 迁移（不在 Git 中）：已按 Owner 决定把 `RUSCHOLAR_PORT` 改为 8000、清空失效的 `RUSCHOLAR_MODEL_PATH`；原文件备份为 `.env.bak-20261021`。

## 第二轮复核（codex）与修复
- 问题（P2）：Vite 的 `loadEnv` 还会读 `.env.local`、`.env.<mode>`，Python 只读 `.env`；复现为代理 9002、后端 6666。
- 修复 `c135686`：`vite.config.ts` 不再用 `loadEnv`，按与 `services/config.py` 相同的规则只读项目根 `.env`（重复的键以第一次为准）；空端口两边都退回 8000。
- 验证：66 passed / 1 skipped；tsc、eslint 通过。端到端：`.env`=6666 + `.env.local`=9002 + `.env.development`=9003 → 两边都是 6666；空端口 → 8000；命令行 `RUSCHOLAR_PORT=7001` → 7001。

## Owner 直接授权收尾（2026-10-21，codex@mac）
- 批准：直接修好剩余锁和端口问题、做好日志及针对性测试，不再反复转交评审。
- 分支 `agent/codex/RS-0002-port-final`：保留 feature 文档并接入 RS-0001～0003 累积提交。
- 空 shell 变量存在时优先于文件，再回退 8000；新增实际 TS/Python 解析器行为测试。
- `npm run test:config`：8 项通过（含空 shell 覆盖、local/mode 忽略等）；累计 `pytest`：68 passed / 1 skipped，退出码 0。使用既有本机环境，临时副本运行；未验证全新安装、Windows、Metal。
- `npm run build`：TypeScript 与 Vite 构建通过，构建产物仅留临时目录。
