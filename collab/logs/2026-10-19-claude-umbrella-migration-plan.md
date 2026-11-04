# 会话日志：2026-10-19 claude 大项目迁移方案

- 关联任务：TASK-0012（迁移后改为 HUB-0001…）
- 分支：`feature/style-diagnostics`（未提交）

## 做了什么
- Owner 提出：把 RuScholar、去 AI 味、3000 篇写作 skill、BMSTU 格式检查以及 Windows 上的项目合并为一个大项目，放在 OneDrive，由三个助手协同开发，每一步修改都要写文档。
- 起草 `docs/03-plans/2026-10-19-umbrella-migration-plan.md` 与 `docs/02-design/adr/ADR-0004-umbrella-monorepo.md`（状态：提议），看板新增 TASK-0012。

## 关键决定与理由
- 建议代码走 GitHub 私有 monorepo，OneDrive 只放数据，理由见方案第 2 节。
- 迁移与重构分开：先搬家，再抽共享代码。

## 遗留问题
- 读取 `~/Documents/博士论文管家` 的授权请求超时，盘点表中其余子项目待补。
- Windows 上的项目需要在 Windows 上由助手盘点。

## 更新（11:40）：Owner 决定全部放 OneDrive
- Owner 要求：全部放 OneDrive，但保证两个平台不会同时编辑。
- 方案改为 OneDrive 版，ADR-0004 改为"已接受"；AGENTS.md 新增第 11 条硬性规则（先拿机器锁再写）。
- 新增 `tools/onedrive/`：`session-start.sh/.ps1`、`session-end.sh/.ps1`、`machines.conf`；`.gitignore` 忽略 `ai-collab/machine-lock*.json`。
- 验证：bash 版在临时目录中测了 6 种情况，全部符合预期：抢锁被拒、未提交改动时不许收工、他机不能释放锁、真冲突副本被拦截、`setup-mac.sh` 这类正常文件不误报、同步窗口内锁被抢写时放弃。**PowerShell 版尚未在 Windows 上实测**，列入 HUB-0001 第 0 步试验。
- 修正：冲突副本检测原先按机器 ID 匹配，会误报 `*-mac.*` 这类正常文件；已改为按 OneDrive 实际使用的设备名匹配，需在 machines.conf 中填写。
