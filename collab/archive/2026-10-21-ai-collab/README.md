# ai-collab — 多助手协作区

> 本目录是 RuScholar 子项目的协作区（看板、TASK 任务卡、日志）。总项目级的协作协议、HUB 任务、机器锁见 PHD-Scholar 根目录的 `ai-collab/README.md` 与 `AGENTS.md`；冲突时以根目录为准。

Codex、Claude、Antigravity 三个助手在同一仓库协作时的"工位"。正式产品文档在 `docs/`，这里放**过程性记录**：谁在做什么、做到哪、交给谁。

```
ai-collab/
├── README.md        # 本文件：协作协议
├── board.md         # 任务看板（唯一事实来源）
├── tasks/           # 任务卡 TASK-xxxx-<slug>.md
├── handoffs/        # 交接单 YYYY-MM-DD-<from>-to-<to>-TASK-xxxx.md
├── logs/            # 会话日志 YYYY-MM-DD-<agent>-<topic>.md
├── reviews/         # 评审记录 REVIEW-TASK-xxxx-<reviewer>.md
└── templates/       # 所有模板
```

## 1. 角色

| 角色 | 由谁担任 | 职责 |
| --- | --- | --- |
| Owner（产品负责人 / 审批人） | 用户本人 | 提需求、定优先级、批准设计与需要决策的事项、最终验收 |
| 架构 / 需求分析 / 评审（建议） | Claude | 把需求写成 REQ 与设计、拆任务卡、做代码评审 |
| 实现 / 单元测试（建议） | Codex | 按任务卡实现后端与算法改动、补测试 |
| 前端 / 端到端验证（建议） | Antigravity | 前端改动、浏览器端到端走查、截图验证 |

分工只是默认建议，Owner 可在任务卡里指派任何助手做任何任务。

## 2. 标准流程（对应大厂研发流程）

```
需求提出 → 需求评审 → 技术设计 → 任务拆分 → 开发 → 自测 → 代码评审 → 合并 → 验收 → 发布/记录
  REQ        Owner批准     spec/ADR      TASK      分支     pytest/lint   reviews/     main     Owner    CHANGELOG
```

| 阶段 | 产出物 | 存放位置 | 谁做 | 出口条件 |
| --- | --- | --- | --- | --- |
| 1 需求提出 | 需求单 REQ-xxxx | `docs/01-requirements/requests/` | Owner 口述，助手整理 | 用模板写清背景、目标、验收标准 |
| 2 需求评审 | 需求单状态 → `已批准` | 同上 | Owner | Owner 明确批准 |
| 3 技术设计 | 设计文档（小改动可省略）/ ADR | `docs/02-design/specs/`、`docs/02-design/adr/` | 架构助手 | 涉及接口、数据结构、依赖变更时必须有 |
| 4 任务拆分 | 任务卡 TASK-xxxx，登记到看板 | `ai-collab/tasks/`、`board.md` | 架构助手 | 每张卡 ≤ 1 天工作量，可独立验收 |
| 5 开发 | 分支 + 提交 | `agent/<agent>/TASK-xxxx-*` | 实现助手 | 满足任务卡的完成定义 |
| 6 自测 | 测试结果写进任务卡 | 任务卡"验证记录" | 实现助手 | `pytest -q` 通过；前端 lint+build 通过 |
| 7 代码评审 | 评审记录 | `ai-collab/reviews/` | 非实现者 | 结论 `通过` 或 `修改后通过` |
| 8 合并 | PR 合入 `main` | GitHub | Owner 或被授权助手 | 评审通过 |
| 9 验收 | 任务卡状态 → `已完成` | 看板 | Owner | 对照需求验收标准 |
| 10 记录 | CHANGELOG / 会话日志 | `CHANGELOG.md`、`logs/` | 完成任务的助手 | 用户可见的变化都要进 CHANGELOG |

小修（文档、错别字、注释）可以跳过 1–4，直接开一张任务卡做完。

## 3. 编号规则

- 需求：`REQ-0001` 起，按提出顺序递增
- 任务：`TASK-0001` 起，看板上登记后编号即占用，不复用
- 决策：`ADR-0001` 起
- 新建编号前先看看板/目录里最大的编号，+1

## 4. 任务状态

`待办` → `进行中` → `待评审` → `已完成`；另有 `阻塞`（写明卡在哪）和 `需要 Owner 决策`。

## 5. 认领与并发规则（防止助手互相踩）

1. 动手前在 `board.md` 修改该任务行：状态 `进行中`、负责人写自己、开始日期。
2. 同一文件同一时间只允许一个"进行中"任务修改；任务卡的"影响范围"写明会动哪些文件，认领前检查冲突。
3. 发现别的助手留下的未提交改动：不要覆盖，不要回滚，写进交接单问 Owner。
4. 超过一个会话没完成：必须写交接单，状态保持 `进行中` 或改为 `阻塞`。

## 6. 会话开始 / 结束检查清单

**开始**：读 `AGENTS.md` → 读 `board.md` → 读最近的交接单和自己任务卡 → `git status` 确认工作区干净、所在分支正确。

**结束**：
- [ ] 测试结果写入任务卡"验证记录"
- [ ] 更新 `board.md` 状态
- [ ] 写会话日志 `logs/YYYY-MM-DD-<agent>-<topic>.md`
- [ ] 未完成则写交接单 `handoffs/`
- [ ] 用户可见的变化加到 `CHANGELOG.md` 的 Unreleased

## 7. 完成定义（Definition of Done）

- 满足任务卡全部验收标准
- 新增/修改逻辑有测试覆盖，`pytest -q` 通过
- 不新增未说明的依赖；新增依赖已写入 `requirements.txt` / `package.json` 且有版本上界
- 相关文档（架构、API 表、README 命令）已同步
- 评审记录存在且结论为通过
