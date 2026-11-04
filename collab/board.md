# RS 看板（只列未完成）

状态：待办 / 进行中 / 待评审 / 待验收 / 阻塞 / 需要 Owner 决策。认领时把"负责"改成 `助手@机器`。

## P0
| 任务 | 内容 | 状态 | 负责 | 依赖 |
| --- | --- | --- | --- | --- |
| [RS-0015](tasks/RS-0015-migration-runtime.md) | 迁移后 Web/MCP/真实 Qwen 运行验证 | 执行完成，待验收 | codex@mac | 旧目录已删除；新目录删除后复查通过 |
| [RS-0014](tasks/RS-0014-purge-thesis-drafts.md) | **论文引言草稿在 GitHub 公开**：演练已通过；需先暂设私有；强推后可申请 GitHub 清缓存（不保证受理），所有设备必须重新克隆；等 Owner 确认 | 需要 Owner 决策 | claude@mac | RS-0001～0003 合并后 |

## P1
| 任务 | 内容 | 状态 | 负责 | 依赖 |
| --- | --- | --- | --- | --- |
| [RS-0005](tasks/RS-0005-refactor-diagnostic-pipeline.md) | 诊断流水线去重 | 待办 | 建议 claude 设计 / codex 实现 | RS-0002 |
| [RS-0006](tasks/RS-0006-ppl-performance.md) | PPL 计算向量化 | 待办 | 建议 codex | — |
| [RS-0007](tasks/RS-0007-frontend-modularize.md) | 前端 App.tsx 拆分 | 待办 | 建议 antigravity | — |
| [RS-0018](tasks/RS-0018-ui-refine.md) | 原界面去 AI 味、补充学科阈值/困惑度分布/词法汇总等信息 | 待验收 | claude@cloud | RS-0017 |

## P2
| 任务 | 内容 | 状态 | 负责 | 依赖 |
| --- | --- | --- | --- | --- |
| [RS-0008](tasks/RS-0008-mcp-server-split.md) | MCP 服务拆分 | 待办 | 建议 codex | RS-0005 |
| [RS-0009](tasks/RS-0009-session-and-security.md) | 会话 TTL、CORS、上传限制 | 待办 | 建议 codex | RS-0002 |
| [RS-0010](tasks/RS-0010-evaluation-benchmark.md) | 诊断质量评测集（只用公开与自写语料） | 待办（已批准方向） | 建议 claude | — |

已完成：RS-0000、RS-0012、RS-0004、RS-0016、RS-0017；RS-0001～0003 与 RS-0011 已获 Owner 验收并合入 main。旧编号 TASK-00xx 与 RS-00xx 一一对应；旧看板在 `archive/`。

当前开发主干：`main`；定型代码已包含 `c7af83c`（RS-0011），配置与本机锁修复已由 Owner 验收。新工作从 main 建任务分支，不再重复提交这些修复评审。RS-0013 的完整平台验证与 RS-0014 的历史清理仍单列。

2026-11-04 发布更新：RS-0016 后端整合及 RS-0017 原界面适配已通过 PR #1 合入 main（44525aa），远端前端/Python 3.10/3.12 三个 CI job 成功。当前以恢复后的深色玻璃双栏界面为准；旧迁移与历史基线记录保留用于追溯。
