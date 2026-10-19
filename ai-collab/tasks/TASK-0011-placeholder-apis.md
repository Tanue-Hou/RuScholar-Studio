# TASK-0011：占位接口立项（/api/polish /format /structure /references）

| 字段 | 值 |
| --- | --- |
| 状态 | 需要 Owner 决策 |
| 优先级 | P3 |
| 负责人 | 未分配 |
| 评审人 | Owner |
| 关联需求 | 待写 REQ |

## 背景
`backend/main.py` 中 4 个接口当前返回 501。MCP 侧已有 `thesis_suggest_revision`、`thesis_audit_vak_gost_compliance` 等能力，但 Web UI 未接入。

## 要做的事
- [ ] Owner 决定哪些要做进 Web UI，每个写一份 REQ
- [ ] 不做的接口直接删除，避免误导

## 验证记录
