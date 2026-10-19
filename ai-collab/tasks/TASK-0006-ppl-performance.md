# TASK-0006：PPL 计算向量化提速

| 字段 | 值 |
| --- | --- |
| 状态 | 待办 |
| 优先级 | P1 |
| 负责人 | 未分配（建议 codex） |
| 评审人 | claude |
| 关联需求 | 性能 |

## 背景
`naturalization_layer/ppl_engine.py` 对每个 token 用纯 Python `max()/sum(math.exp())` 遍历整个词表（Qwen3 约 15 万）做 softmax，长句 PPL 计算以秒计，是本地模式的主要瓶颈之一。

## 要做的事
- [ ] 用 numpy 对 `llm._scores` 切片做 log-softmax（或 `scipy.special.logsumexp`）
- [ ] 写基准脚本 `scripts/bench_ppl.py`，记录改前/改后每句耗时
- [ ] 数值一致性测试（与旧实现误差 < 1e-4）

## 验收标准
- [ ] 同一批句子结果一致，耗时显著下降（在任务卡记录数字）

## 验证记录
