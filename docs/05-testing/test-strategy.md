# 测试策略

## 1. 分层

| 层 | 范围 | 要求 |
| --- | --- | --- |
| 单元测试 | `naturalization_layer/` 各模块 | 不依赖模型与网络；必须进 CI |
| 服务/契约测试 | `services/`、MCP 工具返回结构、SSE `result` 字段 | 用假的判定器（`StyleJudge(None)`）；必须进 CI |
| 模型测试 | 需要 GGUF / llama-cpp 的测试 | 标记 `@pytest.mark.model`，CI 跳过，本地发版前跑 |
| 端到端 | 浏览器走查：上传 → 诊断 → 点击定位 → 文献上传 | 发版前人工或 Antigravity 执行，截图存任务卡 |
| 质量评测 | 误报/漏报（TASK-0010） | 规则或阈值改动时必须跑 |

## 2. 基线（2026-10-19，claude 记录）

环境：Linux / Python 3.10，全新 venv，`mcp<2`，已安装 `ru_core_news_sm`，未安装 llama-cpp-python。

```
pytest -q --ignore=tests/test_llm_judge.py   →  55 passed
```

未装 spaCy 俄语模型时：`test_rules_engine.py::test_analyze_text_rules_advanced` 与 `test_services_and_mcp.py::test_mcp_e2e_references_flow` 失败。
装 mcp 2.x 时：`test_services_and_mcp.py` 无法导入。

## 3. 规则
- 修 bug 先写能复现的失败测试
- 测试样例放 `tests/fixtures/`，不得使用未授权的真实论文全文
- 测试不得访问网络（OpenAlex/DeepSeek 调用需 mock）——目前 `test_mcp_e2e_references_flow` 需排查是否依赖网络
