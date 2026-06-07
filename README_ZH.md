# PhD Thesis Butler / RuScholar Studio

**版本：v5.2.0-alpha**  
**语言切换：** [English](README.md) | **中文** | [Русский](README_RU.md)

证据驱动的学术写作质量审计系统，面向博士论文、学术手稿与科研论文。项目延续原有 **PhD Thesis Butler** skill 的算法与写作规则资产，并扩展为 **RuScholar Studio**：同时支持 Web UI、人机协同审阅和 MCP Agent 工具调用的本地研究写作工作台。

本系统刻意避开传统“AI 检测率评分”的陷阱，采用 **本地规则引擎 + 本地 PPL 探针 + 本地/在线文献检索 + LLM-as-NLI Judge 证据审计** 的可追溯验证架构。系统输出应被理解为风险信号和证据链提示，而不是对 AI 代写、剽窃或学术不端的自动裁决。

版本命名沿用源规则资产的迭代脉络：`polishing_rules_v5.json` 当前规则版本为 `5.1.3`，本仓库在此基础上加入 WebUI、MCP、服务层复用、GitHub 安装脚本和三语文档，因此命名为 `v5.2.0-alpha`。

![Web UI diagnostics](docs/assets/webui-diagnostics.png)

Web UI 展示的是混合诊断模式：左侧为俄语论文正文与逐句风险标注，右侧为学科识别、PPL 均值、风格风险、可预测性风险、翻译腔风险、冗余风险和句级解释面板。截图中的黄色/红色高亮并不等同于“定罪”，而是提示需要进一步核查的证据链节点。

## 系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| Python | 3.9+ | 3.10+ |
| Node.js | 18+ | 20+ |
| RAM | 8 GB，适合纯云端模式 | 16 GB，本地模型模式 |
| 磁盘空间 | 500 MB，源码与依赖 | 4 GB，含 2.7 GB GGUF 模型 |
| 操作系统 | macOS / Linux / Windows | macOS Apple Silicon + Metal |

macOS Apple Silicon 用户可使用 Metal 加速；Linux/Windows 用户如不希望编译本地模型依赖，可优先使用 `cloud-pro` 或 `cloud-flash` 模式。

## 快速开始

```bash
git clone https://github.com/Tanue-Hou/RuScholar-Studio.git
cd RuScholar-Studio
chmod +x setup.sh
./setup.sh
```

安装时同时下载本地模型：

```bash
DOWNLOAD_MODEL=1 ./setup.sh
```

Apple Silicon 上强制安装 Metal 版本：

```bash
INSTALL_LLAMA_METAL=1 ./setup.sh
```

Windows:

```powershell
.\setup.ps1
```

## 本地大模型说明

为保护研究者论文手稿隐私，系统的本地 PPL 探针与本地 NLI/风格裁判可以依赖 **Qwen3-4B-Q5_K_M GGUF** 模型。模型约 2.7 GB，默认下载到：

```text
models/Qwen3-4B-Q5_K_M.gguf
```

手动下载：

```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

也可以通过 MCP 工具 `download_model_tool` 让 AI 客户端触发下载。如果本地没有模型，`local` 与 `hybrid` 模式不可用，但纯云端模式仍可运行。

## Web UI 启动

前后端合并模式：

```bash
source .venv/bin/activate
python backend/main.py
```

浏览器打开 `http://localhost:8000`。

开发热更新模式：

```bash
# 终端 1
python backend/main.py

# 终端 2
cd frontend
npm run dev
```

可通过环境变量修改后端地址：

```bash
THESIS_BUTLER_HOST=127.0.0.1 THESIS_BUTLER_PORT=8010 python backend/main.py
```

## MCP 集成

本系统原生支持 **MCP (Model Context Protocol)**，使 Claude Code、Cursor、Claude Desktop、Codex 等 AI Agent 可以直接调用本地工具，对本地学术手稿进行离线或混合诊断。

启动 MCP Server：

```bash
python -m mcp_server.server
```

Claude Desktop 示例配置：

```json
{
  "mcpServers": {
    "thesis-butler": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/YOUR_CLONE_PATH/RuScholar-Studio"
    }
  }
}
```

Claude Code 示例：

```bash
claude mcp add thesis-butler python -m mcp_server.server --cwd "/YOUR_CLONE_PATH/RuScholar-Studio"
```

当前 MCP 工具：

| # | 工具名 | 功能 |
|---|--------|------|
| 1 | `analyze_manuscript` | 对论文段落进行学术风格诊断，包括翻译腔、名词堆叠、PPL 风险评估 |
| 2 | `audit_citations` | 交叉核验正文引文标号与文末参考文献一致性 |
| 3 | `retrieve_evidence` | 通过本地文献库或 OpenAlex 检索证据片段 |
| 4 | `suggest_revision` | 结合上下文与学科规则生成改写建议 |
| 5 | `export_report` | 导出 Markdown 或 JSON 审计报告 |
| 6 | `check_model_installed` | 检查本地模型是否存在及大小是否正确 |
| 7 | `download_model_tool` | 自动下载 GGUF 本地模型 |
| 8 | `register_references` | 注册 BibTeX 文本和/或本地 PDF 路径 |
| 9 | `clear_references` | 清除指定会话引用库 |
| 10 | `list_references` | 列出指定会话引用库 |

## 诊断机制

系统采用多轨协同诊断策略：

1. **Track A：规则与风格结构轨**  
   检测名动比、被动结构、名词第二格链、连接词堆叠、学术套话和机器翻译腔。

2. **Track B：概率特征轨**  
   使用本地 GGUF 模型计算 Perplexity，并通过早期退出机制降低本地推理成本。

3. **Track C：文献一致性轨**  
   检查正文引用与参考文献列表之间的双向缺口，支持本地 BM25 检索和 OpenAlex 摘要辅助核验。

4. **Track D：LLM/NLI 证据审计轨**  
   将论文 claim 与检索到的 snippet 进行蕴含、矛盾、证据不足三类判断。

高风险文献问题优先提示；风格与 PPL 异常会触发专家模型进行上下文诊断。系统保留解释、指标与原始片段，便于人工复核。

## 运行模式

| 模式 | 本地 PPL | LLM 裁判 | 适用场景 |
|------|---------|---------|---------|
| `local` | 是 | 本地 Qwen | 完全离线，保护隐私 |
| `hybrid-pro` | 是 | DeepSeek Pro | 本地概率探针 + 云端深度分析 |
| `hybrid-flash` | 是 | DeepSeek Flash | 本地概率探针 + 云端快速分析 |
| `cloud-pro` | 否 | DeepSeek Pro | 无本地模型，纯云端深度诊断 |
| `cloud-flash` | 否 | DeepSeek Flash | 无本地模型，纯云端快速诊断 |

## 配置项

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

## 测试验证

```bash
pytest -q
cd frontend && npm run build
```

当前测试覆盖规则引擎、PPL 引擎、LLM 裁判、引文审计、RAG/NLI、服务层与 MCP stdio 集成。

## 贡献与许可

欢迎提交 Issue 和 Pull Request。项目以 MIT License 开源。
