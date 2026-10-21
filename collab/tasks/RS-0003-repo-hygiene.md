# RS-0003：仓库卫生（被跟踪的草稿、许可证、分支）

| 字段 | 值 |
| --- | --- |
| 状态 | 待验收（累计代码已整合至 Codex 收尾分支，68 项 pytest 通过） |
| 分支 | agent/claude/RS-0003-repo-hygiene（3fe6d5a，基于 RS-0002 最新） |
| 优先级 | P0 |
| 负责人 | claude@mac |
| 评审人 | codex（2026-10-21：当前版本合理，依赖前序，暂缓合并） |
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

## 决定（2026-10-21，Owner 授权 claude 判断）
1. `git rm -r --cached scratch`：**做**（可回退，scratch 已在 .gitignore）。
2. 添加 MIT `LICENSE`：**做**（README 已声明 MIT，补齐文件）。
3. 分支收敛：**以 `main` 为唯一主干**。核实结果：`main`、`master`、`origin/*` 都停在 `078365e`，没有独有提交；`feature/style-diagnostics` 领先。RS-0001/0002 验收后把 feature 快进合并到 `main`；`master` 在下次推送时删除远端分支（推送需 Owner 确认）。
4. **论文引言草稿已在 GitHub 公开**（`origin/main`、`origin/master`、`origin/feature/style-diagnostics` 都含 `docs/superpowers/plans/纵横垂协同控制论文引言_*.md`）。判断：应从历史中清除，避免未发表论文文本公开、日后查重误判。改写历史并强制推送不可撤销，另立 RS-0014，由 claude 准备、**Owner 确认后才推送**。

## 验证记录（2026-10-21，claude@mac）
- 第 1 项：`git rm --cached` 5 个 scratch 条目（文件仍在磁盘，私有副本在 `../../data/private/ruscholar-scratch/`）。第 2 项：新增 MIT `LICENSE`。`pytest -q`：61 passed, 1 skipped。
- 第 3 项（以 main 为主干）：等 RS-0001～0003 验收后，把 feature 与三个任务分支依次快进合并到 `main`；第 4 项见 RS-0014。

## 评审（codex，2026-10-21）
- 清理合理；依赖 RS-0001/0002，暂缓合并。注意：本任务**不**清除历史中的论文草稿（见 RS-0014）。
