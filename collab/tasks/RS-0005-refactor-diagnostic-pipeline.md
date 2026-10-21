# RS-0005：重构诊断流水线，消除 local / cloud 两套重复代码

| 字段 | 值 |
| --- | --- |
| 状态 | 待办（建议先完成 RS-0002） |
| 优先级 | P1 |
| 负责人 | 未分配（建议 claude 设计 + codex 实现） |
| 评审人 | Owner |
| 关联需求 | 技术债 |

## 背景
`services/diagnostic_service.py`（554 行）里 `process_sentence_local` 与 `process_sentence_cloud` 大段复制（参考文献免检、相似度、翻译腔检查、结果字典构造），`run_sentence_diagnose_stream` 与 `run_sentence_diagnose_batch` 又各有一套。`backend/main.py` 里关键词兜底分类写了两遍，`get_discipline_rules` 与 diagnostic_service 重复。

## 要做的事
- [ ] 先写设计：`docs/02-design/specs/YYYY-MM-DD-diagnostic-pipeline-refactor.md`，定义 `SentenceResult` pydantic 模型和"阶段"接口（rules → similarity → ppl → judge → citation）
- [ ] 抽出单句处理函数，local/hybrid/cloud 只在"用哪个判定器、是否算 PPL"上不同
- [ ] stream 与 batch 共用同一个生成器
- [ ] 关键词分类兜底收敛到一个函数

## 验收标准
- [ ] SSE 事件格式与前端完全兼容（前端零改动）
- [ ] 现有测试全部通过，并新增 SentenceResult 的契约测试

## 验证记录
