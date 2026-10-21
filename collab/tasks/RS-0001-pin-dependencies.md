# RS-0001：修复依赖漂移，保证新环境可安装可测试

| 字段 | 值 |
| --- | --- |
| 状态 | 待验收 |
| 分支 | agent/claude/RS-0001-pin-dependencies（e5f75af；评审时为 b183eef，变基到 c4e7721 后 range-diff 内容一致） |
| 优先级 | P0 |
| 负责人 | claude@mac |
| 评审人 | codex（2026-10-21：通过） |
| 关联需求 | 技术债 |

## 背景
2026-10-19 在全新环境安装时发现：`requirements.txt` 中 `mcp>=1.0.0` 会装到 mcp 2.x，`from mcp.server.fastmcp import FastMCP` 直接报错，MCP 服务与 `tests/test_services_and_mcp.py` 全部无法导入。另外 spaCy 俄语模型 `ru_core_news_sm` 未安装时规则引擎会**静默降级**（属格链检测返回空），导致测试失败但不报错。`tests/test_llm_judge.py` 顶层直接 `from llama_cpp import Llama`，没装 llama-cpp-python 时整个测试收集失败。

## 要做的事
- [ ] `requirements.txt` 中改为 `mcp>=1.0.0,<2`，其余依赖补上合理上界
- [ ] `tests/test_llm_judge.py` 改为 `pytest.importorskip("llama_cpp")`
- [ ] 规则引擎加载 spaCy 模型失败时打印明确警告（或在 `/api/check_model` 一类的健康检查中体现）
- [ ] 评估是否生成 `requirements.lock`（pip-tools）

## 影响范围
`requirements.txt`、`tests/test_llm_judge.py`、`naturalization_layer/rules_engine.py`

## 验收标准
- [ ] 全新 venv：`pip install -r requirements.txt && python -m spacy download ru_core_news_sm && pytest -q` 全部通过（无 llama-cpp 时 llm_judge 显示 skipped）

## 验证记录

## 验证记录（2026-10-21，claude@mac，云端 Python 3.13 全新环境，未装 llama-cpp）
- 依赖加上界；`mcp>=1.0,<2`（装到 1.30.0）；`pymorphy3>=2.0,<3`；新增 `requirements-dev.txt`（pytest），setup 脚本改装它。
- `test_llm_judge.py` 缺 llama-cpp 时跳过；spaCy 模型只加载一次，缺失时打印一次明确警告（已用模拟加载失败验证）。
- `pytest -q`：55 passed, 1 skipped；MCP 服务可启动，17 个工具。

## 评审（codex，2026-10-21，由 Owner 转交）
- 结论：未发现阻断性问题，可进入验收。评审方本机测试 57 passed / 1 skipped（已有环境）。
- 尚未验证：全新安装、Windows、Mac 本机 llama-cpp（Metal）。
