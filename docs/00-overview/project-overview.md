# 项目总览与现状评估

> 基于 2026-10-19 对 `feature/style-diagnostics` 分支（HEAD `078365e`，VERSION 5.4.1）的完整源码阅读与测试运行。

## 1. 定位

RuScholar Studio（前身 PhD Thesis Butler 的工程执行层）是面向俄语学位论文/学术稿件的写作质量审计与风格自然化工作台。
核心理念：**不给黑箱"AI 率"，只给可复核的证据链**——每个标记都带指标、原句、解释与改写建议。

上游知识资产是 PhD Thesis Butler Skill（俄语学术范式模板库），本仓库将其中的规则抽取为 `naturalization_layer/rules/polishing_rules_v5.json`（6 个学科簇：SCI_TECH、AUTOMATION_CONTROL、AGRI_MED、HUM_POL_ECON、ARTS_SPORTS、UNIVERSAL）。

## 2. 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | React 19、TypeScript 6、Vite 8、lucide-react；单页 `App.tsx` |
| 后端 | FastAPI + sse-starlette（SSE 流式推送逐句诊断） |
| MCP | `mcp` Python SDK 1.x 的 FastMCP，stdio，17 个 `thesis_*` 工具 |
| NLP | spaCy `ru_core_news_sm`（分句/依存/词性）、pymorphy3（词形还原） |
| 本地模型 | llama-cpp-python + Qwen3-8B-Q5_K_M GGUF（PPL 探针 + 本地判定），可回退 4B |
| 云端 | DeepSeek（OpenAI 兼容接口），用于 hybrid / cloud 判定 |
| 检索 | 自研 BM25（俄语词形还原）+ OpenAlex 在线摘要兜底 |
| 文档解析 | python-docx、pypdf |

## 3. 模块地图（代码行数）

| 模块 | 行数 | 职责 |
| --- | --- | --- |
| `backend/main.py` | 468 | HTTP/SSE 路由、模型懒加载、静态托管 `frontend/dist` |
| `services/diagnostic_service.py` | 554 | 逐句诊断流水线（local 分支 / cloud+hybrid 分支；stream 与 batch 两种出口） |
| `services/citation_audit_service.py` | 296 | 引文键提取、断言抽取、证据需求分类、证据绑定、NLI 引文审计 |
| `services/report_service.py` | 175 | Markdown / JSON 报告 |
| `services/shared_state.py` | 43 | 会话引用缓存、模型锁、模型路径解析 |
| `naturalization_layer/` | ~1990（不含规则 JSON） | 规则引擎、PPL、StyleJudge、NLIJudge、RAG、ГОСТ 校验、ВАК 专业映射、翻译腔/风格/相似度风险 |
| `mcp_server/server.py` | 1195 | 17 个 MCP 工具 + 兼容旧签名的函数 + 工作流路由 + ВАК/ГОСТ 合规审计 |
| `frontend/src/App.tsx` | 1361 | 全部 UI 与状态 |
| `tests/` | 1469 | 15 个测试文件，58 个用例 |

## 4. 现状评估

### 做得好的
- 分层意图清晰：算法层（`naturalization_layer`）与编排层（`services`）已分离，Web 与 MCP 共用服务层。
- 本地优先 + 优雅降级：无模型 → 纯启发式；无 llama-cpp → 跳过 PPL；云端出错不阻断。
- 早退出（early exit）+ 3 句一批的并发设计，兼顾算力和云端限流。
- 测试覆盖面广（规则、PPL、RAG/NLI、ГОСТ、ВАК、MCP 端到端），除需 llama-cpp 的 3 个用例外 55/55 通过。
- 设计文档有沉淀（4 份 spec、2 份 plan）。

### 主要问题（已全部转为任务卡，见 `ai-collab/board.md`）
| 类别 | 问题 | 任务 |
| --- | --- | --- |
| 可安装性 | `mcp>=1.0.0` 会装到 2.x 导致 MCP 无法导入；spaCy 模型缺失时规则引擎静默降级 | TASK-0001 |
| 配置 | 代码不读取 `.env`；端口 8000 / 6666 三处不一致；README 仍写 Qwen3-4B | TASK-0002 |
| 仓库卫生 | 被忽略的 `scratch/` 仍有文件被跟踪；个人论文草稿曾进入公开仓库历史；无 LICENSE；main/master 并存 | TASK-0003 |
| 工程化 | 无 CI、无 lint 门禁 | TASK-0004 |
| 代码重复 | 诊断流水线 local/cloud、stream/batch 大量复制；规则/校准加载和关键词兜底在 backend 与 service 重复 | TASK-0005 |
| 性能 | PPL 用纯 Python 遍历整个词表做 softmax | TASK-0006 |
| 前端可维护性 | 1361 行单组件 | TASK-0007 |
| MCP 可维护性 | 1195 行单文件，业务逻辑混在工具里 | TASK-0008 |
| 稳定/安全 | 内存会话无过期；CORS `*` + credentials；默认绑定 0.0.0.0；上传无大小限制 | TASK-0009 |
| 可信度 | 阈值与 README 中的量化宣称缺少可复现评测 | TASK-0010 |
| 范围 | 4 个 501 占位接口 | TASK-0011 |

### 隐私说明（需与 README 表述对齐）
本地模式下论文正文不出本机；但引文审计在本地没有对应 PDF 时，会用参考文献条目（标题/作者/年份）查询 OpenAlex。hybrid/cloud 模式会把句子发送给 DeepSeek。README 的"完全离线"应限定为 `local` 模式且未启用在线检索。
