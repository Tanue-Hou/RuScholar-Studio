# RS 看板（只列未完成）

状态：待办 / 进行中 / 待评审 / 待验收 / 阻塞 / 需要 Owner 决策。认领时把"负责"改成 `助手@机器`。

## P0
| 任务 | 内容 | 状态 | 负责 | 依赖 |
| --- | --- | --- | --- | --- |
| [RS-0014](tasks/RS-0014-purge-thesis-drafts.md) | **论文引言草稿在 GitHub 公开**：演练已通过；需先暂设私有；强推后可申请 GitHub 清缓存（不保证受理），所有设备必须重新克隆；等 Owner 确认 | 需要 Owner 决策 | claude@mac | RS-0001～0003 合并后 |

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
| [RS-0011](tasks/RS-0011-placeholder-apis.md) | 删除 4 个 501 占位接口 | 实现及自测完成，待 Owner 验收 | codex@mac | — |

已完成：RS-0000、RS-0012；RS-0001～0003 已按 Owner 本轮定型授权整合入 main。旧编号 TASK-00xx 与 RS-00xx 一一对应；旧看板在 `archive/`。

当前开发主干：`main`；定型代码 `81cb8f4`，配置与本机锁修复已由 Owner 验收。新工作从 main 建任务分支，不再重复提交这些修复评审。RS-0013 的完整平台验证与 RS-0014 的历史清理仍单列。
