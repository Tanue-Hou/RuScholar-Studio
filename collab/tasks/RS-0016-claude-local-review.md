# RS-0016：Claude 三轮修改接入与本地修正

| 字段 | 值 |
| --- | --- |
| 状态 | 已完成，随 RS-0017 合入 main |
| 优先级 | P0 |
| 负责人 | codex@mac |
| 评审人 | Owner |
| Owner 批准 | 2026-11-04：检查 Claude 三轮大改，按照 Claude 的思路进行本地修正 |
| 分支 | agent/codex/RS-0016-claude-local-review |

## 目标与范围
接入远端 claude/sharp-einstein-dmbnvw 的三轮架构改动（依赖/PPL 与降级、服务层整合、打包/MCP/前端拆分），保留 Claude 的设计方向，解决与本地配置、CI、迁移修复的冲突并修正可复现问题。使用本机 Python，依赖及构建缓存位于 OneDrive 外；RS-0016 阶段仅本地提交；Owner 随后在 RS-0017 批准恢复原 UI 后合入/推送。

## 验收标准
- [x] 三轮提交纳入本地任务分支，已有本地迁移和配置修复保留
- [x] 复核服务层、模型/会话/文献生命周期、MCP 与前端行为；问题有复现与修正
- [x] 自动测试、前端 lint/config/build、安装入口检查通过
- [x] 从新目录启动真实 Qwen，Web/SSE 与 MCP 实际调用通过
- [x] 更新交接和验证记录，列出仍无法验证的范围

## 验证记录
- 后端 111 passed / 1 deselected，pip check 通过；前端 lint、配置 8/8、API 4/4、构建通过。
- 源码与 wheel 安装的 MCP 各 17 工具且可调用；输入 schema 与原本地基线一致。
- 真实 Qwen：自写样例 PPL 40.75 / 17.89，Web SSE 完整；浏览器导入、停止、重启、标注与详情走查通过。
- 详见 [审查记录](../reviews/2026-11-04-RS-0016-local-review.md) 与 [交接](../handoffs/2026-11-04-codex-RS0016.md)。
- 云端真实调用、Windows、远端 CI 未验收；开发依赖 minimatch 有 1 项 moderate，诊断准确率仍属 RS-0010。

## 后续验收
2026-11-04 Owner 批准发布，原界面按 RS-0017 恢复。代码已通过 [PR #1](https://github.com/Tanue-Hou/RuScholar-Studio/pull/1) 合入 main（44525aa）；远端三项 CI job 成功，替代上述本轮尚未运行的状态。
