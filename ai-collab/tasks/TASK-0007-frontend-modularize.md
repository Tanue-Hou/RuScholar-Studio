# TASK-0007：前端拆分 App.tsx（1361 行单文件）

| 字段 | 值 |
| --- | --- |
| 状态 | 待办 |
| 优先级 | P1 |
| 负责人 | 未分配（建议 antigravity） |
| 评审人 | claude |
| 关联需求 | 可维护性 |

## 要做的事
- [ ] 目录：`src/api/`（fetch 与 SSE 客户端）、`src/types/`（DiagnosticResult 等，与后端 SentenceResult 对齐）、`src/hooks/`（useDiagnoseStream、useModelStatus）、`src/components/`（DocumentPane、Inspector、RiskPanel、ReferenceUploader、SettingsPanel）
- [ ] 行为与样式保持不变；拆分前后各截图一张存到任务卡
- [ ] 补最小前端测试（vitest）覆盖 SSE 事件归并逻辑

## 验收标准
- [ ] `npm run lint && npm run build` 通过；端到端走一遍上传→诊断→点击定位，行为一致

## 验证记录
