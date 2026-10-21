# RS-0011：占位接口立项（/api/polish /format /structure /references）

| 字段 | 值 |
| --- | --- |
| 状态 | 待 Owner 验收（实现与自测完成，不转交助手评审） |
| 优先级 | P2 |
| 负责人 | codex@mac |
| 验收人 | Owner（本轮按授权实现并自测，不再转交助手评审） |
| 分支 | agent/codex/RS-0011-remove-placeholders |
| Owner 批准 | 2026-10-21：此前批准删除四个占位接口；本轮授权继续开发，沿用已有批准 |
| 关联需求 | 待写 REQ |

## 背景
`backend/main.py` 中 4 个接口当前返回 501。MCP 侧已有 `thesis_suggest_revision`、`thesis_audit_vak_gost_compliance` 等能力，但 Web UI 未接入。

## 要做的事
- [x] 删除四个只返回 501 的路由，OpenAPI 不再公开这些能力。
- [x] 核对前端无调用；保留诊断、模型状态与参考文献上传接口。
- [x] 更新当前 PRD/API 说明；新增路由行为回归并运行应用测试。

## 验证记录

## 决定（2026-10-21，Owner 授权 claude 判断）
- 删除 4 个返回 501 的占位接口（`/api/polish`、`/api/references`、`/api/format`、`/api/structure`），避免误导；这些能力今后以 REQ 形式重新立项。P2。

## 本轮范围
- backend/main.py、API 行为测试、PRD/architecture、任务卡/看板与会话日志。
- 不改诊断算法、MCP 工具、SSE 契约或历史私有数据；不新增依赖。
- 从已定型 main（8362afd）开发；新增工作先提交任务分支，不把既有验收冒充为新增任务验收。

## 验证结果（2026-10-21）
- `tests/test_http_api_surface.py` 新增 5 项，验证四路由不在 OpenAPI、HTTP 不再提供占位能力，原有七个 API 契约及模型状态响应保留。
- 临时副本运行全量 pytest：73 passed / 1 skipped / 1 个环境测试客户端弃用提醒，退出码 0；无模型加载/下载，不新增依赖。
- main 保持已验收基线 8362afd；本任务实现提交在独立分支，提交号由本日志 Git 历史追溯。
