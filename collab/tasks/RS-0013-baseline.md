# RS-0013：运行基线

| 字段 | 值 |
| --- | --- |
| 状态 | 已完成（基线已记录） |
| 分支 | —（只读） |
| 优先级 | P0 |
| 负责人 | claude@mac |
| 评审人 | 待定（不能是负责人） |
| Owner 批准 | 待批准 |
| 来源 | 原 RS-GOV-01、HUB-0007 拆分 |

## 目标
在当前提交（`feature/style-diagnostics`）下，弄清楚 RuScholar 在 Mac 上实际能不能装、能不能跑、测试结果如何，作为之后所有任务的起点。

## 范围
只读与本机环境（虚拟环境建在 OneDrive 之外）；不改代码。

## 验收标准
- [ ] 记录提交号、Python/Node 版本、安装命令与结果
- [ ] `pytest -q` 结果（注明跳过与失败的原因）
- [ ] 后端、前端开发模式、MCP 服务各启动一次的结果
- [ ] 发现的问题写成新任务或补进已有任务

## 验证记录

## 基线结果（2026-10-21，claude@mac；云端 Python 3.13 全新环境 + Node 22；提交 61ccef9）
- 原样 `pip install -r requirements.txt`：**失败**，`pymorphy3>=2.1` 在 PyPI 上不存在（最新 2.0.6）→ RS-0001。
- 放宽 pymorphy3、跳过 llama-cpp 后可安装，但装到 **mcp 2.3.0**：`mcp_server` 无法导入、MCP 服务启动失败 → RS-0001。
- requirements 中没有 pytest → RS-0001。
- pytest：`test_llm_judge.py`（缺 llama-cpp）与 `test_services_and_mcp.py`（mcp 2.x）收集失败；其余 42 个通过。
- 后端：8000 端口启动正常，`/api/check_model`、`/api/detect_discipline` 可用；无模型时退回纯规则模式；未构建前端时提示缺 `frontend/dist`。
- 前端：`npm ci`、`npm run build` 成功；`npm run lint` 1 个错误（`App.tsx:73` no-explicit-any）→ 留给 RS-0007。
- llama-cpp-python 需要本机编译（Mac 用 Metal），未在此环境验证；在 Mac 本机运行时另行记录。
