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

## 演练记录（2026-10-21，claude@mac，云端临时副本，未推送、未改动真实仓库）
- `git filter-repo --invert-paths` 去掉两份草稿：清除前有 2 个提交含草稿，清除后所有分支与历史中 0 处；提交数不变（63）；feature 最新提交的文件树与清除前完全一致。
- 真正执行时需在合并 RS-0001～0003 之后、对**全部分支**（含 main、master、feature 与任务分支）一次完成，并先备份 bundle；所有提交号会改变。
- 等 Owner 一句"确认清除并强制推送"后执行。推送需要 GitHub 写权限（在 Mac 本机终端或有凭据的环境中进行）。

## 评审补充：强推之外必须处理的边界（codex 2026-10-21；依据 GitHub 官方文档 Removing sensitive data from a repository）
- 改写历史只影响本仓库的分支。**已有的其他克隆、fork 不会被清除**；fork 的内容需要 fork 所有者处理或向 GitHub 申请。
- GitHub 上的**缓存视图、已关闭或打开的 PR 引用的旧提交**仍可能被访问：执行后需要联系 GitHub Support 清除缓存与 PR 引用。
- 改写后所有协作者（含其他设备上的克隆、Windows 端）必须重新克隆或硬重置，否则旧历史可能被再次推回。
- 内容一旦公开就应视为可能已被复制，清除只能降低继续传播的风险。
- 执行前建议先把仓库暂时设为私有，执行与清理完成后再决定是否恢复公开。
- 执行步骤更新为：① 仓库暂设私有（Owner 在 GitHub 操作）→ ② 备份 bundle → ③ filter-repo 全分支 → ④ 核验 → ⑤ Owner 确认后强推 → ⑥ 联系 GitHub Support 清缓存与 PR 引用 → ⑦ 所有设备重新克隆 → ⑧ 视情况恢复公开。
