# 博士论文管家：统一大项目迁移方案（OneDrive 版）

> **更新（2026-10-19 14:05）**：项目正式名为 **PHD-Scholar**，根目录是 OneDrive 中的 `个人项目/PHD-Scholar`（Mac：`~/Library/CloudStorage/OneDrive-个人/个人项目/PHD-Scholar`）。下文中的 `ThesisButler/thesis-butler` 一律指它。执行进度见 `ai-collab/logs/2026-10-19-claude-mac-migration-prep.md`。

- 状态：**方案已由 Owner 确定（全部放 OneDrive，两台电脑不同时编辑）**，具体执行待盘点
- 起草：claude，2026-10-19；对应 ADR-0004、看板 TASK-0012
- 范围：Mac 上的 `~/Documents/博士论文管家`、`~/Documents/antigravity/friendly-lavoisier`（RuScholar），以及 Windows 电脑上的相关项目

## 1. 目标

1. 一个大项目 **thesis-butler** 下放多个同源小项目：AI 率/证据链审计（RuScholar）、去 AI 味、3000 篇文章蒸馏出的科学写作 skill、BMSTU 格式检查（多个逆向实现）等。
2. 全部放在 OneDrive，Mac 与 Windows 都能打开同一份项目。
3. **同一时间只有一台电脑在写**，用机器锁脚本强制执行。
4. 每一步修改都有文档记录，所有助手可见，并由脚本和检查兜底。

## 2. OneDrive 中的目录

```
OneDrive/ThesisButler/                     # 文件夹名一律用 ASCII
├── thesis-butler/                         # 大项目（git 仓库；另推送到 GitHub 私有仓库做备份）
│   ├── AGENTS.md  CLAUDE.md  GEMINI.md    # 全局规则
│   ├── README.md  CHANGELOG.md
│   ├── ai-collab/                         # 全局看板、任务、交接、日志、评审、模板
│   │   └── machine-lock.json              # 机器锁（不入 git）
│   ├── docs/                              # 大项目级文档 00–06
│   ├── projects/
│   │   ├── ruscholar-studio/              # AI 率 / 证据链审计
│   │   ├── deai-rewriter/                 # 去 AI 味（名字待定）
│   │   ├── writing-skill/                 # 3000 篇蒸馏写作 skill
│   │   └── bmstu-format-checker/          # BMSTU 格式检查（variants/ 放多个逆向版本）
│   ├── packages/                          # 同源共享代码（迁移完成后再抽）
│   └── tools/
│       ├── onedrive/                      # 机器锁：session-start / session-end（.sh + .ps1）
│       └── bootstrap.sh / bootstrap.ps1   # 每台机器重建本地环境
└── data/                                  # 不进 git 的大文件与私有数据
    ├── models/          # GGUF 模型（两台电脑都设为「始终保留在此设备上」）
    ├── corpora/         # 3000 篇语料（版权材料，仅私用）
    ├── bmstu-samples/   # 格式模板、样本、逆向参考
    ├── thesis/          # 论文草稿
    ├── outputs/<项目>/<日期>/
    └── backups/         # 每周 git bundle
```

代码通过环境变量 `THESIS_DATA_ROOT` 找 `data/`。两台电脑上的 OneDrive 根路径不同，所以每台机器在本机 `.env` 或系统环境变量中各写一次：Mac 一般在 `~/Library/CloudStorage/OneDrive-<账户>/ThesisButler/data`，Windows 一般在 `C:\Users\<用户>\OneDrive\ThesisButler\data`。

## 3. 保证"两台电脑不同时编辑"：机器锁

### 3.1 机制
- 锁文件：`thesis-butler/ai-collab/machine-lock.json`，记录持有锁的机器、助手和时间。它随 OneDrive 同步，但不进 git。
- **开工**：`tools/onedrive/session-start.sh <agent>`（Windows 用 `.ps1`）依次执行：
  1. 扫描 OneDrive 冲突副本（文件名带设备名），有则拒绝开工；
  2. 锁被另一台机器持有则拒绝；
  3. 写入锁，等待 30 秒让 OneDrive 同步，再复核锁仍属于本机，防止两台电脑在同步延迟窗口内同时抢锁；
  4. 显示 git 分支与未提交改动。
- **收工**：`tools/onedrive/session-end.sh [--push]`。有未提交改动就拒绝收工，强制先提交并写好记录；只有锁的持有者能释放锁；可顺带推送到 GitHub 备份。
- **强制接管**：只有当另一台电脑确认已关机或断网，而锁没释放时，Owner 才可加 `--force`。助手不得自行使用。

### 3.2 换电脑的标准动作

