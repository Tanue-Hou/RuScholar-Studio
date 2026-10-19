# TASK-0003：仓库卫生（被跟踪的草稿、许可证、分支）

| 字段 | 值 |
| --- | --- |
| 状态 | 需要 Owner 决策 |
| 优先级 | P0 |
| 负责人 | 未分配 |
| 评审人 | Owner |
| 关联需求 | 技术债 |

## 背景
- `scratch/` 已在 `.gitignore`，但 `scratch/impeccable/`（第三方 skill 的三份拷贝）、`scratch/test*.txt`、`scratch/*.py` 等仍被 git 跟踪，会随公开仓库发布。
- 两份个人博士论文引言草稿曾放在 `docs/superpowers/plans/` 并已提交到公开仓库；2026-10-19 已移到 `scratch/thesis-drafts/`（不再跟踪），但**仍存在于 git 历史中**。
- README 声称 MIT 许可，仓库里没有 `LICENSE` 文件。
- 远端同时存在 `main`、`master`、`feature/style-diagnostics` 三个长期分支，当前工作在 feature 分支上。

## 要做的事（每项都需 Owner 确认）
- [ ] `git rm -r --cached scratch` 并提交
- [ ] 决定是否用 `git filter-repo` 从历史中抹去论文草稿（会改写历史、需要 force push）
- [ ] 添加 `LICENSE`（MIT）
- [ ] 把 feature 分支合入 `main`，删除或归档 `master`，以后 `main` 为唯一主干

## 验收标准
- [ ] `git ls-files scratch` 为空；LICENSE 存在；远端只剩 `main` + 进行中的任务分支

## 验证记录
