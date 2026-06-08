# RuScholar Studio 🎓

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Node Version](https://img.shields.io/badge/node-18%2B-green)](https://nodejs.org/)

**RuScholar Studio**（原名 *PhD Thesis Butler*，即博士论文管家）是一款专为俄语学术手稿、博士学位论文及科研论文设计的、保护隐私的**学术写作质量审计与自然化润色工作台**。它支持本地离线或云端协同的多轨诊断流。

---

### Language / Язык / 语言

[English](README.md) · [Русский](README_RU.md) · [简体中文](README_ZH.md)

---

## 📸 Web UI 驾驶舱交互界面

下面是系统多轨诊断与人机协作审阅界面的实际运行效果：

![Web UI Diagnostics](docs/assets/webui-diagnostics.png)

> [!IMPORTANT]
> Web UI 会实时高亮论文正文中的风格、句法和参考文献证据链异常（黄色表示警告，红色表示高风险）。这些标记是为作者提供**修改建议与证据链线索**，绝非对学术不端或 AI 代写的自动裁决。

---

## 🌟 核心优势

*   **不做黑箱 AI 检测率**：系统强调可追溯的证据链，输出的是具体的风险维度、指标、诊断释义、原句以及可复核的引文献片段，拒绝给出单一的“AI 检测率百分比”评分。
*   **俄语学术写作定向优化**：围绕俄语学术写作中的名词化倾斜（名动比）、被动语态泛滥、名词第二格链式堆叠、缺少谓语动词、以及英语式直译进行深度启发式规则计算，而非套用通用英语检测器。
*   **本地隐私绝对保障**：原生支持本地 GGUF 大模型（`Qwen3-4B`）、本地物理困惑度（PPL）探针、本地 PDF/BibTeX 文献检索，未发表的学术手稿完全离线处理，确保数据不泄露。
*   **LLM-as-NLI 证据链验证**：利用自然语言推理（Natural Language Inference）模型，对正文中的 claim 论点与检索到的引文 snippet 进行蕴含、矛盾、无关的三分类逻辑判定。
*   **FastMCP 协议原生支持**：内嵌 stdio JSON-RPC 通道，允许 AI 客户端（如 Claude Code, Cursor, Claude Desktop）直接调用工具，实现一键引用校验和报告导出。
*   **云端与本地灵活协同**：支持纯本地模式（离线保护）、混合模式（本地 PPL 估算 + 云端 DeepSeek 协同判定）以及纯云端模式。

---

## 🧠 与 PhD Thesis Butler Skill 的关系

RuScholar Studio 是在 **PhD Thesis Butler** (`phd-thesis-butler`) 自定义 AI Agent Skill 知识资产之上建立的可视化工程执行层。

```
+-----------------------------------------------------------+
|          PhD Thesis Butler Skill (上游大脑知识库)         |
|  - 拥有 16.7K 条俄语学术范式模板，提炼自 2,118 篇论文    |
|  - 提供学术大纲规划、段落句式推荐、学术修辞规则            |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|            RuScholar Studio (下游可视化与工程执行层)      |
|  - Web UI 审阅面板           - FastMCP 本地后台 daemon     |
|  - 本地 PPL / NLI 物理探针    - PDF 解析器 & BM25 检索      |
+-----------------------------------------------------------+
```

| 维度 | PhD Thesis Butler Skill | RuScholar Studio |
| :--- | :--- | :--- |
| **定位** | AI 助手加载的俄语学术写作技能库 (Skill) | 可 clone、可运行、可部署的审计与润色工作台 |
| **核心资产** | 16,722 条俄语学术模板，覆盖 5 大理/工/文/社学科簇 | 诊断服务、Web UI 页面、MCP 服务端、报告生成器 |
| **核心任务** | 章节大纲设计、论点角色分配、句法结构润色 | 风格风险检测、物理 PPL 探针、引文一致性、NLI 逻辑审计 |
| **运行方式** | 作为 Codex/Hermes/Claude 类助手的 skill 加载 | 作为本地 FastAPI 后端及 React 页面运行 |
| **上下游关系** | 提供上游学术知识和修辞范式 | 提供下游工程化执行、算法审计与可视化展示 |

---

## 🛠️ 系统要求

| 资源 | 最低配置 | 推荐配置 |
| :--- | :--- | :--- |
| **Python** | 3.9+ | 3.10+ |
| **Node.js** | 18+ | 20+ |
| **RAM 内存** | 8 GB（适用于纯云端模式） | 16 GB 以上（适用于本地 GGUF 推理） |
| **磁盘空间** | 500 MB（源码与依赖包） | 4 GB（含 2.7 GB 的本地模型文件） |
| **操作系统** | macOS / Windows / Linux | macOS Apple Silicon（可使用 Metal 硬件加速） |

---

## 🚀 快速开始

### 1. 一键安装与环境配置

克隆仓库并运行一键配置脚本：

**macOS / Linux**:
```bash
git clone https://github.com/Tanue-Hou/RuScholar-Studio.git
cd RuScholar-Studio
chmod +x setup.sh
./setup.sh
```
*   如果要在安装时自动下载 2.7 GB 本地模型：`DOWNLOAD_MODEL=1 ./setup.sh`
*   Apple Silicon 用户如果想编译支持 Metal 硬件加速：`INSTALL_LLAMA_METAL=1 ./setup.sh`

**Windows (PowerShell)**:
```powershell
.\setup.ps1
```
*   下载模型：`.\setup.ps1 -DownloadModel`

### 2. 本地大模型下载

若需使用 `local` 或 `hybrid` 诊断模式，系统依赖 **Qwen3-4B-Q5_K_M GGUF** 大模型。该模型默认放置在：
```
models/Qwen3-4B-Q5_K_M.gguf
```

您可以通过命令行手动触发高速下载：
```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

---

## 💻 启动 Web UI 驾驶舱

运行单端口一体化服务器（FastAPI 会自动托管构建完成的 React 静态页面）：

```bash
source .venv/bin/activate
python backend/main.py
```
在浏览器中打开 **`http://localhost:8000`**。

### 开发者模式（热更新）
若要对前端 React 代码进行修改和调试：
```bash
# 终端 1: 启动后端 API 服务
source .venv/bin/activate
python backend/main.py

# 终端 2: 启动前端 Vite 调试服务
cd frontend
npm run dev
```
打开输出的开发服务器地址（通常是 `http://localhost:5173`）。

---

## 🔌 MCP 客户端集成

要将工作台连接到 Claude Desktop、Claude Code 或 Cursor 等智能客户端，使其能自动读取、注册并核验文献：

### 1. Claude Desktop
在 `~/Library/Application Support/Claude/claude_desktop_config.json` 中添加：
```json
{
  "mcpServers": {
    "ruscholar-studio": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "<YOUR_CLONE_PATH>/RuScholar-Studio"
    }
  }
}
```

### 2. Claude Code
在终端中执行：
```bash
claude mcp add ruscholar-studio python -m mcp_server.server --cwd "<YOUR_CLONE_PATH>/RuScholar-Studio"
```

### 暴露的工具列表
1.  `analyze_manuscript`：对学术手稿进行句式、PPL 困惑度以及翻译腔分析。
2.  `audit_citations`：交叉校验文内引用序号与篇末参考文献列表的对应关系。
3.  `retrieve_evidence`：从本地 PDF/BibTeX 文件库或在线 OpenAlex 接口抓取文献原句作为论据支撑。
4.  `suggest_revision`：结合上下文和学科规则对问题句进行重写润色。
5.  `export_report`：将当前诊断结果导出为 Markdown/JSON 格式报告。
6.  `check_model_installed`：检测本地大模型文件状态与大小。
7.  `download_model_tool`：自动执行 Qwen 本地大模型下载。
8.  `register_references`：注册 BibTeX 文本和/或本地 PDF 物理路径到会话。
9.  `clear_references`：清除当前会话缓存的文献。
10. `list_references`：列出当前会话已注册的文献库。

---

## ⚙️ 配置项说明

在项目根目录下复制 `.env.example` 并重命名为 `.env`：
```bash
cp .env.example .env
```

| 环境变量名 | 默认值 | 作用与配置说明 |
| :--- | :--- | :--- |
| `DEEPSEEK_API_KEY` | *(空)* | 云端 Judge 推理时所需的 API Key。 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | 兼容 OpenAI 格式的云端大模型接口地址。 |
| `RUSCHOLAR_MODEL_PATH` | `models/Qwen3-4B-Q5_K_M.gguf` | 本地 GGUF 大模型文件的物理存放路径。 |
| `RUSCHOLAR_MODEL_URL` | `https://modelscope.cn/models/...` | 自动下载本地大模型时所用的 ModelScope 节点 URL。 |
| `RUSCHOLAR_RULES_PATH` | `naturalization_layer/rules/polishing_rules_v5.json` | 学科写作规范及学术模板数据库路径。 |
| `RUSCHOLAR_GPU_LAYERS` | `-1` | 物理 PPL 探针推理时的 GPU 卸载层数（-1 表示最大，0 表示纯 CPU）。 |
| `RUSCHOLAR_HOST` | `0.0.0.0` | 后端服务器绑定的 host。 |
| `RUSCHOLAR_PORT` | `8000` | 后端服务器绑定的 port。 |

---

## 🧪 单元测试

运行测试套件，验证服务层、MCP JSON-RPC、NLI / RAG 文献检索：

```bash
pytest -v
```

---

## 📝 GitHub 仓库打包与推送检查

在推送代码或发布 Release 时，请注意：
*   **已忽略的文件**：根目录的 `.gitignore` 已经将本地大模型 (`models/*.gguf`)、前端依赖 (`frontend/node_modules/`)、静态构建产物 (`frontend/dist/`)、临时缓存 (`.pytest_cache/`, `scratch/`) 排除，保证 Git 仓库不产生臃肿。
*   **关键的 Python 导入**：`services/`、`mcp_server/`、`backend/` 和 `tests/` 目录下的 `__init__.py` 已经全部就绪并处于 git 跟踪状态，确保用户克隆后不会遇到 `ModuleNotFoundError`。

---

## 🤝 许可

RuScholar Studio 采用 **MIT License** 开源。
