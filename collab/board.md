# RS 看板（只列未完成）

状态：待办 / 进行中 / 待评审 / 待验收 / 阻塞 / 需要 Owner 决策。认领时把"负责"改成 `助手@机器`。

## P0
| 任务 | 内容 | 状态 | 负责 | 依赖 |
| --- | --- | --- | --- | --- |
| [RS-0013](tasks/RS-0013-baseline.md) | 运行基线：当前提交下后端、前端、MCP 能否启动，测试结果 | 待办 | 建议 codex@mac | — |
| [RS-0001](tasks/RS-0001-pin-dependencies.md) | 依赖漂移（`mcp<2`、spaCy 模型、llama 可选） | 待办 | 建议 codex | — |
| [RS-0002](tasks/RS-0002-unify-config.md) | 统一配置：`.env` 不生效、端口 8000/6666、模型改读 `data/models` | 需要 Owner 决策（端口） | 建议 codex | — |
| [RS-0003](tasks/RS-0003-repo-hygiene.md) | 仓库卫生：被跟踪的 scratch、LICENSE、分支收敛 | 需要 Owner 决策 | — | — |

## P1
| 任务 | 内容 | 状态 | 负责 | 依赖 |
| --- | --- | --- | --- | --- |
| [RS-0004](tasks/RS-0004-ci-pipeline.md) | CI（pytest + 前端 lint/build） | 待办 | 建议 codex | RS-0001 |
| [RS-0005](tasks/RS-0005-refactor-diagnostic-pipeline.md) | 诊断流水线去重 | 待办 | 建议 claude 设计 / codex 实现 | RS-0002 |
| [RS-0006](tasks/RS-0006-ppl-performance.md) | PPL 计算向量化 | 待办 | 建议 codex | — |
| [RS-0007](tasks/RS-0007-frontend-modularize.md) | 前端 App.tsx 拆分 | 待办 | 建议 antigravity | — |

## P2
| 任务 | 内容 | 状态 | 负责 | 依赖 |
| --- | --- | --- | --- | --- |
| [RS-0008](tasks/RS-0008-mcp-server-split.md) | MCP 服务拆分 | 待办 | 建议 codex | RS-0005 |
| [RS-0009](tasks/RS-0009-session-and-security.md) | 会话 TTL、CORS、上传限制 | 待办 | 建议 codex | RS-0002 |
| [RS-0010](tasks/RS-0010-evaluation-benchmark.md) | 诊断质量评测集 | 需要 Owner 决策 | 建议 claude | — |
| [RS-0011](tasks/RS-0011-placeholder-apis.md) | 501 占位接口立项或删除 | 需要 Owner 决策 | — | — |

已完成：RS-0000（仓库整理）、RS-0012（迁入 PHD-Scholar）。旧编号 TASK-00xx 与 RS-00xx 一一对应；旧看板在 `archive/`。
