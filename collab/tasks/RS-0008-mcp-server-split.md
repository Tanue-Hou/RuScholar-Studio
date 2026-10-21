# RS-0008：拆分 MCP 服务（1195 行）并统一返回结构

| 字段 | 值 |
| --- | --- |
| 状态 | 待办 |
| 优先级 | P2 |
| 负责人 | 未分配 |
| 评审人 | claude |
| 关联需求 | 可维护性 |

## 背景
`mcp_server/server.py` 同时包含"兼容旧签名的函数"和 `@mcp.tool()` 包装、工作流路由关键词表、ВАК/ГОСТ 合规逻辑（~160 行在工具函数里）。

## 要做的事
- [ ] 拆为 `mcp_server/tools/{workflow,manuscript,citations,references,model,compliance}.py`
- [ ] 合规与路由逻辑下沉到 `services/`
- [ ] 17 个工具目前都手写返回 `{summary, findings, evidence, next_actions}` 字典：抽成一个 pydantic `ToolResult` 模型，并加契约测试防止后续漂移

## 验收标准
- [ ] 17 个工具名称与参数不变；`tests/test_services_and_mcp.py` 通过

## 验证记录
