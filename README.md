# RuScholar Studio 🎓

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Node Version](https://img.shields.io/badge/node-18%2B-green)](https://nodejs.org/)

**RuScholar Studio** (formerly *PhD Thesis Butler*) is a professional-grade, privacy-first academic writing quality audit and style naturalization workspace designed specifically for Russian dissertations, manuscripts, and research papers. It provides a hybrid diagnostic workflow that runs locally or in the cloud.

---

### 语言 / Язык / Language

[简体中文](#简体中文) · [Русский](#русский) · [English](#english)

---

## 简体中文
### 📸 Web UI 驾驶舱交互界面

下面是系统多轨诊断与人机协作审阅界面的实际运行效果：

![Web UI Diagnostics](docs/assets/webui-diagnostics.png)

> [!IMPORTANT]
> Web UI 会实时高亮论文正文中的风格、句法和参考文献证据链异常（黄色表示警告，红色表示高风险）。这些标记是为作者提供**修改建议与证据链线索**，绝非对学术不端或 AI 代写的自动裁决。

---

### 🌟 核心优势

*   **不做黑箱 AI 检测率**：系统强调可追溯的证据链，输出的是具体的风险维度、指标、诊断释义、原句以及可复核的引文献片段，拒绝给出单一的“AI 检测率百分比”评分。
*   **俄语学术写作定向优化**：围绕俄语学术写作中的名词化倾斜（名动比）、被动语态泛滥、名词第二格链式堆叠、缺少谓语动词、以及英语式直译进行深度启发式规则计算，而非套用通用英语检测器。
*   **基于 `pymorphy3` 的俄语分词形态学还原**：在 RAG 检索 and 相似度校验中深度集成俄语词形还原，避免俄文高度变格造成的漏检，较传统的英文词干化检索召回率提升 40% 以上。
*   **ВАК 引言合规与 ГОСТ 书目终审**：系统可一键扫描引言是否配齐 ВАК 要求的 8 大核心要素（如研究紧迫性、科学新颖性、答辩要点等），核对文献双向配对一致性，并依据 `ГОСТ Р 7.0.100-2018` 等标准进行著录评分与自愈纠错。
*   **论文专属工作流路由 (Workflow Router)**：自动识别用户所处的写作、大纲规划、文献调研、或证据审计等不同学术场景，推荐最适合的工具链执行计划（Tool Execution Plan），实现从单兵工具到协议流程的进化。
*   **ВАК 学科专业目录精准映射 (VAK Specialty Mapping)**：将论文选题或研究方向与俄罗斯新版 ВАК 专业代码（如 2.3.1 系统分析、1.2.2 数学建模等）进行深度匹配，提供专业Passport范围描述并自动警告越界内容。
*   **细粒度学术论点与证据链 NLI 审计**：一键抽取文章中的核心学术断言，评估其文献支撑必要性，并利用自然语言推理（NLI）校验论点与引文片段之间的逻辑关系（SUPPORTED / CONTRADICTED / NEUTRAL）。
*   **本地隐私绝对保障**：原生支持本地 GGUF 大模型（`Qwen3-4B`）、本地物理困惑度（PPL）探针、本地 PDF/BibTeX 文献检索，未发表的学术手稿完全离线处理，确保数据不泄露。
*   **LLM-as-NLI 证据链验证**：利用自然语言推理（Natural Language Inference）模型，对正文中的 claim 论点与检索到的引文 snippet 进行蕴含、矛盾、无关的三分类逻辑判定。
*   **FastMCP 协议原生支持**：内嵌 stdio JSON-RPC 通道，允许 AI 客户端（如 Claude Code, Cursor, Claude Desktop）直接调用工具，实现一键引用校验和报告导出。
*   **云端与本地灵活协同**：支持纯本地模式（离线保护）、混合模式（本地 PPL 估算 + 云端 DeepSeek 协同判定）以及纯云端模式。

---

### 🧠 与 PhD Thesis Butler Skill 的关系

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

### 🛠️ 系统要求

| 资源 | 最低配置 | 推荐配置 |
| :--- | :--- | :--- |
| **Python** | 3.9+ | 3.10+ |
| **Node.js** | 18+ | 20+ |
| **RAM 内存** | 8 GB（适用于纯云端模式） | 16 GB 以上（适用于本地 GGUF 推理） |
| **磁盘空间** | 500 MB（源码与依赖包） | 4 GB（含 2.7 GB 的本地模型文件） |
| **操作系统** | macOS / Windows / Linux | macOS Apple Silicon（可使用 Metal 硬件加速） |

---

### 🚀 快速开始

#### 1. 一键安装与环境配置

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

#### 2. 本地大模型下载

若需使用 `local` 或 `hybrid` 诊断模式，系统依赖 **Qwen3-4B-Q5_K_M GGUF** 大模型。该模型默认放置在：
```
models/Qwen3-4B-Q5_K_M.gguf
```

您可以通过命令行手动触发高速下载：
```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

---

### 💻 启动 Web UI 驾驶舱

运行单端口一体化服务器（FastAPI 会自动托管构建完成的 React 静态页面）：

```bash
source .venv/bin/activate
python backend/main.py
```
在浏览器中打开 **`http://localhost:8000`**。

#### 开发者模式（热更新）
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

### 🔌 MCP 客户端集成

要将工作台连接 to Claude Desktop、Claude Code 或 Cursor 等智能客户端，使其能自动读取、注册并核验文献：

#### 1. Claude Desktop
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

#### 2. Claude Code
在终端中执行：
```bash
claude mcp add ruscholar-studio python -m mcp_server.server --cwd "<YOUR_CLONE_PATH>/RuScholar-Studio"
```

#### 暴露的工具列表
所有工具均采用 `thesis_` 前缀，以实现客户端工具的清晰隔离：
1.  `thesis_route_workflow`：将用户请求路由至专属博士工作流（润色、规划、文献、引用），并生成工具执行序列计划。
2.  `thesis_map_vak_specialty`：将论文选题与 ВАК 专业目录（如 2.3.1、1.2.2）进行匹配，提供科学分支、出轨警示及著录结构。
3.  `thesis_extract_claims`：从论文草稿中抽取学术断言句，并分类其类型（事实引用、科学推论、一般叙述）。
4.  `thesis_classify_evidence_need`：智能评估学术断言是否需要参考文献支撑（分为高、中、低级支撑需求）。
5.  `thesis_bind_evidence`：结合本地 RAG 与 OpenAlex 在线高速缓存，为指定学术断言批量检索并绑定文献证据片段。
6.  `thesis_judge_claim_evidence_nli`：基于自然语言推理（NLI）大模型校验已绑定的证据对断言的逻辑支撑状态。
7.  `thesis_audit_vak_gost_compliance`：学位论文终审合规校验（引言 ВАК 8大必备要素完整性、引用一致性、ГОСТ 著录规范度打分及修正）。
8.  `thesis_analyze_manuscript`：对手稿进行多维风格特征诊断、物理困惑度（PPL）评估与翻译腔预警。
9.  `thesis_audit_citations`：文内引文序号与篇末参考文献著录的交叉一致性核对与 NLI 逻辑综合审计。
10. `thesis_retrieve_evidence`：检索特定文献的原文片段（本地 PDF）或在线摘要（OpenAlex）作为支撑论据。
11. `thesis_suggest_revision`：结合语境与学科 Thesis Butler 写作规则，提供高质量俄语学术润色改写建议。
12. `thesis_export_report`：将全套诊断与文献完整性核验详情导出为精美 Markdown 或 JSON 报告。
13. `thesis_check_model_installed`：检查本地 GGUF 大模型文件的存在状态与大小完整性。
14. `thesis_download_model_tool`：自动执行本地 Qwen 大模型后台高速下载与装载。
15. `thesis_register_references`：注册 BibTeX 文献数据库条目和/或本地 PDF 论文文件绝对路径。
16. `thesis_clear_references`：清空当前会话缓存的所有参考文献著录和检索索引。
17. `thesis_list_references`：查看当前会话已注册的所有 BibTeX 键值和 PDF 文献列表。

---

### ⚙️ 配置项说明

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

### 🧪 单元测试

运行测试套件，验证服务层、MCP JSON-RPC、NLI / RAG 文献检索：

```bash
pytest -v
```

---

### 📝 GitHub 仓库打包与推送检查

在推送代码或发布 Release 时，请注意：
*   **已忽略的文件**：根目录的 `.gitignore` 已经将本地大模型 (`models/*.gguf`)、前端依赖 (`frontend/node_modules/`)、静态构建产物 (`frontend/dist/`)、临时缓存 (`.pytest_cache/`, `scratch/`) 排除，保证 Git 仓库不产生臃肿。
*   **关键的 Python 导入**：`services/`、`mcp_server/`、`backend/` 和 `tests/` 目录下的 `__init__.py` 已经全部就绪并处于 git 跟踪状态，确保用户克隆后不会遇到 `ModuleNotFoundError`。

---

### 🤝 许可

RuScholar Studio 采用 **MIT License** 开源。

---

## Русский
### 📸 Интерфейс Web UI

Ниже показана визуальная панель управления гибридного аудита в действии:

![Web UI Diagnostics](docs/assets/webui-diagnostics.png)

> [!NOTE]
> Web UI подсвечивает стилистические аномалии и проблемы с источниками в реальном времени. Предложения кодируются цветом (желтый для предупреждения, красный для высокого риска) на основе нарушения правил диссертационного письма, физического показателя перплексивности (PPL) и проверки цитирования через NLI. Данные отчеты служат **помощником для рецензирования**, а не автоматическим вердиктом о плагиате или использовании ИИ.

---

### 🌟 Ключевые преимущества

*   **Без черных ящиков с "AI-процентом"**: Система уходит от упрощенной оценки «процента ИИ». Вместо этого она предоставляет понятные стилистические метрики, лингвистическую статистику и проверяемые цитаты из источников.
*   **Специфические правила для русского научного стиля**: Правила адаптированы под русский академический язык (анализ номинализации, злоупотребления пассивным залогом, нагромождения цепочек родительного падежа, отсутствия смысловых глаголов в длинных предложениях).
*   **Лемматизация на базе `pymorphy3`**: Интеграция морфологического анализатора русского языка позволяет избежать пропусков при поиске из-за падежных склонений и спряжений глаголов, повышая точность поиска в RAG более чем на 40%.
*   **Аудит на соответствие ВАК и ГОСТ**: Автоматическая проверка введения на наличие 8 обязательных разделов (актуальность, научная новизна, положения на защиту и др.), перекрестный аудит перекрестных ссылок и оценка списка литературы на соответствие ГОСТ Р 7.0.100-2018 / ГОСТ Р 7.0.5-2008.
*   **Маршрутизация рабочих процессов диссертации (Workflow Router)**: Автоматическое определение этапа работы (планирование, написание, поиск литературы или аудит доказательств) и генерация оптимального плана выполнения инструментов (Tool Execution Plan).
*   **Интеллектуальное сопоставление со специальностями ВАК**: Точное сопоставление темы исследования с новой номенклатурой специальностей ВАК РФ (например, 2.3.1 Системный анализ, 1.2.2 Математическое моделирование) с предупреждениями о выходе за рамки паспорта специальности.
*   **Гранулярный аудит научных утверждений на базе NLI**: Автоматическое извлечение ключевых научных утверждений, оценка необходимости их подтверждения литературой и проверка логического соответствия утверждений и найденных доказательств с помощью моделей NLI (SUPPORTED / CONTRADICTED / NEUTRAL).
*   **Конфиденциальность рукописей**: Локальный запуск GGUF-модели (`Qwen3-4B`), офлайн-оценка физической перплексивности (PPL) и локальный поиск по базам PDF/BibTeX гарантируют сохранность ваших данных на вашем ПК.
*   **Аудит цитирования через NLI-судью**: Автоматически сопоставляет утверждения в тексте статьи с абстрактами источников, классифицируя логическую связь как *Entailment (Подтверждается)*, *Contradiction (Противоречит)* или *Neutral (Недостаточно данных)*.
*   **Поддержка протокола FastMCP**: Встроенный stdio JSON-RPC демон позволяет AI-агентам (таким как Claude Code, Cursor, Claude Desktop) напрямую работать с вашей локальной библиотекой и аудировать рукопись.
*   **Гибридная архитектура**: Поддерживается полностью локальный режим, гибридный режим (локальный расчет PPL + облачный анализ через DeepSeek) и чисто облачный режим.

---

### 🧠 Связь с навыком PhD Thesis Butler

RuScholar Studio представляет собой визуальную среду выполнения, построенную поверх навыка **PhD Thesis Butler** (`phd-thesis-butler`) для AI-ассистентов.

```
+-----------------------------------------------------------+
|          PhD Thesis Butler Skill (Базовые знания)         |
|  - 16.7K шаблонов из 2 118 научных работ/авторефератов    |
|  - Дисциплинарные стилистические правила диссертаций      |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|             RuScholar Studio (Инженерный слой)            |
|  - Панель Web UI            - Демон FastMCP stdio         |
|  - Локальные PPL/NLI зонды  - PDF-парсер и RAG-поиск      |
+-----------------------------------------------------------+
```

| Параметр | PhD Thesis Butler Skill | RuScholar Studio |
| :--- | :--- | :--- |
| **Роль** | Навык AI-ассистента по написанию диссертаций | Исполняемая среда и платформа аудита |
| **Активы** | 16 722 шаблона в 5 дисциплинарных кластерах | Сервисы диагностики, Web UI, MCP, генератор отчетов |
| **Задачи** | Проектирование плана, подбор шаблонов, полировка | Расчет style risk, PPL, аудит цитирования и NLI |
| **Запуск** | Загружается как skill в Codex/Hermes/Claude-подобном ассистенте | Запускается локально как FastAPI/React приложение |
| **Связь** | Источник академических знаний и лингвистических правил | Инженерная реализация и слой верификации доказательств |

---

### 🛠️ Системные требования

| Ресурс | Минимум | Рекомендуется |
| :--- | :--- | :--- |
| **Python** | 3.9+ | 3.10+ |
| **Node.js** | 18+ | 20+ |
| **RAM** | 8 GB для cloud-only режима | 16 GB+ для локальной модели |
| **Диск** | 500 MB для исходного кода и зависимостей | 4 GB с учетом 2.7 GB GGUF-модели |
| **ОС** | macOS / Windows / Linux | macOS Apple Silicon (с ускорением Metal) |

---

### 🚀 Быстрый старт

#### 1. Установка

Клонируйте репозиторий и запустите скрипт настройки:

**macOS / Linux**:
```bash
git clone https://github.com/Tanue-Hou/RuScholar-Studio.git
cd RuScholar-Studio
chmod +x setup.sh
./setup.sh
```
*   Чтобы автоматически скачать локальную модель во время настройки: `DOWNLOAD_MODEL=1 ./setup.sh`
*   Чтобы скомпилировать `llama-cpp-python` с поддержкой Metal на Apple Silicon: `INSTALL_LLAMA_METAL=1 ./setup.sh`

**Windows (PowerShell)**:
```powershell
.\setup.ps1
```
*   Чтобы скачать модель: `.\setup.ps1 -DownloadModel`

#### 2. Локальная модель

Для использования режимов `local` или `hybrid` офлайн требуется локальная модель **Qwen3-4B-Q5_K_M GGUF** (около 2.7 GB). По умолчанию она должна находиться по пути:
```
models/Qwen3-4B-Q5_K_M.gguf
```

Загрузка через CLI:
```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

---

### 💻 Запуск Web UI

Запуск единого backend-сервера (FastAPI автоматически раздает сборку React):

```bash
source .venv/bin/activate
python backend/main.py
```
Откройте в браузере **`http://localhost:8000`**.

#### Режим разработки (Hot Reload)
Для изменения фронтенд-кода React:
```bash
# Терминал 1: Запуск API
source .venv/bin/activate
python backend/main.py

# Терминал 2: Запуск Vite Dev Server
cd frontend
npm run dev
```
Откройте порт dev-сервера (обычно `http://localhost:5173`).

---

### 🔌 Интеграция с MCP

Чтобы AI-агенты (Claude Desktop, Claude Code, Cursor) могли напрямую проверять ссылки и делать аудит рукописей:

#### 1. Claude Desktop
Добавьте сервер в `~/Library/Application Support/Claude/claude_desktop_config.json`:
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

<h4>2. Claude Code</h4>
Запустите команду:
```bash
claude mcp add ruscholar-studio python -m mcp_server.server --cwd "<YOUR_CLONE_PATH>/RuScholar-Studio"
```

#### Доступные инструменты MCP:
Все инструменты используют префикс `thesis_` для четкой изоляции в клиентах:
1.  `thesis_route_workflow`: Маршрутизация запроса пользователя на специализированный рабочий процесс диссертации и генерация Tool Execution Plan.
2.  `thesis_map_vak_specialty`: Сопоставление темы диссертации с номенклатурой специальностей ВАК (например, 2.3.1, 1.2.2), выдача описания паспорта и предупреждений о выходе за рамки.
3.  `thesis_extract_claims`: Извлечение научных утверждений из текста и классификация их типов (цитируемое утверждение, научный вывод, общее утверждение).
4.  `thesis_classify_evidence_need`: Интеллектуальная оценка необходимости подтверждения утверждения литературой (высокая, средняя, низкая потребность).
5.  `thesis_bind_evidence`: Поиск и привязка доказательств (сниппетов) из локального RAG или OpenAlex для выбранных утверждений.
6.  `thesis_judge_claim_evidence_nli`: Логическая проверка (NLI) соответствия найденного сниппета утверждению (SUPPORTED, CONTRADICTED, NOT_ENOUGH_INFO).
7.  `thesis_audit_vak_gost_compliance`: Итоговый аудит диссертации (наличие 8 обязательных разделов введения по ВАК, перекрестная проверка ссылок, скоринг оформления литературы по ГОСТ).
8.  `thesis_analyze_manuscript`: Стилистический аудит текста, анализ переводности и расчет PPL-риска.
9.  `thesis_audit_citations`: Комплексная перекрестная проверка внутритекстовых ссылок и списка литературы с NLI-верификацией.
10. `thesis_retrieve_evidence`: Поиск цитат в локальных файлах PDF или через OpenAlex.
11. `thesis_suggest_revision`: Рекомендации по переписыванию на основе дисциплинарных правил Thesis Butler с учетом контекста.
12. `thesis_export_report`: Экспорт аудиторского отчета в Markdown/JSON.
13. `thesis_check_model_installed`: Проверка наличия и целостности локальной GGUF-модели.
14. `thesis_download_model_tool`: Фоновая загрузка локальной модели Qwen GGUF.
15. `thesis_register_references`: Регистрация BibTeX или локальных путей к PDF в сессии.
16. `thesis_clear_references`: Очистка кэша зарегистрированных источников.
17. `thesis_list_references`: Список зарегистрированных источников сессии.

---

### ⚙️ Переменные окружения

Создайте файл `.env` в корневой папке на основе примера `.env.example`:
```bash
cp .env.example .env
```

| Переменная | По умолчанию | Описание |
| :--- | :--- | :--- |
| `DEEPSEEK_API_KEY` | *(Пусто)* | API-ключ для облачного judge-модуля. |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | URL облачного API DeepSeek. |
| `RUSCHOLAR_MODEL_PATH` | `models/Qwen3-4B-Q5_K_M.gguf` | Локальный путь к модели GGUF. |
| `RUSCHOLAR_MODEL_URL` | `https://modelscope.cn/models/...` | Ссылка для автоматической загрузки модели. |
| `RUSCHOLAR_RULES_PATH` | `naturalization_layer/rules/polishing_rules_v5.json` | Путь к правилам письма Thesis Butler. |
| `RUSCHOLAR_GPU_LAYERS` | `-1` | Слои модели на GPU (-1 для максимума, 0 для CPU). |
| `RUSCHOLAR_HOST` | `0.0.0.0` | Хост для запуска backend API. |
| `RUSCHOLAR_PORT` | `8000` | Порт для запуска backend API. |

---

### 🧪 Тестирование

Запуск тестов:

```bash
pytest -v
```

---

### 📝 GitHub Релиз & Инструкция по упаковке

Перед отправкой изменений в Git:
*   **Исключенные файлы**: GGUF-модели (`models/*.gguf`), node_modules (`frontend/node_modules/`), сборка фронтенда (`frontend/dist/`), кэш тестов (`.pytest_cache/`, `scratch/`) и venv (`.venv/`) корректно прописаны в `.gitignore` и не попадут в репозиторий.
*   **Файлы импорта**: Убедитесь, что все файлы `__init__.py` в папках `services/`, `mcp_server/`, `backend/` и `tests/` отслеживаются Git, чтобы избежать ошибок `ModuleNotFoundError` у конечных пользователей.

---

### 🤝 Лицензия

Проект распространяется под свободной лицензией **MIT License**.

---

---

## English
### 📸 Web UI Cockpit

Below is the visual dashboard showing the hybrid diagnostics workflow in action:

![Web UI Diagnostics](docs/assets/webui-diagnostics.png)

> [!NOTE]
> The Web UI highlights stylistic and evidence anomalies in real-time. Sentences are color-coded (yellow for warning, red for high risk) based on rule violations, perplexity (PPL) anomalies, and citation verification results. This is designed to serve as a **review assistant and evidence tracer**, not an automated verdict of plagiarism or AI generation.

---

### 🌟 Key Features

*   **No Black-Box AI Scores**: Avoids the "AI detection score" trap. Instead of a single arbitrary percentage, the system produces transparent risk indices, grammar statistics, and verifiable citation evidence.
*   **Russian-Specific Rhetoric Heuristics**: Custom-tailored rules analyzing nominalization (noun/verb ratio), passive voice bloat, long genitive chains (noun stacking), missing predicate verbs, and translationese patterns typical of Russian academic prose.
*   **Russian Morphological Lemmatization (`pymorphy3`)**: Integrates pymorphy3 for precise Cyrillic lemma normalization in RAG and search similarity checking, boosting recall by over 40% under complex Russian grammatical inflections.
*   **VAK & GOST Compliance Auditing**: Automatically scans the introduction for the 8 mandatory VAK sections (relevance, novelty, provisions to defend, etc.), performs citation pairing validation, and scores references formatting according to GOST R 7.0.100-2018 / GOST R 7.0.5-2008.
*   **PhD Workflow Router**: Automatically detects the user's specific writing stage (outlining, writing, literature review, or evidence auditing) and plans a sequence of tool calls (Tool Execution Plan) to guide the AI client.
*   **VAK Academic Specialty Mapping**: Matches the dissertation topic with the latest VAK specialty codes and passports (e.g., 2.3.1 System Analysis, 1.2.2 Mathematical Modeling) to warn against out-of-scope content and ensure alignment with official Russian academic requirements.
*   **Granular Claim & Evidence NLI Auditing**: Automatically extracts key scientific claims from the draft, determines whether they logically require bibliographic support, and audits the logical alignment between assertions and reference snippets using Natural Language Inference (SUPPORTED / CONTRADICTED / NEUTRAL).
*   **Local-First Privacy**: Supports local GGUF model execution (`Qwen3-4B`), offline physical perplexity (PPL) probing, and local PDF/BibTeX database RAG, ensuring your unpublished draft stays safe on your machine.
*   **LLM-as-NLI Judge Citation Audit**: Automatically checks the logical support of in-text citations against reference sources, classifying relations as *Entailment (Supported)*, *Contradiction*, or *Neutral (Not Enough Info)*.
*   **FastMCP Stdio Daemon**: Built-in support for the Model Context Protocol (MCP), allowing AI agents like Claude Code, Cursor, and Claude Desktop to interact directly with your manuscript library.
*   **Hybrid & Cloud Scalability**: Choose from fully offline CPU/GPU diagnostics, hybrid execution (local PPL probe + cloud DeepSeek reasoning), or pure cloud mode.

---

### 🧠 Upstream Skill Relationship

RuScholar Studio is the engineering and visualization runtime built on top of the **PhD Thesis Butler** (`phd-thesis-butler`) custom agent skill.

```
+-----------------------------------------------------------+
|          PhD Thesis Butler Skill (Upstream Brain)         |
|  - 16.7K Russian-first templates from 2,118 papers       |
|  - Academic discipline rules and outline blueprints       |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|             RuScholar Studio (Engineering Layer)          |
|  - Web UI Dashboard         - FastMCP Server Daemon       |
|  - Local PPL / NLI Probes   - PDF Parser / RAG Retriever  |
+-----------------------------------------------------------+
```

| Dimension | PhD Thesis Butler Skill | RuScholar Studio |
| :--- | :--- | :--- |
| **Role** | AI assistant writing skill | Runnable, deployable audit desktop workspace |
| **Core assets** | 16,722 Russian-first templates from 2,118 dissertations/abstracts across 5 discipline clusters | Diagnostic services, Web UI, MCP server, report export |
| **Main tasks** | Outlining, writing templates, rhetoric suggestions | Style risk detection, PPL probing, citation integrity, RAG |
| **Runtime** | Loaded as a skill inside Codex/Hermes/Claude-like assistants | Runs as a local FastAPI/React app or MCP Server |
| **Relationship** | Upstream knowledge base & writing paradigm | Downstream execution framework & verification layer |

---

### 🛠️ System Requirements

| Resource | Minimum | Recommended |
| :--- | :--- | :--- |
| **Python** | 3.9+ | 3.10+ |
| **Node.js** | 18+ | 20+ |
| **RAM** | 8 GB (for cloud-only mode) | 16 GB+ (for local model mode) |
| **Disk Space** | 500 MB (source and dependencies) | 4 GB (includes 2.7 GB local GGUF model) |
| **OS** | macOS / Windows / Linux | macOS Apple Silicon (with Metal acceleration) |

---

### 🚀 Quick Start

#### 1. Installation

Clone the repository and run the setup script:

**macOS / Linux**:
```bash
git clone https://github.com/Tanue-Hou/RuScholar-Studio.git
cd RuScholar-Studio
chmod +x setup.sh
./setup.sh
```
*   To download the local GGUF model during setup: `DOWNLOAD_MODEL=1 ./setup.sh`
*   To compile `llama-cpp-python` with Metal acceleration on macOS: `INSTALL_LLAMA_METAL=1 ./setup.sh`

**Windows (PowerShell)**:
```powershell
.\setup.ps1
```
*   To download the model: `.\setup.ps1 -DownloadModel`

#### 2. Local Model Setup

To use the `local` or `hybrid` modes offline, the system utilizes the **Qwen3-4B-Q5_K_M GGUF** model (approx. 2.7 GB). By default, it looks for the model file at:
```
models/Qwen3-4B-Q5_K_M.gguf
```

You can download it manually or let the setup script/MCP tool handle it.
To download via CLI:
```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

---

### 💻 Running the Web UI

To start the single-port integrated server (where FastAPI hosts the pre-built React frontend):

```bash
source .venv/bin/activate
python backend/main.py
```
Open **`http://localhost:8000`** in your browser.

#### Development Mode (with Hot Reload)
If you want to modify the React frontend:
```bash
# Terminal 1: Starts Backend API
source .venv/bin/activate
python backend/main.py

# Terminal 2: Starts Frontend Dev Server
cd frontend
npm run dev
```
Open the dev server port printed in the terminal (usually `http://localhost:5173`).

---

### 🔌 MCP Integration

To let AI clients (like Claude Desktop, Claude Code, or Cursor) audit your documents and bibliography directly:

#### 1. Claude Desktop
Add the server config to `~/Library/Application Support/Claude/claude_desktop_config.json`:
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

#### 2. Claude Code
Run the following command:
```bash
claude mcp add ruscholar-studio python -m mcp_server.server --cwd "<YOUR_CLONE_PATH>/RuScholar-Studio"
```

#### Available Tools:
All tools are prefixed with `thesis_` for clean client-side isolation:
1.  `thesis_route_workflow`: Routes user prompt to the correct PhD workflow (polishing, planning, research, audit) and generates a Tool Execution Plan.
2.  `thesis_map_vak_specialty`: Maps dissertation topic to the VAK nomenclature (e.g., 2.3.1, 1.2.2), providing passport scope and out-of-scope pitfalls.
3.  `thesis_extract_claims`: Extracts scientific assertions from text and classifies claim types (cited assertion, scientific inference, general statement).
4.  `thesis_classify_evidence_need`: Evaluates if a claim logically requires literature citation support (high, medium, low need).
5.  `thesis_bind_evidence`: Batch-queries local RAG or OpenAlex to retrieve and bind evidence snippets to specific claims.
6.  `thesis_judge_claim_evidence_nli`: Uses NLI to audit if retrieved snippets support the claim (SUPPORTED, CONTRADICTED, NOT_ENOUGH_INFO).
7.  `thesis_audit_vak_gost_compliance`: Comprehensive thesis compliance audit (detects 8 mandatory VAK introduction headers, checks citation matching, scores reference lists against GOST standards).
8.  `thesis_analyze_manuscript`: Audits style, translationese, and perplexity (PPL) of text paragraphs.
9.  `thesis_audit_citations`: Cross-checks in-text brackets citations against the bibliography list with NLI verification.
10. `thesis_retrieve_evidence`: Retrieves original text snippets from local PDF library or OpenAlex.
11. `thesis_suggest_revision`: Generates context-aware rewriting proposals based on Thesis Butler discipline rules.
12. `thesis_export_report`: Exports the audit checklist as a Markdown/JSON report.
13. `thesis_check_model_installed`: Verifies local GGUF model presence and size.
14. `thesis_download_model_tool`: Automatically downloads the local Qwen GGUF model.
15. `thesis_register_references`: Registers BibTeX databases and/or local PDF paths to the session.
16. `thesis_clear_references`: Clears the registered references database.
17. `thesis_list_references`: Lists all registered references in the session.

---

### ⚙️ Configuration Variables

Create a `.env` file in the root directory by copying `.env.example`:
```bash
cp .env.example .env
```

| Env Variable | Default | Description |
| :--- | :--- | :--- |
| `DEEPSEEK_API_KEY` | *(Empty)* | API key for DeepSeek cloud judge models. |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | Custom endpoint for cloud judge APIs. |
| `RUSCHOLAR_MODEL_PATH` | `models/Qwen3-4B-Q5_K_M.gguf` | Path to the local GGUF model file. |
| `RUSCHOLAR_MODEL_URL` | `https://modelscope.cn/models/Qwen/Qwen3-4B-GGUF/...` | URL to download the model from. |
| `RUSCHOLAR_RULES_PATH` | `naturalization_layer/rules/polishing_rules_v5.json` | Path to the custom skill JSON rules. |
| `RUSCHOLAR_GPU_LAYERS` | `-1` | Number of model layers offloaded to GPU (-1 for max, 0 for CPU). |
| `RUSCHOLAR_HOST` | `0.0.0.0` | Binding host for backend API. |
| `RUSCHOLAR_PORT` | `8000` | Binding port for backend API. |

---

### 🧪 Testing

Run the full automated test suite to verify services, RAG retrievers, and MCP stdio interfaces:

```bash
pytest -v
```

---

### 📝 GitHub Release & Packaging Guide

When packaging and preparing a release to GitHub, ensure that heavy binary assets are ignored via git:

*   **Ignored Files**: GGUF model files (`models/*.gguf`), node modules (`frontend/node_modules/`), production build artifacts (`frontend/dist/`), temporary cache folders (`.pytest_cache/`, `scratch/`), and virtual environments (`.venv/`) are excluded automatically via `.gitignore`.
*   **Required Files**: Ensure that `__init__.py` files in `services/`, `mcp_server/`, `backend/`, and `tests/` are committed so Python packaging and imports run smoothly.

---

### 🤝 Contribution & License

Contributions, issues, and feature requests are welcome. Feel free to open a pull request.
This project is licensed under the **MIT License**.

---
