# 交接单：claude → 所有助手（仓库规范化完成，进入阶段 0）

- 日期：2026-10-19
- 分支：`feature/style-diagnostics`，改动**尚未提交**
- 当前状态：目录与协作体系已建立，等待 Owner 审阅并提交

## 已完成
- 见 `logs/2026-10-19-claude-repo-restructure.md`

## 下一步（按顺序）
1. **Owner**：审阅 `git status` 中的移动与新增文件，提交为 `docs: restructure repo and add multi-agent collaboration workflow (TASK-0000)`
2. **Owner**：在 TASK-0002 里决定端口（8000 或 6666）；在 TASK-0003 里决定 scratch 出库 / 历史清理 / 分支收敛
3. **codex**：认领 TASK-0001（依赖修复），完成后 TASK-0004（CI）
4. **antigravity**：可并行认领 TASK-0007（前端拆分），注意 SSE 字段契约见 `docs/02-design/architecture.md` 第 2 节
5. **claude**：TASK-0005 设计文档，完成后交 codex 实现

## 注意事项 / 坑
- 测试需要：`pip install "mcp<2"` 与 `python -m spacy download ru_core_news_sm`
- `.env` 不会被自动加载；开发模式下后端需用 6666 端口才能被 vite 代理到
- 项目根的 `.venv` 是 macOS 生成的，Linux/其他机器需自建

## 需要 Owner 决策的问题
- 端口统一值（TASK-0002）
- TASK-0003 全部四项
- 评测语料来源与授权（TASK-0010）
