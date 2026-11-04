# ADR-0004：统一大项目 thesis-butler 全部放在 OneDrive，用机器锁保证单机写入

- 状态：已接受（方案方向）；具体名称与盘点待补
- 日期：2026-10-19
- 决策人：Owner

## 背景
AI 率审计（RuScholar）、去 AI 味、科学写作 skill、BMSTU 格式检查等多个同源项目分散在 Mac 与 Windows 上，需要由 Claude / Codex / Antigravity 协同开发，并且所有修改都要留下可见的文档。

## 决策
1. 大项目 `thesis-butler` 与数据区 `data/` 全部放在 OneDrive 的 `ThesisButler/` 下。
2. 同一时间只允许一台电脑写入：用 `tools/onedrive/session-start|end` 机器锁强制执行。
3. git 继续用于历史记录、审查与回滚，并推送到 GitHub 私有仓库作为第二份备份。
4. 虚拟环境、缓存、`node_modules`、`.env` 不放在同步范围内；模型等大文件放 `data/`，代码通过 `THESIS_DATA_ROOT` 读取。
详见 `docs/03-plans/2026-10-19-umbrella-migration-plan.md`。

## 备选方案及放弃原因
- 代码只走 GitHub、各机本地 clone、OneDrive 只放数据：最稳妥，但 Owner 希望所有内容都集中在 OneDrive 中直接可见，故未采用；保留 GitHub 推送作为折中。
- 每个子项目一个仓库，再用 submodule 组合：助手难以跨项目看到文档，操作容易出错。

## 影响
- 所有助手必须先拿锁再写文件（写入 AGENTS.md 硬性规则）。
- 迁移后，本仓库变为 `projects/ruscholar-studio`；`ai-collab/` 与 `tools/onedrive/` 上移到大项目根目录。
