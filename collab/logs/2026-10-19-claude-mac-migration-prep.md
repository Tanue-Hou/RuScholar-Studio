# Mac 电脑项目盘点与迁移准备（2026-10-19，claude）

> 对应 Windows 侧文档 `claude/windows-inventory-2026-10-19.md`。项目正式名：**PHD-Scholar**。
> 本次 Mac 侧**没有向 OneDrive 写入任何文件**：Windows 正在迁移，遵守"同一时间只有一台电脑写"。

## 1. OneDrive 状态（Mac，莫斯科时间 14:05）
- Mac 路径：`~/Library/CloudStorage/OneDrive-个人/个人项目/PHD-Scholar`
- 文件夹已存在，但在 Mac 上**仍是空的**：Windows 写入的内容还没同步过来，也看不到 Windows 的机器锁。
- 注意：上层路径含中文（`OneDrive-个人/个人项目`）。PHD-Scholar 内部请只用 ASCII 文件夹名，并在两台电脑上分别验证 llama.cpp、Ghidra 能否从该路径读取文件。

## 2. Mac 项目清单

| 项目 | Mac 位置 | Git | 内容与大小 | 迁移去向 |
| --- | --- | --- | --- | --- |
| RuScholar Studio（**最新版，以此为准**） | `~/Documents/antigravity/friendly-lavoisier` | `Tanue-Hou/RuScholar-Studio`，分支 `feature/style-diagnostics`，HEAD `078365e`；今天的整理（AGENTS.md、ai-collab、docs 00–06、tools/onedrive 机器锁脚本）**尚未提交** | 源码含 .git 7.5 MB | `projects/ruscholar-studio/` |
| └ 本地模型 | `.../friendly-lavoisier/models/Qwen3-8B-Q5_K_M.gguf` | 不入库 | 5.85 GB | `data/models/` |
| └ scratch（个人草稿、论文引言草稿、一次性脚本、impeccable 副本，内含一个嵌套 .git） | `.../friendly-lavoisier/scratch/` | 已 gitignore（部分历史文件仍被跟踪，见 RS 任务 TASK-0003） | 137 MB | `data/private/ruscholar-scratch/`（私有，不进任何仓库） |
| TestVkr 逆向导出（Mac 版，6 月 15–16 日） | `~/Documents/博士论文管家/analysis_TestVkr`、`analysis_TestVkr_2` | 无 | 字符串表、函数摘要、反汇编、PE 资源 .bin；26 MB + 4.6 MB | `projects/bmstu-format-checker/archive/mac-2026-06/`（含原程序资源，私有） |
| 「博士论文管家」根目录的 `.git` | `~/Documents/博士论文管家/.git` | 没有任何提交，只有 `refs/codex/turn-diffs` | 444 MB，Codex 改动快照 | **不迁移** |

去 AI 味项目、3000 篇写作 skill 在 Mac 上**未发现**（写作 skill 在 Windows：`D:\Hermes\01_Active_Projects\PhD_Thesis_Butler`）。Mac 其他目录（如 `~/superpowers-project`、`~/Supervisor-Skills`、`~/ZCodeProject`）未扫描，需 Owner 确认是否相关。

## 3. 已完成的准备
1. **备份（OneDrive 之外）**：`~/Documents/博士论文管家/_migration/backups/ruscholar-studio-mac-20261019.tar.gz`（114 MB，含 .git 与未提交改动；不含 .venv、node_modules、模型、dist）。
2. **迁移脚本**：`~/Documents/博士论文管家/_migration/mac-migrate.sh`
   - 默认只演练；`--apply` 时要求 `PHD-Scholar/ai-collab/machine-lock.json` 的 holder 为 `mac`，否则拒绝；目标子目录非空时拒绝，避免覆盖 Windows 侧内容。
   - 只复制、不删除源文件；目标子目录可用环境变量覆盖，以对齐 Windows 侧建好的结构。
   - 已在临时目录演练：4 个步骤的数量和大小如上表；锁在 win 手上时正确拒绝。

## 4. 请 Windows 侧会话配合（对齐事项）
1. **机器锁格式**：请在 `PHD-Scholar/ai-collab/machine-lock.json` 写入并维护：
   `{"holder": "win", "agent": "claude", "since": "<UTC ISO 时间>"}`；完成后改为 `{"holder": null, "released_by": "win", "released_at": "<UTC>"}`。
   正式的 `session-start/end`（.sh + .ps1）在 Mac 版 RuScholar 的 `tools/onedrive/` 中，Mac 拿到锁后会把它们放到 PHD-Scholar 根目录 `tools/onedrive/`。
2. **目录结构**：Mac 侧默认导入到 `projects/ruscholar-studio/`、`projects/bmstu-format-checker/archive/mac-2026-06/`、`data/models/`、`data/private/ruscholar-scratch/`。如果 Windows 侧用了别的名字，请在交接单里写明。
3. **根目录协作文件**：Mac 版 RuScholar 已有一套完整的 AGENTS.md / ai-collab / docs 规范。建议 Mac 导入后把它提升为 PHD-Scholar 根目录规范；如果 Windows 侧已建立根目录 AGENTS.md，则由下一个拿锁的会话合并。
4. **Windows 上的 RuScholar 旧副本**（6 月 `05aa00f`）不要导入 `projects/ruscholar-studio/`，以免与 Mac 新版冲突。
5. Windows 完成后：释放锁，并在 `PHD-Scholar/ai-collab/handoffs/` 写交接单（已建哪些目录、还缺什么）。

## 5. Mac 侧执行顺序（等 Windows 释放锁后）
1. Mac 上的 OneDrive 显示"已是最新"，并能看到 Windows 写入的内容与已释放的锁。
2. 读 Windows 交接单，必要时用环境变量调整目标目录。
3. 拿锁（写 `holder: mac`），`bash mac-migrate.sh <PHD-Scholar> ` 再演练一次，然后加 `--apply`。
4. 在 `projects/ruscholar-studio` 中 `git status`，确认与迁移前一致后提交今天的整理（RS TASK-0000 / TASK-0012）。
5. 把 `tools/onedrive/` 放到 PHD-Scholar 根目录，合并根目录 AGENTS.md / ai-collab。
6. 写会话日志 → 释放锁。
7. 旧位置保留不动两周（只读），之后由 Owner 决定。

## 6. 需要 Owner 提供
- Mac 的设备名（系统设置 → 通用 → 关于本机 → 名称），用于识别 OneDrive 冲突副本；Windows 设备名已知为 `tanue`。
- 去 AI 味项目在哪台电脑的哪个位置？
- 正式名拼写确认：`PHD-Scholar`（不是 Scholar）？
