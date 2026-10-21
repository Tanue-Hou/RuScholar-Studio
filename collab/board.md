# RS 看板（只列未完成）

状态：待办 / 进行中 / 待评审 / 待验收 / 阻塞 / 需要 Owner 决策。认领时把"负责"改成 `助手@机器`。

## P0
| 任务 | 内容 | 状态 | 负责 | 依赖 |
| --- | --- | --- | --- | --- |
| [RS-0001](tasks/RS-0001-pin-dependencies.md) | 依赖漂移（`mcp<2`、pymorphy3、pytest、spaCy 提示） | 待验收（codex 评审通过） | claude@mac / 评审 codex | — |
| [RS-0002](tasks/RS-0002-unify-config.md) | 统一配置：`.env`、端口 **8000**、模型读 `data/models` | 待验收（Codex 按 Owner 授权直接修复并自测） | codex@mac（收尾） | RS-0001 |
| [RS-0014](tasks/RS-0014-purge-thesis-drafts.md) | **论文引言草稿在 GitHub 公开**：演练已通过；需先暂设私有；强推后可申请 GitHub 清缓存（不保证受理），所有设备必须重新克隆；等 Owner 确认 | 需要 Owner 决策 | claude@mac | RS-0001～0003 合并后 |
| [RS-0003](tasks/RS-0003-repo-hygiene.md) | 仓库卫生：scratch 取消跟踪、补 LICENSE；之后以 main 为主干 | 待验收（累计代码已整合并自测） | claude@mac / 收尾 codex | RS-0002 |

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
| [RS-0010](tasks/RS-0010-evaluation-benchmark.md) | 诊断质量评测集（只用公开与自写语料） | 待办（已批准方向） | 建议 claude | — |
| [RS-0011](tasks/RS-0011-placeholder-apis.md) | 删除 4 个 501 占位接口 | 待办（已批准） | 建议 codex | — |

已完成：RS-0000（仓库整理）、RS-0012（迁入 PHD-Scholar）。旧编号 TASK-00xx 与 RS-00xx 一一对应；旧看板在 `archive/`。

当前可继续开发分支：`agent/codex/RS-0002-port-final`，已整合 feature 的最新文档、RS-0001～0003 累积代码和最终端口修复。原任务分支保留；Owner 验收后将此整合分支合入 main，无须再次反复变基和转交评审。RS-0013 待 Owner 验收；RS-0014 仍需单独批准。
