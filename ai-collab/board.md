# 任务看板（唯一事实来源）

> 认领：把状态改为 `进行中`、负责人写你的助手名、填开始日期，然后再动代码。
> 状态：待办 / 进行中 / 待评审 / 已完成 / 阻塞 / 需要 Owner 决策
> 最后更新：2026-10-19 14:05 莫斯科时间（claude，Mac 侧迁移准备）

## 进行中 / 待评审

| 任务 | 标题 | 优先级 | 状态 | 负责人 | 评审人 | 开始 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| — | — | — | — | — | — | — | — |

## 待办 / 待决策（按优先级）

| 任务 | 标题 | 优先级 | 状态 | 建议负责人 | 依赖 |
| --- | --- | --- | --- | --- | --- |
| [TASK-0001](tasks/TASK-0001-pin-dependencies.md) | 修复依赖漂移（mcp<2、spaCy 模型、llama 可选） | P0 | 待办 | codex | — |
| [TASK-0002](tasks/TASK-0002-unify-config.md) | 统一配置（.env 未加载、端口 8000/6666、4B/8B） | P0 | 待办 | codex | 端口需 Owner 定 |
| [TASK-0003](tasks/TASK-0003-repo-hygiene.md) | 仓库卫生（草稿入库、LICENSE、分支收敛） | P0 | 需要 Owner 决策 | — | — |
| [TASK-0004](tasks/TASK-0004-ci-pipeline.md) | GitHub Actions CI | P1 | 待办 | codex | 0001 |
| [TASK-0005](tasks/TASK-0005-refactor-diagnostic-pipeline.md) | 诊断流水线去重重构 | P1 | 待办 | claude 设计 / codex 实现 | 0002 |
| [TASK-0006](tasks/TASK-0006-ppl-performance.md) | PPL 计算向量化提速 | P1 | 待办 | codex | — |
| [TASK-0007](tasks/TASK-0007-frontend-modularize.md) | 前端 App.tsx 拆分 | P1 | 待办 | antigravity | — |
| [TASK-0008](tasks/TASK-0008-mcp-server-split.md) | MCP 服务拆分 + ToolResult 模型 | P2 | 待办 | codex | 0005 |
| [TASK-0009](tasks/TASK-0009-session-and-security.md) | 会话 TTL、CORS、绑定地址、上传限制 | P2 | 待办 | codex | 0002 |
| [TASK-0010](tasks/TASK-0010-evaluation-benchmark.md) | 诊断质量评测集 | P2 | 需要 Owner 决策 | claude | — |
| [TASK-0011](tasks/TASK-0011-placeholder-apis.md) | 501 占位接口立项或删除 | P3 | 需要 Owner 决策 | — | — |
| [TASK-0012](../docs/03-plans/2026-10-19-umbrella-migration-plan.md) | 迁移到统一大项目 **PHD-Scholar**（OneDrive `个人项目/PHD-Scholar`，机器锁，ADR-0004） | P0 | 基本完成：本仓库已迁入 PHD-Scholar/projects/ruscholar-studio 并提交整理（306fa71）；之后由总项目看板 HUB-0002~0005 跟进 | claude | 见 [Mac 准备日志](logs/2026-10-19-claude-mac-migration-prep.md)、总项目 `ai-collab/logs/2026-10-19-claude-mac-rename-and-import.md` |

## 已完成

| 任务 | 标题 | 负责人 | 完成日期 | 记录 |
| --- | --- | --- | --- | --- |
| TASK-0000 | 仓库目录与协作体系规范化 | claude | 2026-10-19 | [日志](logs/2026-10-19-claude-repo-restructure.md) |
