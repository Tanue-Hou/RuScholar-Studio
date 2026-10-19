# ADR-0003：仓库目录规范与多助手协作机制

- 状态：已接受
- 日期：2026-10-19
- 决策人：Owner

## 背景
Codex、Claude、Antigravity 同时参与开发，此前文档散落在 `docs/superpowers/`，一次性脚本、旧版 UI、落地页、测试样例混在根目录和代码目录中，助手接手时难以判断哪些是有效代码。

## 决策
1. 根目录 `AGENTS.md` 为所有助手的唯一规则入口；`CLAUDE.md`、`GEMINI.md` 仅引用它。
2. 正式文档按生命周期放 `docs/00-06`；过程记录放 `ai-collab/`（看板、任务卡、交接单、日志、评审）。
3. 采用"需求单 → 设计 → 任务卡 → 分支开发 → 交叉评审 → 合并 → 验收 → CHANGELOG"流程。
4. 旧实现放 `legacy/`，独立站点放 `sites/`，测试样例放 `tests/fixtures/`，一次性脚本与个人草稿放 `scratch/`（不入库）。
5. Python 包目录（backend、services、naturalization_layer、mcp_server）暂不迁入 `src/`，避免破坏现有 import 与 MCP 客户端配置；如需迁移另立 ADR。

## 影响
本次整理只移动了不被代码引用的文件，业务代码零改动；整理前后 `pytest` 结果一致。
