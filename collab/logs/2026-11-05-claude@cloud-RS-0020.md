# RS-0020 会话日志（claude@cloud，2026-11-05）

- 原因：Owner 指出 AI 生成特征、翻译腔等在前端显示的数据不正确。
- 复现：用真实诊断流水线（只模拟判定接口）跑出 6 处问题：参考文献计入分母、只保留首个问题、接口失败显示为通过、可预测性口径、前缀 PPL 混用、未知类型改名。
- 后端：result 只增 is_bibliography / issues / judge_error / ppl_basis；风险只算正文，可预测性回退分母为已判定正文句。
- 前端：统计只算正文；多问题计数与展示；「未判定」状态与提醒；参考文献免检；前缀 PPL 标注；无数据显示「—」。
- 验证：pytest 116 passed / 1 deselected（新增 5 项）；lint、API 6/6、配置 8/8、构建通过；浏览器按真实流水线输出核对两个场景，数字均正确。
- 证据：collab/reviews/2026-11-05-RS-0020-data-correctness.md。
- 遗留：待 Owner 确认；推送需 Owner 批准。
