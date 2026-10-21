# RS-0002：统一配置管理（.env、端口、模型名）

| 字段 | 值 |
| --- | --- |
| 状态 | 待办（已批准） |
| 优先级 | P0 |
| 负责人 | 未分配（建议 codex） |
| 评审人 | claude |
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
