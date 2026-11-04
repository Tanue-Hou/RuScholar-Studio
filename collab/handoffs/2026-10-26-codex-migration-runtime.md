# RuScholar 迁移与运行交接（codex@mac，2026-10-26）

- Owner 已明确：新目录为当前 PHD-Scholar；确认可运行后删除旧 RuScholar；Python 可直接使用本机环境。
- 唯一开发目录：`projects/ruscholar-studio/`；当前分支 `agent/codex/RS-0015-migration-runtime`，接续原 CI 分支；main 与历史分支保留，未推送。
- 旧 `~/Documents/antigravity/friendly-lavoisier` 已删除；删除后 Web/PPL 和新进程 MCP 均再次通过。
- Python：`~/miniforge3/bin/python3`（3.13.12）；依赖来源为本机 miniforge，不依赖旧 .venv；不另建环境。
- 稳定启动：在本项目执行 `PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/bin/python3 -B -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`。
- 网页：`http://127.0.0.1:8000`；Chrome 已实际打开，页面显示 Qwen3 引擎在线。
- 后端：73 passed / 1 deselected；pip check 通过。相对模型路径测试改用临时夹具，避免真实模型存在时污染单测。
- 前端：在 OneDrive 外 npm ci，lint、配置 8/8、build 通过；构建已放入被忽略的 frontend/dist。
- 真实 Qwen：自写普通句 PPL 40.75、early_exit；自写套话句 PPL 17.89、生成式判定 flagged；两次均 init/result/done，非 Mock。
- MCP：stdio 初始化、17 工具、模型完整性及断言提取调用通过；Antigravity cwd/PYTHONPATH 和 Claude 的旧目录授权均已切换。
- 资产：新旧模型哈希一致；1970 个私有文件与 data/private/ruscholar-scratch 全部一致；旧 Git 历史已存在于新仓库，另存 bundle。
- 私有证据与恢复包：`../../data/backups/20261026-ruscholar-migration/`；归档逐文件核验，删除前 2119 个非模型源文件再次核验通过；不进 Git。
- 客户端若仍缓存旧 MCP，刷新该服务使配置生效；独立新进程的协议调用已验证，不等同于所有客户端 GUI 都完成重连。
- 留待后续：npm audit 发现 1 项 high（zod 4.4.3，eslint-plugin-react-hooks 的开发依赖）；此次未改锁文件。
- 运行通过不代表 AI 检测准确率已验证；质量评测仍按 RS-0010。Windows、远端 CI、RS-0014 公开历史清理仍各自待办。
- 后续按看板推进 RS-0005/0006 等；写入前按新会话拿 RS 锁，本轮不合并 main。
