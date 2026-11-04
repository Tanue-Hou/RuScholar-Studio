# RS-0004：建立 CI（GitHub Actions）

| 字段 | 值 |
| --- | --- |
| 状态 | 本地实现与验证完成；远端待首次运行 |
| 优先级 | P1 |
| 负责人 | codex@mac |
| 验收人 | Owner（本轮不反复转交助手评审） |
| Owner 批准 | 2026-10-21：继续推进 CI 和自动化测试，含任务列明的开发检查 |
| 分支 | agent/codex/RS-0004-ci |
| 关联需求 | 技术债 |

## 要做的事
- [x] `.github/workflows/ci.yml`：Python 3.10/3.12 矩阵，安装依赖 + spaCy 模型，跑 `pytest -q`（不下载 GGUF 模型）
- [x] 前端 job：`npm ci && npm run lint && npm run build`
- [x] 加 ruff（lint + format 检查），先只报告不阻断

## 验收标准
- [ ] PR 上自动出现两个绿色检查

## 验证记录

## 本轮实施（2026-10-21）
- 工作流：Python 3.10/3.12、Node 22；后端无 GGUF 测试，前端严格 lint/配置测试/build；只读权限，不使用业务密钥。
- core/test/完整运行依赖单独维护，dev/CI 通过 -r 复用；不复制版本约束。Mock 测试不再依赖 llama-cpp，真实模型显式标记并默认排除。
- 新增 scripts/check_backend.py 与 pytest 收集范围；前端既有 any 类型改为 LucideIcon，解除原 lint 阻断。
- CI 新安装发现前端 7 项告警；在原有版本范围内更新锁文件，未使用 force，锁文件审计已归零；安装后完整回归。
- 本地两个全新 Python 环境均 73 passed / 1 deselected，pip check 通过；完整测试不含私有文档/模型。
- Ruff 报告历史 213 项与 46 个格式待整理文件，保持非阻断，不批量改业务代码。
- 远端 GitHub/Ubuntu 检查须获准推送后验证，本轮没有推送，不能将本地通过冒充 PR 绿灯。

- 前端更新后的锁文件 npm ci 成功且 audit=0；严格 lint、配置行为 8/8、TypeScript/Vite build 均通过。本机 Node 26，工作流 Node 22 实际远端运行仍待验证。
