# RuScholar Studio 文档中心

按软件研发生命周期编号组织。过程性记录（看板、任务卡、交接、日志）不在这里，见 [`../collab/`](../collab/README.md)。

| 目录 | 阶段 | 内容 | 入口 |
| --- | --- | --- | --- |
| `00-overview/` | 总览 | 项目定位、现状评估、模块地图 | [project-overview.md](00-overview/project-overview.md) |
| `01-requirements/` | 需求 | 产品需求基线 PRD；新需求单 `requests/REQ-xxxx-*.md` | [PRD.md](01-requirements/PRD.md) |
| `02-design/` | 设计 | 架构说明；功能设计规约 `specs/`；架构决策记录 `adr/` | [architecture.md](02-design/architecture.md) |
| `03-plans/` | 计划 | 路线图；各功能的实施计划 | [roadmap.md](03-plans/roadmap.md) |
| `04-development/` | 开发 | 环境、运行、分支、提交、代码规范、已知坑 | [dev-guide.md](04-development/dev-guide.md) |
| `05-testing/` | 测试 | 测试策略、测试基线 | [test-strategy.md](05-testing/test-strategy.md) |
| `06-release/` | 发布 | 版本号与发布流程（变更记录在根目录 `CHANGELOG.md`） | [release-process.md](06-release/release-process.md) |
| `assets/` | — | 文档图片 | — |

## 文件命名

- 设计规约 / 实施计划：`YYYY-MM-DD-<kebab-slug>.md`
- 需求单：`REQ-xxxx-<slug>.md`；ADR：`ADR-xxxx-<slug>.md`
- 模板统一在 `collab/templates/`

## 历史说明

2026-10-19 之前的设计与计划文档原放在 `docs/superpowers/{specs,plans}/`（由 superpowers 技能生成），已原样迁移到 `02-design/specs/` 与 `03-plans/`，内容未改动；其中提到的 `scripts/web_app.py` 现位于 `legacy/streamlit_web_app.py`。