| 顺序 | 在哪台 | 动作 |
| --- | --- | --- |
| 1 | 旧电脑 | 所有助手停止写文件 → 提交 → 写会话日志/交接单 → `session-end --push` |
| 2 | 旧电脑 | 等 OneDrive 图标显示「已是最新」再合盖 |
| 3 | 新电脑 | 等 OneDrive 图标显示「已是最新」 |
| 4 | 新电脑 | `session-start <agent>`，读最新交接单后再开工 |

### 3.3 同一台电脑上的多个助手
机器锁只管"哪台电脑"。同一台电脑上 Claude / Codex / Antigravity 之间的分工，仍按看板认领规则：同一文件同一时间只有一个"进行中"任务。

### 3.4 首次配置（每台电脑一次）
1. 设置环境变量 `THESIS_MACHINE`：Mac 写 `mac`，Windows 写 `win`。
2. 在 `tools/onedrive/machines.conf` 中把两台电脑的真实设备名填进去，用于识别冲突副本。
3. git 配置（在仓库内执行）：
   ```
   git config core.filemode false     # Mac/Windows 权限位不同，避免全部显示为已修改
   git config core.autocrlf false     # 换行统一由 .gitattributes 控制
   git config core.fsmonitor false
   git config core.longpaths true     # 仅 Windows
   ```
   并在根目录放 `.gitattributes`：`* text=auto eol=lf`，`*.ps1 text eol=crlf`。

## 4. 不能放进 OneDrive 同步的东西

| 内容 | 处理方式 |
| --- | --- |
| Python 虚拟环境 | 用 `uv`，设置 `UV_PROJECT_ENVIRONMENT` 指向本机不同步目录（如 `~/.venvs/thesis-butler/<项目>`、`C:\venvs\thesis-butler\<项目>`）；`uv sync` 一条命令重建 |
| `__pycache__` | 设置 `PYTHONPYCACHEPREFIX` 指向本机目录（Python 3.8+ 支持） |
| pytest 缓存 | pyproject 中 `addopts = "-p no:cacheprovider"` |
| `node_modules` | OneDrive 不支持排除文件夹。第 0 步先测试"`node_modules` 软链接到本机目录"在两台电脑上是否被 OneDrive 正确忽略；不行就只在做前端时安装、做完删除（`npm ci` 约 1 分钟） |
| `frontend/dist` 等构建产物 | 按需生成，可以同步，但不进 git |
| `.env`（密钥、本机路径） | 每台机器一份，不同步：放在仓库外，例如 `~/.config/thesis-butler/.env`，由 bootstrap 读取 |
| GGUF 模型 | 放 `data/models/`，设为「始终保留在此设备上」，避免按需下载时读取失败 |

## 5. 协作与文档规则（升级 AGENTS.md）

1. **开工必须先拿机器锁，收工必须释放**（新增硬性规则）。
2. 两级 AGENTS.md：根目录放全局规则，`projects/<子项目>/AGENTS.md` 只写差异。
3. 任务编号带项目前缀：`HUB-`（大项目级）、`RS-`（RuScholar）、`DA-`（去 AI 味）、`WS-`（写作 skill）、`BF-`（BMSTU 格式）。现有 TASK-0001~0012 迁移后改为 RS-0001~0011、HUB-0001。
4. 一张总看板，增加"项目"列和"机器"列。
5. "每一步写文档"的机器兜底：
   - `commit-msg` 钩子要求提交信息带任务号；
   - `session-end` 不允许留着未提交改动收工；
   - 提交前检查（pre-commit 钩子）：改了 `projects/` 或 `packages/` 下的代码，但同一次提交没有改 `ai-collab/`（任务卡验证记录或日志），就拒绝提交。
6. git 仍然保留，用于历史、回滚和审查；每次收工 `--push` 到 GitHub 私有仓库，作为 OneDrive 之外的第二份备份。

## 6. 迁移步骤

> 原则：先备份，再复制，验证通过后切换；旧文件夹只改名归档，不删除。

### 第 0 步：盘点与试验（HUB-0001）
- 盘点 Mac 与 Windows 上所有项目，填写下表：

| 项目 | 机器与路径 | git / 远端 | 语言 | 大文件 | 新目录 |
| --- | --- | --- | --- | --- | --- |
| RuScholar Studio | Mac `~/Documents/antigravity/friendly-lavoisier` | 是 / GitHub 公开 | Python + React | models 5.5 GB、scratch 135 MB | `projects/ruscholar-studio` |
| 去 AI 味 | 待盘点 | | | | `projects/deai-rewriter` |
| 科学写作 skill（3000 篇） | 待盘点 | | | 语料 | `projects/writing-skill` |
| BMSTU 格式检查（多个） | 待盘点 | | | 样本 | `projects/bmstu-format-checker` |

