# 当前主干交接（codex@mac，2026-10-21）

- Owner 已验收锁/端口修复，授权现状定型；main 已整合代码 `81cb8f4`，前序 feature/任务分支保留。
- 当前配置：只读根 .env，shell 存在即优先；空端口默认 8000；模型自动查找 data/models。
- 已验证：端口行为 8/8、pytest 68+1 skipped、TypeScript/Vite build；根锁回归 7/7。
- 新工作从 main 建任务分支；本轮随后推进 RS-0011 占位接口删除，进度以看板及其任务卡为准。
- Windows 上先同步新锁脚本，设置 THESIS_MACHINE=win；锁恢复和释放必须带会话号。本机互斥不替代双方同步确认。
- RS-0013 的全新安装/Windows/Metal 及 RS-0014 历史清理仍单列，不宣称通过；未推送。
- 不以旧 feature/style-diagnostics 或 master 作为后续开发起点，不覆盖历史记录。
