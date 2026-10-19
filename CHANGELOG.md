# 变更记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循语义化版本。

## [Unreleased]

### 新增
- 多助手协作体系：`AGENTS.md`（统一入口）、`CLAUDE.md`、`GEMINI.md`、`ai-collab/`（看板、任务卡、交接、日志、评审、模板）
- 文档按生命周期重组为 `docs/00-overview` … `docs/06-release`；新增总览、PRD 基线、架构说明、ADR-0001~0003、路线图、开发指南、测试策略、发布流程

### 变更（仅移动文件，业务代码未改）
- `docs/superpowers/specs/*` → `docs/02-design/specs/`；`docs/superpowers/plans/2026-*` → `docs/03-plans/`
- `scripts/web_app.py`（旧 Streamlit UI）→ `legacy/streamlit_web_app.py`
- `backend/test_judge.py` → `scripts/manual_test_judge.py`
- `test_input.txt` → `tests/fixtures/sample_ru_sentences.txt`
- `phd-thesis-butler-landing/` → `sites/phd-thesis-butler-landing/`
- 个人论文草稿移出文档目录至 `scratch/thesis-drafts/`；`frontend/rewrite_app.py`（一次性改写脚本）归档到 `scratch/archive/`

## [5.4.1] - 2026-10-02
- 升级本地模型到 Qwen3-8B，界面现代化，仓库脱敏准备公开发布

## [5.x] - 2026-06（摘要）
- ВАК 专业映射、细粒度引文审计、ГОСТ 合规审计（Wave 3.0）
- 俄语词形还原接入 RAG 与相似度
- MCP 工具统一 `thesis_` 前缀、工作流路由、统一返回结构
- NLI 判定与双轨引文检索；服务层抽取并接入 stdio MCP
- 混合模式、学科分类路由、3 句并发、PDF 解析
- 项目由 PhD Thesis Butler 更名为 RuScholar Studio
