# RS-0015：迁移后运行验证与开发接续

| 字段 | 值 |
| --- | --- |
| 状态 | 执行完成，待验收 |
| 优先级 | P0 |
| 负责人 | codex@mac |
| 评审人 | Owner |
| Owner 批准 | 2026-10-26：继续 AI 风格审计与千问系统；迁入当前 PHD-Scholar，确认运行后删除旧 RuScholar |
| 分支 | agent/codex/RS-0015-migration-runtime |
| 关联 | HUB-0016：跨目录迁移与清理 |

## 范围
阅读当前规则、需求、架构、看板及交接；接续已有 CI 开发提交，验证新项目路径、本机 Python、前端、Web/SSE、MCP、真实 Qwen，修复由真实模型存在导致的测试隔离问题。Owner 追加明确可直接使用本机环境，不要求另建 Python 环境。保留既有分支，不合并 main、不推送、不改写历史。

## 验收标准
- [x] 无模型测试与前端 lint/config/build 通过
- [x] 从新路径启动 Web，上传与逐句 SSE 流可用
- [x] MCP stdio 注册与调用可用
- [x] 新路径加载真实 Qwen，取得有效推理与 PPL 结果
- [x] 留存交接，说明运行可用与诊断准确率证据的区别

## 验证记录
Mac 本机 Python 3.13.12：73 passed / 1 deselected，pip check 通过；Node 26：lint、配置 8/8、build 通过。真实 Qwen 完成 PPL 与生成式风格判定，Web 上传与 SSE init/result/done 通过，MCP 17 工具可列出并调用。旧目录删除后独立性复查通过。见最新交接；npm audit 的 1 项开发依赖告警另记，不宣称检测准确率已验证。
