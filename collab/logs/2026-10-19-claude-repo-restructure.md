# 会话日志：2026-10-19 claude 仓库规范化与协作体系搭建

- 关联任务：TASK-0000（Owner 直接指派）
- 分支：`feature/style-diagnostics`（未提交，改动留在工作区由 Owner 审阅后提交）

## 做了什么
1. 通读全部源码（backend、services、naturalization_layer、mcp_server、frontend/src、scripts、tests、docs），在全新 venv 中跑测试建立基线。
2. 文件归位（只用 mv，未删除任何文件，未改任何业务代码）：
   - `docs/superpowers/{specs,plans}` → `docs/02-design/specs/`、`docs/03-plans/`
   - `scripts/web_app.py` → `legacy/streamlit_web_app.py`
   - `backend/test_judge.py` → `scripts/manual_test_judge.py`
   - `test_input.txt` → `tests/fixtures/sample_ru_sentences.txt`（同步改了 `scratch/test_real_sentences.py` 中的路径）
   - `phd-thesis-butler-landing/` → `sites/`
   - 两份论文引言草稿 → `scratch/thesis-drafts/`；`frontend/rewrite_app.py` → `scratch/archive/`
3. 新建：`AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、`CHANGELOG.md`、`ai-collab/` 全套、`docs/00–06` 全套文档、ADR-0001~0003、11 张任务卡。
4. README 顶部加了"项目文档与协作"入口链接（其余内容未改）。

## 关键决定与理由
- **不把 Python 包迁入 `src/`**：会破坏现有 import、MCP 客户端的 `cwd`/`-m mcp_server.server` 配置和用户已部署的 Antigravity MCP 配置，收益小于风险（ADR-0003 第 5 条）。
- **脚本不移入 scripts 子目录**：现有脚本用 `dirname(dirname(__file__))` 计算项目根，移入子目录会失效。
- **发现的问题只建任务卡，不顺手修**：遵守"无任务卡不改业务代码"。

## 验证
- 整理前：`pytest -q --ignore=tests/test_llm_judge.py` → 55 passed（mcp<2 + ru_core_news_sm）
- 整理后：同命令结果见下方交接单

## 遗留问题
- `docs/superpowers/plans/`、`docs/superpowers/specs/` 两个空目录因电脑上默认禁止删除而保留，可手动删除（git 不跟踪空目录，无影响）。
- 论文草稿仍在 git 历史中（TASK-0003，需 Owner 决策）。
