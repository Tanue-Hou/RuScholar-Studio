# RuScholar Studio

证据驱动的俄语学术写作质量审计系统。项目原名和能力来源为 PhD Thesis Butler，现在扩展为同时支持 Web UI 与 MCP Agent 工具调用的本地研究写作工作台。

![Web UI diagnostics](docs/assets/webui-diagnostics.png)

Web UI 展示的是混合诊断模式：左侧为俄语论文正文与逐句风险标注，右侧为学科识别、PPL 均值、风格风险、可预测性风险、翻译腔风险、冗余风险和句级解释面板。截图中的黄色/红色高亮并不等同于“定罪”，而是提示需要进一步核查的证据链节点。

## 核心能力

- 俄语学术文本风格诊断：套话、连接词堆叠、被动结构、名词化、第二格链、机器翻译腔。
- 本地 PPL 风险评估：使用 GGUF 本地模型计算困惑度，支持早期退出以降低计算成本。
- 学科阈值校准：通过 `naturalization_layer/calibration/calibration_config.json` 与随仓库发布的 `naturalization_layer/rules/polishing_rules_v5.json` 调整判定边界。
- 文献证据链审计：正文引用与参考文献列表双向核查，本地 RAG 检索，OpenAlex 摘要辅助核验。
- NLI 引文逻辑审计：对 claim 与 evidence snippet 做蕴含、矛盾、证据不足判断。
- 双入口架构：Web UI 适合人工审阅，MCP 适合 Claude、Codex、Cursor 等 Agent 调用。

## 证据链可靠性判断

当前证据链已经具备工程可用性，但不应被包装成自动判定论文造假或 AI 代写的最终裁决器。合理定位是“审计辅助系统”：

- 可靠部分：引用完整性差集、参考文献缺失、正文标号缺失、本地 RAG 可回溯片段、PPL 与规则特征的交叉提示。
- 需要人工复核部分：PPL 低值不必然代表 AI 生成，PPL 高值不必然代表翻译错误，OpenAlex 摘要不能替代全文证据，LLM/NLI 结论需要保留解释与原文片段。
- GitHub 文档中应持续强调：系统输出是 risk signal 和 evidence trail，不是 misconduct verdict。

## 系统要求

- Python 3.9 或更高版本。
- Node.js 20 或更高版本，用于构建 Web UI。
- 建议内存 16GB 以上。本地 Qwen3-4B Q5_K_M GGUF 模型约 2.7GB。
- Apple Silicon 用户建议安装 Metal 版本 `llama-cpp-python`；无 GPU 环境可设置 `THESIS_BUTLER_GPU_LAYERS=0` 使用 CPU 回退。

## 快速开始

```bash
git clone <YOUR_REPOSITORY_URL>
cd ruscholar-studio
./setup.sh
```

如需安装时同时下载本地模型：

```bash
DOWNLOAD_MODEL=1 ./setup.sh
```

Apple Silicon 上如需强制编译 Metal 版本：

```bash
INSTALL_LLAMA_METAL=1 ./setup.sh
```

Windows:

```powershell
.\setup.ps1
```

## 手动安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download ru_core_news_sm

cd frontend
npm install
npm run build
cd ..
```

下载本地模型：

```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

## 启动 Web UI

```bash
source .venv/bin/activate
python backend/main.py
```

默认地址为 `http://localhost:8000`。可通过 `.env` 或环境变量修改：

```bash
THESIS_BUTLER_HOST=127.0.0.1 THESIS_BUTLER_PORT=8010 python backend/main.py
```

## MCP 集成

MCP 模式让 Claude、Codex、Cursor、Claude Desktop 等客户端直接调用本地审计工具。

```bash
python -m mcp_server.server
```

示例配置：

```json
{
  "mcpServers": {
    "ruscholar-studio": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/YOUR_CLONE_PATH/ruscholar-studio"
    }
  }
}
```

当前 MCP 工具包括：

- `analyze_manuscript`
- `audit_citations`
- `retrieve_evidence`
- `suggest_revision`
- `export_report`
- `check_model_installed`
- `download_model_tool`
- `register_references`
- `clear_references`
- `list_references`

## 配置项

复制 `.env.example` 为 `.env`，按需填写：

```bash
cp .env.example .env
```

常用变量：

- `DEEPSEEK_API_KEY`：云端 judge API key。
- `DEEPSEEK_BASE_URL`：兼容 OpenAI API 风格的 DeepSeek 地址。
- `THESIS_BUTLER_MODEL_PATH`：本地 GGUF 模型路径。
- `THESIS_BUTLER_MODEL_URL`：模型下载源。
- `THESIS_BUTLER_RULES_PATH`：学科修辞规则路径。
- `THESIS_BUTLER_GPU_LAYERS`：`-1` 表示尽量 GPU offload，`0` 表示 CPU-only。

## 运行测试

```bash
pytest -q
cd frontend && npm run build
```

## GitHub 发布前检查

- 不提交 `.env`、API key、模型文件、`frontend/dist/`、`node_modules/`。
- 保留 `naturalization_layer/rules/polishing_rules_v5.json`，它是项目级规则资源。
- 保留 `docs/assets/webui-diagnostics.png`，README 依赖该图展示 Web UI。
- README 中使用 `/YOUR_CLONE_PATH/...` 占位符，不写作者本机路径。

