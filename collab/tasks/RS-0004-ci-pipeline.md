# RS-0004：建立 CI（GitHub Actions）

| 字段 | 值 |
| --- | --- |
| 状态 | 待办（依赖 RS-0001） |
| 优先级 | P1 |
| 负责人 | 未分配（建议 codex） |
| 评审人 | claude |
| 关联需求 | 技术债 |

## 要做的事
- [ ] `.github/workflows/ci.yml`：Python 3.10/3.12 矩阵，安装依赖 + spaCy 模型，跑 `pytest -q`（不下载 GGUF 模型）
- [ ] 前端 job：`npm ci && npm run lint && npm run build`
- [ ] 加 ruff（lint + format 检查），先只报告不阻断

## 验收标准
- [ ] PR 上自动出现两个绿色检查

## 验证记录
