# 发布流程

## 版本号
语义化版本 `MAJOR.MINOR.PATCH`，单一来源为根目录 `VERSION`，`frontend/package.json` 的 version 同步修改。
- PATCH：修 bug、文档
- MINOR：新功能、向后兼容的接口新增
- MAJOR：SSE 契约 / MCP 工具名或参数的不兼容变更

## 步骤
1. 看板上该版本的任务全部 `已完成`
2. `pytest -q` 全绿；本地带模型跑一遍模型测试；前端 `npm run build`
3. 端到端走查一遍并截图
4. 更新 `VERSION`、`frontend/package.json`、`CHANGELOG.md`（把 Unreleased 改为版本号与日期）
5. PR 合入 `main` 后打 tag `vX.Y.Z`，GitHub Release 正文取自 CHANGELOG
6. 发布前检查：无 `.env`、模型文件、论文原文、`scratch/` 内容被跟踪（`git ls-files`）
