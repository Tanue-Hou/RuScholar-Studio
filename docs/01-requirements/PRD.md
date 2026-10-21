# 产品需求基线（PRD v5.4.1，逆向整理）

> 本文是根据现有代码与 README 逆向整理的**需求基线**，描述"系统现在应该做到什么"。
> 之后的新需求一律以需求单形式提交到 `requests/`（模板：`collab/templates/requirement.md`），批准后再更新本文。

## 1. 目标用户与场景

| 用户 | 典型场景 |
| --- | --- |
| 在俄罗斯攻读学位的外国博士生/硕士生（首要用户） | 用非母语写俄语论文，担心翻译腔、模板化表达、被误判为 AI 生成 |
| 俄语学术写作者 | 投稿/答辩前的自查：文献引用一致性、ГОСТ 著录、ВАК 引言要素 |
| AI 助手（Claude/Codex/Cursor 等） | 通过 MCP 调用审计工具，作为写作工作流的一环 |

## 2. 功能需求（状态：✅ 已实现 / 🟡 部分 / ⛔ 占位）

### A. 文稿输入与诊断
| ID | 需求 | 状态 | 实现位置 |
| --- | --- | --- | --- |
| F-A1 | 上传 .docx / .pdf / .txt 或粘贴文本 | ✅ | `/api/upload` |
| F-A2 | 自动识别学科簇（本地/云端模型，失败回退关键词） | ✅ | `/api/detect_discipline` |
| F-A3 | 逐句流式诊断：规则轨（名动比、被动、属格链、套话、连接词）+ PPL 轨 + 判定轨 | ✅ | `/api/session` + `/api/diagnose`（SSE） |
| F-A4 | 三种引擎模式：local、hybrid（本地 PPL + 云端判定）、cloud；pro/flash 两档 | ✅ | `diagnostic_service` |
| F-A5 | 参考文献区免检、公式/引标保护 | ✅ | `rules_engine.TextPreprocessor` |
| F-A6 | 低 PPL 一票否决、早退出 | ✅ | `diagnostic_service`、`ppl_engine` |
| F-A7 | 实时整体风险：可预测性、均匀性、翻译腔、冗余 | ✅ | `style_risk`、`translationese_risk` |
| F-A8 | 每个标记给出问题类型、严重度、中/俄解释、改写建议、推理过程 | ✅ | `llm_judge` |

### B. 文献与证据链
| ID | 需求 | 状态 | 实现位置 |
| --- | --- | --- | --- |
| F-B1 | 注册 BibTeX 与参考 PDF，按会话缓存并建 BM25 索引 | ✅ | `/api/upload_references`、`thesis_register_references` |
| F-B2 | 文内引标与篇末文献双向一致性检查 | ✅ | `citation_integrity` |
| F-B3 | 句子-引文 NLI 审计（SUPPORTED / CONTRADICTED / NOT_ENOUGH_INFO） | ✅ | `citation_audit_service`、`nli_judge` |
| F-B4 | 本地缺文献时用 OpenAlex 摘要兜底 | ✅ | `rag_retriever.fetch_openalex_abstract` |
| F-B5 | 断言抽取、证据需求分级、证据绑定 | ✅（仅 MCP） | `thesis_extract_claims` 等 |
| F-B6 | 引用缺口（与本地文献高度重合但无引标）告警 | ✅ | `source_similarity` |

### C. 学位论文合规
| ID | 需求 | 状态 | 实现位置 |
| --- | --- | --- | --- |
| F-C1 | ВАК 专业代码映射与越界提示 | ✅（仅 MCP） | `vak_specialty_mapper` |
| F-C2 | 引言 ВАК 8 要素检查 + ГОСТ Р 7.0.100-2018 著录评分 | ✅（仅 MCP） | `thesis_audit_vak_gost_compliance`、`gost_validator` |
| F-C3 | 结构分析、格式检查 | ⛔ | `/api/structure`、`/api/format` 返回 501 |

### D. 输出与集成
| ID | 需求 | 状态 | 实现位置 |
| --- | --- | --- | --- |
| F-D1 | Markdown / JSON 报告导出 | 🟡 仅 MCP，Web UI 未接入 | `report_service` |
| F-D2 | MCP stdio 服务，17 个工具，工作流路由 | ✅ | `mcp_server` |
| F-D3 | 改写建议接口 | 🟡 MCP 有，Web `/api/polish` 501 | `thesis_suggest_revision` |
| F-D4 | 本地模型状态检查与下载（进度条） | ✅ | `/api/check_model`、`/api/download_model` |

## 3. 非功能需求

| ID | 需求 | 现状 |
| --- | --- | --- |
| NF-1 隐私 | local 模式下论文正文不离开本机 | 满足；在线检索只发送文献条目（见总览隐私说明） |
| NF-2 可解释 | 不输出单一"AI 率"，每个结论附证据 | 满足 |
| NF-3 降级 | 缺模型/缺网络/云端报错时仍可用 | 满足（spaCy 模型缺失时为静默降级，需改进 → RS-0001） |
| NF-4 性能 | 本地 8B 模型下中等长度章节可在可接受时间内完成 | 未量化 → RS-0006 建基准 |
| NF-5 安全 | 单机使用，不暴露到局域网 | 未满足 → RS-0009 |
| NF-6 可安装 | 一条脚本完成安装 | 部分满足（依赖漂移 → RS-0001） |
| NF-7 可信度 | 阈值与宣称可被评测复现 | 未满足 → RS-0010 |

## 4. 明确不做（当前版本）
- 不做"查重率"或"AI 检测率"百分比裁决
- 不做多用户账号体系与云端托管
- 不自动替换用户原文（只给建议）
