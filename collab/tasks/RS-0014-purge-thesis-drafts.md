# RS-0014：从公开仓库历史中清除论文引言草稿

| 字段 | 值 |
| --- | --- |
| 状态 | 需要 Owner 决策（仅最后的强制推送） |
| 优先级 | P0 |
| 负责人 | claude@mac（准备）；推送由 Owner 确认 |
| 评审人 | Owner |
| Owner 批准 | 待批准（强制推送不可撤销） |

## 背景
`docs/superpowers/plans/纵横垂协同控制论文引言_草稿.md` 与 `_俄文草稿.md`（未发表的博士论文引言）存在于 GitHub 公开仓库 `Tanue-Hou/RuScholar-Studio` 的 main、master、feature/style-diagnostics 分支与全部历史中。

## 方案
1. 在 OneDrive 之外的临时克隆里用 `git filter-repo --invert-paths --path <两份草稿>` 改写全部分支历史；备份原仓库为 bundle。
2. 核对改写后的历史里不再有这两个文件，其余内容一致。
3. **Owner 确认后**强制推送全部分支，并在 GitHub 上提示其他克隆需重新克隆。
4. 草稿原文保留在 `data/private/ruscholar-scratch/thesis-drafts/`。

## 风险
已被他人 fork 或缓存的副本无法收回；推送后所有协作者需重新克隆。

## 验收标准
- [ ] 远端所有分支和历史中不再包含这两个文件
- [ ] 本地 OneDrive 中的仓库与远端一致