- 试验：在 OneDrive 中建一个测试文件夹，两台电脑各验证一次：机器锁脚本、`node_modules` 软链接是否被忽略、中文/长路径、llama.cpp 能否从 OneDrive 路径加载模型。

### 第 1 步：备份（HUB-0002）
- 每个 git 项目：提交现有改动，执行 `git bundle create <名字>-YYYYMMDD.bundle --all`；非 git 项目整体打 zip。备份先放在本机和移动硬盘，**不要只放在 OneDrive**。
- GitHub 新建私有仓库 `thesis-butler`。

### 第 2 步：搭骨架（HUB-0003）
在 OneDrive `ThesisButler/thesis-butler/` 中初始化：AGENTS.md、docs、ai-collab、tools（含已写好的机器锁脚本）、`.gitattributes`、`.gitignore`、`.env.example`；按 3.4 完成 git 配置，首次提交并推送。

### 第 3 步：导入 RuScholar（HUB-0004）
```bash
# 先在 friendly-lavoisier 中提交 2026-10-19 的整理，并推送到公开仓库
cd <OneDrive>/ThesisButler/thesis-butler
git subtree add --prefix=projects/ruscholar-studio git@github.com:Tanue-Hou/RuScholar-Studio.git main
```
- 把 RuScholar 内的 `ai-collab/`、`tools/onedrive/` 上移到大项目根目录，任务改名为 RS-xxxx。
- `models/` 移到 `data/models/`，代码改为从 `THESIS_DATA_ROOT` 读取（并入 RS-0002 统一配置）。
- 大项目私有；需要更新公开仓库时：`git subtree push --prefix=projects/ruscholar-studio <公开仓库> main`。

### 第 4 步：导入其他项目（每个项目一张 HUB 任务卡）
- 已是 git 的项目：用 `git subtree add` 导入，保留历史。
- 非 git 项目：复制源码，排除 `.venv`、`node_modules`、`__pycache__`、模型、输出，然后提交。
- Windows 上的项目：在 Windows 上取得机器锁后，直接把源码复制进 OneDrive 中的 `projects/<名字>/`，然后提交。
- 大文件移入 `data/`，硬编码路径改为读取 `THESIS_DATA_ROOT`。
- 每个子项目补齐 README、子项目 AGENTS.md、测试基线。

### 第 5 步：双机验证与切换（HUB-0010）
1. Mac 上：拿锁 → bootstrap → 各项目测试通过 → 收工。
2. Windows 上：等同步完成 → 拿锁 → bootstrap → 各项目测试通过 → 收工。
3. 更新两台电脑上的 MCP 客户端配置路径：Claude Desktop、Antigravity `~/.gemini/config/mcp_config.json`、Codex。Claude 桌面应用中连接的文件夹也改为 OneDrive 下的新路径。
4. 旧文件夹改名为 `_archived_20261019_<名字>`，保留两周后由 Owner 决定是否删除。

### 第 6 步：抽取同源代码
迁移完成后，再把重复部分（俄语分句与规则、docx 解析、LLM 客户端、BMSTU 规则数据）逐个抽到 `packages/`。每抽一个开一张任务卡，并写 ADR。

## 7. 剩余风险与应对

| 风险 | 应对 |
| --- | --- |
| OneDrive 暂停同步或离线时开工，锁没传到另一台电脑 | 开工前确认 OneDrive「已是最新」；脚本复核等待可通过 `THESIS_LOCK_SETTLE_SECONDS` 加长 |
| 锁持有电脑没收工就合盖或断网 | 另一台电脑拒绝开工；Owner 确认后 `--force` 接管，并检查冲突副本 |
| OneDrive 产生冲突副本 | `session-start` 会拦截；由 Owner 对比后保留正确版本，并删除副本 |
| `.git` 内部文件同步不完整 | 每次收工 `--push` 到 GitHub；发现异常时从 GitHub 重新 clone 覆盖 |
| 同步大量小文件变慢 | 环境和缓存不放进 OneDrive（第 4 节） |

## 8. 需要 Owner 决定 / 提供

1. 大项目和各子项目的正式英文名（目录名用 ASCII）。
2. 两台电脑的设备名，填进 `tools/onedrive/machines.conf`。
3. 授权助手读取 Mac 上的 `~/Documents/博士论文管家`；在 Windows 上让一个助手做同样的盘点。
4. 确认 3000 篇语料与 BMSTU 样本只放 `data/`，永不进 git。
