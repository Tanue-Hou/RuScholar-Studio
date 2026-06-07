# PhD Thesis Butler - 证据驱动的学术写作质量审计系统 (README_ZH)

本系统是一款专为学术手稿、博士论文及科研论文设计的**学术写作质量审计系统**。它摆脱了传统的“AI 检测率评分”陷阱，升级为**“本地规则引擎 + 本地/在线文献检索 + LLM-as-NLI Judge 证据审计”**的可追溯验证架构。

本系统原生支持 **MCP (Model Context Protocol) 协议**，使 Claude Code、Cursor、Claude Desktop 等 AI Agent 可以调用本地工具直接对您的本地学术手稿进行离线诊断。

---

## 💡 本地大模型（物理基石）配置指南

为保护研究者的论文手稿隐私，系统的**本地困惑度 (PPL) 探针**与**自然语言推理 (NLI) 证据审计**核心算法依赖本地部署的 **Qwen3-4B GGUF** 大模型。如果本地没有该模型，您将无法使用 `local` 和 `hybrid` 诊断模式。

我们提供了**三种极速下载与安装大模型的方式**：

### 1. 终端命令行一键下载（推荐）
在项目根目录下，直接在终端中运行以下 Python 命令，系统会自动从 ModelScope 高速节点下载 `Qwen3-4B-Q5_K_M.gguf` 模型（约 2.7 GB）并自动放置在正确路径：
```bash
python -c "from naturalization_layer.model_downloader import download_model, MODEL_PATH; download_model(MODEL_PATH)"
```

### 2. AI Agent 自动一键下载 (MCP 模式)
如果您将本项目作为 MCP Server 接入了 **Claude Code / Cursor / Claude Desktop**，当您在模型尚未下载时尝试调用诊断，AI 客户端会接收到一条极其人性化的报错指引。
此时，AI Agent 会自动发现并建议您调用 [`download_model_tool`](file:///Users/tanue/Documents/antigravity/friendly-lavoisier/mcp_server/server.py#L358) 工具。您只需确认，Agent 就会自动在后台静默下载并完成配置，实现全自动零摩擦上手。

您也可以随时让 AI Agent 调用 [`check_model_installed`](file:///Users/tanue/Documents/antigravity/friendly-lavoisier/mcp_server/server.py#L320) 工具来查看模型的安装状态和预计大小。

### 3. 手动下载与放置
若需要手动下载，请访问 ModelScope 节点：
*   **下载地址**：[Qwen3-4B-Q5_K_M.gguf (ModelScope)](https://modelscope.cn/models/Qwen/Qwen3-4B-GGUF/resolve/master/Qwen3-4B-Q5_K_M.gguf)
*   **目标存放路径**：`models/Qwen3-4B-Q5_K_M.gguf`（如不存在 `models` 文件夹，请先创建）。

---

## 🛠️ MCP (Model Context Protocol) 集成

本系统暴露了 7 个强大的 MCP 本地工具，供 AI 客户端直接调用：

1.  [`check_model_installed`](file:///Users/tanue/Documents/antigravity/friendly-lavoisier/mcp_server/server.py#L320)：校验本地大模型是否存在及大小是否一致。
2.  [`download_model_tool`](file:///Users/tanue/Documents/antigravity/friendly-lavoisier/mcp_server/server.py#L358)：通过 ModelScope 在线下载 2.7GB 大模型到本地。
3.  [`analyze_manuscript`](file:///Users/tanue/Documents/antigravity/friendly-lavoisier/mcp_server/server.py#L56)：对论文段落进行深度学术风格诊断（包含翻译腔、名词堆叠、PPL 风险评估）。
4.  [`audit_citations`](file:///Users/tanue/Documents/antigravity/friendly-lavoisier/mcp_server/server.py#L107)：自动交叉核验正文引文标号与文末参考文献的一致性，抓取幻觉文献。
5.  [`retrieve_evidence`](file:///Users/tanue/Documents/antigravity/friendly-lavoisier/mcp_server/server.py#L164)：通过本地文献库（BibTeX/PDF）或在线 OpenAlex 数据库抓取特定的学术论点证据片段。
6.  [`suggest_revision`](file:///Users/tanue/Documents/antigravity/friendly-lavoisier/mcp_server/server.py#L236)：结合前后文与学科特定修辞规则，为被警告的句子生成学术重写与润色建议。
7.  [`export_report`](file:///Users/tanue/Documents/antigravity/friendly-lavoisier/mcp_server/server.py#L301)：生成 Markdown 格式的学术审计与质量自查报告。

### 在 AI 客户端中配置

#### ① 在 Claude Desktop 中配置
在 `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) 中加入以下配置：
```json
{
  "mcpServers": {
    "thesis-butler": {
      "command": "python",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "cwd": "/Users/tanue/Documents/antigravity/friendly-lavoisier"
    }
  }
}
```

#### ② 在 Claude Code 中配置
在终端中运行：
```bash
claude mcp add thesis-butler python -m mcp_server.server --cwd "/Users/tanue/Documents/antigravity/friendly-lavoisier"
```

---

## 🚀 Web UI 启动与开发

如果您习惯使用图形化的驾驶舱进行可视化分析与参考文献管理：

1.  **启动后端服务 (FastAPI)**：
    ```bash
    uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
    ```
2.  **启动前端 Web (Vite + TS + React)**：
    ```bash
    cd frontend
    npm run dev
    ```
    启动后访问 Web UI。在左侧控制台，您可以配置并上传本地 `.bib` 或 `.pdf` 参考文献库，并在右侧直接对比您的学术声称与文献中的真实证据段落。

---

## 🧪 自动化测试验证

若要验证系统各模块及 MCP stdio 通信的稳定性，请运行：
```bash
pytest tests/test_services_and_mcp.py -v
```
本系统的自动化测试套件已实现 100% 测试覆盖与绿色通过。
