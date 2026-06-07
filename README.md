# PhD Thesis Butler v5.4.1

Russian dissertation planning, evidence-aware revision, citation auditing, and academic polishing system for AI assistants such as Codex, Claude Code, Cursor, Claude Desktop, and Antigravity.

[中文](#中文) · [Русский](#русский) · [English](#english)

![Web UI diagnostics](docs/assets/webui-diagnostics.png)

The Web UI shows the hybrid diagnostic workflow: manuscript text with sentence-level highlights, discipline detection, average PPL, style risk, predictability risk, translationese risk, redundancy risk, and sentence-level reasoning. Yellow and red highlights are review signals, not final misconduct judgments.

---

## 中文

证据驱动的学术写作质量审计系统，面向博士论文、学术手稿与科研论文。项目延续原有 **PhD Thesis Butler** skill 的算法与写作规则资产，并扩展为 **RuScholar Studio**：同时支持 Web UI、人机协同审阅和 MCP Agent 工具调用的本地研究写作工作台。

本系统刻意避开传统“AI 检测率评分”的陷阱，采用 **本地规则引擎 + 本地 PPL 探针 + 本地/在线文献检索 + LLM-as-NLI Judge 证据审计** 的可追溯验证架构。系统输出应被理解为风险信号和证据链提示，而不是对 AI 代写、剽窃或学术不端的自动裁决。

版本命名沿用源 skill 的迭代脉络：本地 `phd-thesis-butler` skill 当前为 `v5.3.0`，本仓库在它的知识资产和写作规则之上加入 Web UI、MCP、共享服务层、本地 PPL/NLI 执行、GitHub 安装脚本和三语文档，因此命名为 `v5.4.1`。

### 与博士论文管家 Skill 的关系

`博士论文管家` / `phd-thesis-butler` skill 是本项目的源能力层。它提供论文写作智能、俄语句式库、规划层、研究层和证据层；RuScholar Studio 则把这些能力工程化为可运行、可审计、可通过 WebUI 和 MCP 调用的工具系统。

| 层级 | 博士论文管家 Skill | RuScholar Studio |
|------|-------------------|------------------|
| 定位 | AI 助手加载的俄语博士论文写作 skill | 可 clone、可运行、可部署的审计工作台 |
| 核心资产 | 16,722 条 Russian-first templates，来自 2,118 篇论文/摘要，覆盖 5 个学科簇 | 诊断服务、Web UI、MCP Server、本地模型接口、报告导出 |
| 主要任务 | 论文规划、章节蓝图、句式检索、俄语学术表达润色、证据角色绑定 | 风格风险检测、PPL 探针、引用完整性审计、RAG 检索、NLI 证据核验 |
| 运行方式 | 作为 Codex/Hermes/Claude 类助手的 skill 被加载 | 作为本地 FastAPI/React 应用或 MCP Server 被调用 |
| 关系 | 上游知识与写作范式来源 | 下游工程化执行层和证据链审计层 |

一句话概括：**博士论文管家 Skill 是“写作与规划大脑”，RuScholar Studio 是“可视化审计仪表盘 + Agent 工具执行器”。** 二者不是替代关系，而是上下游协同关系。

### 系统架构

PhD Thesis Butler / RuScholar Studio 采用“共享服务层 + 双入口”的架构。Web UI 和 MCP Server 不各自实现逻辑，而是共同调用 `services/` 中的诊断、文献、报告和会话能力，核心算法则沉淀在 `naturalization_layer/` 中。

```text
Web UI (FastAPI + React)
        |
        v
Shared Services
diagnostic_service / citation_audit_service / report_service / shared_state
        |
        v
Naturalization Layer
rules_engine / ppl_engine / llm_judge / nli_judge / rag_retriever / citation_integrity
        |
        v
Evidence Sources
Local GGUF Model / BibTeX / PDF / OpenAlex / DeepSeek-compatible API

MCP Server
        |
        +-- analyze_manuscript
        +-- audit_citations
        +-- retrieve_evidence
        +-- suggest_revision
        +-- export_report
        +-- model and reference management tools
```

这套架构的关键点是：WebUI 面向人工审阅，MCP 面向 AI Agent 协作，但二者共享同一套判定逻辑、同一套引用缓存和同一套报告出口，避免前端产品和 Agent 工具各走一套标准。

### 核心优势

- **不做黑箱 AI 检测率**：系统强调可追溯证据链，输出的是风险类型、指标、解释、原句和可复核证据，而不是单一百分比。
- **俄语学术写作定向优化**：围绕俄语论文中的名词化、第二格链、被动结构、翻译腔和学术套话设计规则，而不是套用通用英文写作检测器。
- **本地隐私优先**：支持本地 GGUF 模型、本地 PPL 探针、本地 PDF/BibTeX 检索；敏感论文可以不上传云端。
- **软硬结合的多轨判断**：规则特征、概率特征、文献一致性和 NLI 证据审计互相校验，降低单一模型误报。
- **面向 Agent 的工具化能力**：MCP 工具让 Claude Code、Codex、Cursor 等客户端可以直接注册文献、检索证据、审计引用并生成报告。
- **WebUI 与 MCP 并存**：人工读者可以在浏览器里看高亮与解释，AI 助手可以通过 MCP 自动处理批量审计任务。

### 版本迭代

| 版本阶段 | 核心变化 | 解决的问题 |
|----------|----------|------------|
| v1.x 基础规则层 | 正则、spaCy POS、名动比、连接词与套话扫描 | 建立最早的俄语学术风格风险提示 |
| v2.x LLM Judge 层 | 引入本地/云端风格裁判与上下文窗口 | 降低只看单句导致的断章取义 |
| v3.x PPL 概率层 | 引入 GGUF 本地 PPL、学科阈值校准 | 从概率角度识别过度可预测或翻译滞涩文本 |
| v4.x 性能与保护层 | Early Exit、LaTeX/图表保护、SSE 流式响应 | 降低本地模型负载，提升 WebUI 实时体验 |
| v5.1.3 规则资产层 | `polishing_rules_v5.json` 形成稳定规则资产 | 沉淀 PhD Thesis Butler skill 的学科写作规则 |
| v5.2 研究层 | 加入研究规划、检索查询、eLIBRARY/DisserCat/CyberLeninka/OpenAlex 等来源策略 | 让论文写作从句式润色扩展到文献研究支持 |
| v5.3.0 证据感知写作层 | 加入 evidence roles、章节证据绑定、citation gap 判断 | 让 skill 能识别 claim 是否需要文献支撑 |
| v5.4.1 工程化协同版 | WebUI + MCP + 共享 services + 本地 PPL/NLI + GitHub 安装与三语同页 README | 将 skill 能力升级为可 clone、可部署、可由 Agent 调用的完整审计工具 |

### 系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| Python | 3.9+ | 3.10+ |
| Node.js | 18+ | 20+ |
| RAM | 8 GB，适合纯云端模式 | 16 GB，本地模型模式 |
| 磁盘空间 | 500 MB，源码与依赖 | 4 GB，含 2.7 GB GGUF 模型 |
| 操作系统 | macOS / Linux / Windows | macOS Apple Silicon + Metal |

macOS Apple Silicon 用户可使用 Metal 加速；Linux/Windows 用户如不希望编译本地模型依赖，可优先使用 `cloud-pro` 或 `cloud-flash` 模式。

### 快速开始

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

### 本地大模型说明

为保护研究者论文手稿隐私，系统的本地 PPL 探针与本地 NLI/风格裁判可以依赖 **Qwen3-4B-Q5_K_M GGUF** 模型。模型约 2.7 GB，默认下载到：

```text
models/Qwen3-4B-Q5_K_M.gguf
```

手动下载：

```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

也可以通过 MCP 工具 `download_model_tool` 让 AI 客户端触发下载。如果本地没有模型，`local` 与 `hybrid` 模式不可用，但纯云端模式仍可运行。

### Web UI 启动

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

### MCP 集成

本系统原生支持 **MCP (Model Context Protocol)**，使 Claude Code、Cursor、Claude Desktop、Codex 等 AI Agent 可以直接调用本地工具，对本地学术手稿进行离线或混合诊断。

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

### 诊断机制

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

### 运行模式

| 模式 | 本地 PPL | LLM 裁判 | 适用场景 |
|------|---------|---------|---------|
| `local` | 是 | 本地 Qwen | 完全离线，保护隐私 |
| `hybrid-pro` | 是 | DeepSeek Pro | 本地概率探针 + 云端深度分析 |
| `hybrid-flash` | 是 | DeepSeek Flash | 本地概率探针 + 云端快速分析 |
| `cloud-pro` | 否 | DeepSeek Pro | 无本地模型，纯云端深度诊断 |
| `cloud-flash` | 否 | DeepSeek Flash | 无本地模型，纯云端快速诊断 |

### 配置项

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

### 测试验证

```bash
pytest -q
cd frontend && npm run build
```

当前测试覆盖规则引擎、PPL 引擎、LLM 裁判、引文审计、RAG/NLI、服务层与 MCP stdio 集成。

### 贡献与许可

欢迎提交 Issue 和 Pull Request。项目以 MIT License 开源。

---

## Русский

Система доказательного аудита академического письма для диссертаций, рукописей и научных статей. Проект продолжает исходный навык **PhD Thesis Butler** и оформляет его как **RuScholar Studio**: локальную рабочую среду исследователя с Web UI и MCP-инструментами для AI-агентов.

Система не сводит анализ к простому "проценту AI-текста". Вместо этого используется трассируемая архитектура: **локальный rule engine, локальный PPL-зонд, локальный/онлайн поиск источников и LLM-as-NLI аудит цитирования**. Результаты следует рассматривать как сигналы риска и доказательную цепочку, а не как автоматический вердикт о нарушении.

Именование версии следует линии исходного skill: локальный `phd-thesis-butler` skill сейчас имеет версию `v5.3.0`; этот репозиторий добавляет Web UI, MCP, общий service layer, локальное PPL/NLI выполнение, GitHub setup scripts и трехъязычную документацию, поэтому релиз назван `v5.4.1`.

### Связь с PhD Thesis Butler Skill

`PhD Thesis Butler` / `博士论文管家` skill является исходным слоем знаний этого проекта. Он содержит writing intelligence, русскоязычные шаблоны, planning layer, research layer и evidence layer. RuScholar Studio превращает эти возможности в исполняемую систему с Web UI, MCP и проверяемой evidence trail.

| Уровень | PhD Thesis Butler Skill | RuScholar Studio |
|---------|-------------------------|------------------|
| Роль | Skill для AI-ассистента по русским диссертациям | Локальная платформа аудита, которую можно clone/run/deploy |
| Активы | 16 722 Russian-first templates из 2 118 диссертаций/авторефератов, 5 дисциплинарных кластеров | Diagnostic services, Web UI, MCP Server, local model bridge, report export |
| Задачи | Планирование диссертации, chapter blueprint, поиск формулировок, академическая полировка, evidence-role binding | Style risk, PPL probe, citation integrity, RAG retrieval, NLI evidence audit |
| Запуск | Загружается как skill в Codex/Hermes/Claude-подобном ассистенте | Запускается как FastAPI/React приложение или MCP Server |
| Отношение | Верхний слой знаний и письменных паттернов | Нижний инженерный runtime и слой аудита доказательств |

Коротко: **PhD Thesis Butler Skill — это “мозг письма и планирования”, а RuScholar Studio — “визуальная панель аудита + исполнитель MCP-инструментов”.** Они не заменяют друг друга, а работают как upstream/downstream.

### Архитектура

PhD Thesis Butler / RuScholar Studio использует архитектуру "общий service layer + два входа". Web UI и MCP Server не дублируют логику, а обращаются к общим сервисам в `services/`; алгоритмы анализа находятся в `naturalization_layer/`.

```text
Web UI (FastAPI + React)
        |
        v
Shared Services
diagnostic_service / citation_audit_service / report_service / shared_state
        |
        v
Naturalization Layer
rules_engine / ppl_engine / llm_judge / nli_judge / rag_retriever / citation_integrity
        |
        v
Evidence Sources
Local GGUF Model / BibTeX / PDF / OpenAlex / DeepSeek-compatible API

MCP Server
        |
        +-- analyze_manuscript
        +-- audit_citations
        +-- retrieve_evidence
        +-- suggest_revision
        +-- export_report
        +-- model and reference management tools
```

Главная идея: Web UI удобен для ручной экспертизы, MCP удобен для AI-агентов, но оба режима используют одни и те же правила, кеш ссылок и формат отчета.

### Преимущества

- **Не черный ящик AI-score**: система показывает тип риска, метрики, объяснение, исходное предложение и проверяемые evidence snippets.
- **Фокус на русском академическом стиле**: правила учитывают номинализацию, цепочки родительного падежа, пассив, переводность и научные клише.
- **Локальная приватность**: поддерживаются локальная GGUF-модель, локальный PPL-зонд и локальный поиск по PDF/BibTeX.
- **Многоуровневая проверка**: правила, вероятностный сигнал, согласованность цитирования и NLI-аудит взаимно проверяют друг друга.
- **Готовность к AI-агентам**: MCP позволяет Claude Code, Codex, Cursor и другим клиентам регистрировать источники, искать доказательства, проверять цитаты и экспортировать отчеты.
- **WebUI и MCP одновременно**: человек видит подсветку и объяснения в браузере, агент может выполнять пакетный аудит.

### История версий

| Этап | Главное изменение | Что решает |
|------|-------------------|------------|
| v1.x базовые правила | Regex, spaCy POS, noun/verb ratio, связки и клише | Первичная диагностика русского академического стиля |
| v2.x LLM Judge | Локальный/облачный судья стиля и контекстное окно | Меньше ошибок от анализа только одного предложения |
| v3.x PPL слой | Локальный GGUF PPL и дисциплинарная калибровка | Вероятностная оценка предсказуемости и переводности |
| v4.x производительность | Early Exit, защита LaTeX/таблиц, SSE streaming | Снижение нагрузки и быстрый WebUI |
| v5.1.3 правила | Стабильный `polishing_rules_v5.json` | Закрепление правил PhD Thesis Butler skill |
| v5.2 research layer | Research planning, query strategy, eLIBRARY/DisserCat/CyberLeninka/OpenAlex source profiles | Переход от фраз и полировки к поддержке литературного исследования |
| v5.3.0 evidence-aware writing | Evidence roles, chapter evidence binding, citation gap detection | Skill начинает понимать, какие claims требуют источников |
| v5.4.1 engineering release | WebUI + MCP + shared services + local PPL/NLI + GitHub setup + single-page trilingual README | Полноценный инструмент, который можно clone/deploy/use with agents |

### Требования

| Параметр | Минимум | Рекомендуется |
|----------|---------|---------------|
| Python | 3.9+ | 3.10+ |
| Node.js | 18+ | 20+ |
| RAM | 8 GB для cloud-only режима | 16 GB для локальной модели |
| Диск | 500 MB для исходного кода и зависимостей | 4 GB с учетом 2.7 GB GGUF модели |
| ОС | macOS / Linux / Windows | macOS Apple Silicon + Metal |

Пользователи Apple Silicon могут использовать Metal-ускорение. Пользователи Linux и Windows могут избежать локальной компиляции модели, выбрав `cloud-pro` или `cloud-flash`.

### Быстрый старт

```bash
git clone https://github.com/Tanue-Hou/RuScholar-Studio.git
cd RuScholar-Studio
chmod +x setup.sh
./setup.sh
```

С загрузкой локальной модели:

```bash
DOWNLOAD_MODEL=1 ./setup.sh
```

Принудительная установка Metal на Apple Silicon:

```bash
INSTALL_LLAMA_METAL=1 ./setup.sh
```

Windows:

```powershell
.\setup.ps1
```

### Локальная модель

Для защиты приватности рукописей локальный PPL-зонд и локальный NLI/style judge могут использовать **Qwen3-4B-Q5_K_M GGUF**. Модель занимает около 2.7 GB и по умолчанию хранится здесь:

```text
models/Qwen3-4B-Q5_K_M.gguf
```

Ручная загрузка:

```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

Также можно вызвать MCP-инструмент `download_model_tool`. Без локальной модели режимы `local` и `hybrid` недоступны, но cloud-only режимы продолжают работать.

### Web UI

```bash
source .venv/bin/activate
python backend/main.py
```

Откройте `http://localhost:8000`.

Режим разработки:

```bash
# Терминал 1
python backend/main.py

# Терминал 2
cd frontend
npm run dev
```

Хост и порт можно изменить:

```bash
THESIS_BUTLER_HOST=127.0.0.1 THESIS_BUTLER_PORT=8010 python backend/main.py
```

### MCP-интеграция

Проект поддерживает **MCP (Model Context Protocol)**, поэтому Claude Code, Cursor, Claude Desktop, Codex и другие агенты могут напрямую вызывать локальные инструменты аудита.

```bash
python -m mcp_server.server
```

Пример для Claude Desktop:

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

Пример для Claude Code:

```bash
claude mcp add thesis-butler python -m mcp_server.server --cwd "/YOUR_CLONE_PATH/RuScholar-Studio"
```

Доступные MCP-инструменты:

| # | Инструмент | Назначение |
|---|------------|------------|
| 1 | `analyze_manuscript` | Диагностика академического стиля, переводности, noun stacking и PPL-риска |
| 2 | `audit_citations` | Проверка соответствия внутритекстовых ссылок и списка литературы |
| 3 | `retrieve_evidence` | Поиск evidence snippets в локальных источниках или OpenAlex |
| 4 | `suggest_revision` | Контекстные академические рекомендации по переписыванию |
| 5 | `export_report` | Экспорт Markdown или JSON отчета |
| 6 | `check_model_installed` | Проверка наличия и размера локальной модели |
| 7 | `download_model_tool` | Загрузка локальной GGUF модели |
| 8 | `register_references` | Регистрация BibTeX и/или локальных PDF |
| 9 | `clear_references` | Очистка библиотеки ссылок сессии |
| 10 | `list_references` | Просмотр библиотеки ссылок сессии |

### Диагностическая архитектура

Система использует многоуровневый процесс:

1. **Track A: правила и структура стиля**  
   Проверяет соотношение существительных и глаголов, пассивные конструкции, цепочки родительного падежа, чрезмерные связки, академические клише и переводность.

2. **Track B: вероятностный сигнал**  
   Вычисляет perplexity предложений через локальную GGUF-модель и использует ранний выход для снижения стоимости инференса.

3. **Track C: согласованность цитирования**  
   Проверяет разрывы между внутритекстовыми ссылками и списком литературы, поддерживает локальный BM25 и OpenAlex.

4. **Track D: LLM/NLI аудит доказательств**  
   Классифицирует связь claim-evidence как entailment, contradiction или not enough information.

Высокорисковые проблемы цитирования показываются в первую очередь. Стилевые и PPL-аномалии запускают контекстный анализ. Система сохраняет объяснения, метрики и исходные фрагменты для ручной проверки.

### Режимы

| Режим | Локальный PPL | LLM Judge | Сценарий |
|-------|---------------|-----------|----------|
| `local` | Да | Локальный Qwen | Полностью офлайн и приватно |
| `hybrid-pro` | Да | DeepSeek Pro | Локальный вероятностный зонд + глубокий облачный анализ |
| `hybrid-flash` | Да | DeepSeek Flash | Локальный вероятностный зонд + быстрый облачный анализ |
| `cloud-pro` | Нет | DeepSeek Pro | Cloud-only глубокая диагностика |
| `cloud-flash` | Нет | DeepSeek Flash | Cloud-only быстрая диагностика |

### Конфигурация

```bash
cp .env.example .env
```

Основные переменные:

- `DEEPSEEK_API_KEY`: ключ облачного judge-модуля.
- `DEEPSEEK_BASE_URL`: OpenAI-compatible endpoint DeepSeek.
- `THESIS_BUTLER_MODEL_PATH`: путь к локальной GGUF-модели.
- `THESIS_BUTLER_MODEL_URL`: URL загрузки модели.
- `THESIS_BUTLER_RULES_PATH`: путь к дисциплинарным правилам письма.
- `THESIS_BUTLER_GPU_LAYERS`: `-1` для GPU offload, `0` для CPU-only.

### Проверка

```bash
pytest -q
cd frontend && npm run build
```

Тесты покрывают rule engine, PPL engine, LLM judge, аудит цитирования, RAG/NLI, service layer и MCP stdio integration.

### Участие и лицензия

Issues и pull requests приветствуются. Проект распространяется по MIT License.

---

## English

Evidence-driven academic writing quality auditing for dissertations, manuscripts, and research papers. The project continues the original **PhD Thesis Butler** skill and packages it as **RuScholar Studio**: a local research-writing workbench with a Web UI and MCP tools for AI agents.

The system avoids the simplistic "AI detection score" framing. Instead, it uses a traceable architecture built from a **local rule engine, local PPL probing, local/online evidence retrieval, and LLM-as-NLI citation auditing**. Results should be treated as review signals and evidence trails, not automatic misconduct verdicts.

Version naming follows the source skill lineage: the local `phd-thesis-butler` skill is currently at `v5.3.0`; this repository adds Web UI, MCP, shared services, local PPL/NLI execution, GitHub setup scripts, and trilingual documentation on top of that layer, so the release is named `v5.4.1`.

### Relationship to PhD Thesis Butler Skill

The `PhD Thesis Butler` / `博士论文管家` skill is the source capability layer for this project. It provides dissertation-writing intelligence, Russian-first sentence templates, planning assets, research workflows, and evidence-aware writing rules. RuScholar Studio turns those capabilities into an executable Web UI and MCP-based audit platform.

| Layer | PhD Thesis Butler Skill | RuScholar Studio |
|-------|-------------------------|------------------|
| Role | AI-assistant skill for Russian dissertation writing | Cloneable, runnable, deployable audit workbench |
| Core assets | 16,722 Russian-first templates from 2,118 dissertations/abstracts across 5 discipline clusters | Diagnostic services, Web UI, MCP Server, local model bridge, report export |
| Main tasks | Dissertation planning, chapter blueprints, template retrieval, academic polishing, evidence-role binding | Style risk detection, PPL probing, citation integrity, RAG retrieval, NLI evidence audit |
| Runtime | Loaded as a skill inside Codex/Hermes/Claude-like assistants | Runs as a local FastAPI/React app or MCP Server |
| Relationship | Upstream knowledge and writing-pattern source | Downstream engineering runtime and evidence-audit layer |

In short: **PhD Thesis Butler Skill is the writing and planning brain; RuScholar Studio is the visual audit dashboard plus MCP tool executor.** They are complementary, not competing.

### Architecture

PhD Thesis Butler / RuScholar Studio uses a "shared service layer + dual entrypoint" architecture. The Web UI and MCP Server do not duplicate logic; both call the shared diagnostic, citation, report, and session services in `services/`, while the core algorithms live in `naturalization_layer/`.

```text
Web UI (FastAPI + React)
        |
        v
Shared Services
diagnostic_service / citation_audit_service / report_service / shared_state
        |
        v
Naturalization Layer
rules_engine / ppl_engine / llm_judge / nli_judge / rag_retriever / citation_integrity
        |
        v
Evidence Sources
Local GGUF Model / BibTeX / PDF / OpenAlex / DeepSeek-compatible API

MCP Server
        |
        +-- analyze_manuscript
        +-- audit_citations
        +-- retrieve_evidence
        +-- suggest_revision
        +-- export_report
        +-- model and reference management tools
```

The important design choice is that the browser workflow and the agent workflow share the same decision logic, reference cache, and report pipeline. Web UI is for human review; MCP is for agent collaboration.

### Strengths

- **No black-box AI score**: the system returns risk type, metrics, explanations, source sentence, and reviewable evidence instead of a single percentage.
- **Russian academic writing focus**: rules target nominalization, genitive chains, passive constructions, translationese, and academic cliches common in Russian dissertations.
- **Local-first privacy**: supports local GGUF inference, local PPL probing, and local PDF/BibTeX evidence retrieval.
- **Multi-track judgment**: rule signals, probabilistic signals, citation consistency, and NLI evidence auditing cross-check each other.
- **Agent-native workflow**: MCP tools let Claude Code, Codex, Cursor, and similar clients register references, retrieve evidence, audit citations, suggest revisions, and export reports.
- **WebUI and MCP coexist**: researchers can inspect highlights in the browser while agents run repeatable batch checks.

### Version Evolution

| Stage | Main Change | Problem Solved |
|-------|-------------|----------------|
| v1.x rule foundation | Regex, spaCy POS, noun/verb ratio, connectors, cliche scanning | First Russian academic style risk signals |
| v2.x LLM Judge | Local/cloud style judge with context windows | Less brittle than isolated sentence rules |
| v3.x PPL layer | Local GGUF perplexity and discipline calibration | Probabilistic signal for predictability and translation risk |
| v4.x performance layer | Early Exit, LaTeX/table protection, SSE streaming | Lower local inference cost and responsive Web UI |
| v5.1.3 rule assets | Stable `polishing_rules_v5.json` | Consolidates PhD Thesis Butler skill rules |
| v5.2 research layer | Research planning, query strategy, eLIBRARY/DisserCat/CyberLeninka/OpenAlex source profiles | Expands from polishing into literature research support |
| v5.3.0 evidence-aware writing | Evidence roles, chapter evidence binding, citation gap detection | Lets the skill reason about which claims require sources |
| v5.4.1 engineering release | WebUI + MCP + shared services + local PPL/NLI + GitHub setup + single-page trilingual README | Turns the skill into a cloneable, deployable, agent-callable audit tool |

### Requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| Python | 3.9+ | 3.10+ |
| Node.js | 18+ | 20+ |
| RAM | 8 GB for cloud-only mode | 16 GB for local model mode |
| Disk | 500 MB for source and dependencies | 4 GB including the 2.7 GB GGUF model |
| OS | macOS / Linux / Windows | macOS Apple Silicon with Metal |

Apple Silicon users can use Metal acceleration. Linux and Windows users can avoid local model compilation by using `cloud-pro` or `cloud-flash`.

### Quick Start

```bash
git clone https://github.com/Tanue-Hou/RuScholar-Studio.git
cd RuScholar-Studio
chmod +x setup.sh
./setup.sh
```

Download the local model during setup:

```bash
DOWNLOAD_MODEL=1 ./setup.sh
```

Force Metal-enabled installation on Apple Silicon:

```bash
INSTALL_LLAMA_METAL=1 ./setup.sh
```

Windows:

```powershell
.\setup.ps1
```

### Local Model

To protect manuscript privacy, the local PPL probe and local NLI/style judge can use **Qwen3-4B-Q5_K_M GGUF**. The model is around 2.7 GB and defaults to:

```text
models/Qwen3-4B-Q5_K_M.gguf
```

Manual download:

```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

You can also let an MCP client call `download_model_tool`. Without the local model, `local` and `hybrid` modes are unavailable, but cloud-only modes still work.

### Web UI

```bash
source .venv/bin/activate
python backend/main.py
```

Open `http://localhost:8000`.

Development mode:

```bash
# Terminal 1
python backend/main.py

# Terminal 2
cd frontend
npm run dev
```

Override host and port:

```bash
THESIS_BUTLER_HOST=127.0.0.1 THESIS_BUTLER_PORT=8010 python backend/main.py
```

### MCP Integration

The project supports **MCP (Model Context Protocol)** so Claude Code, Cursor, Claude Desktop, Codex, and other agents can call local audit tools directly.

```bash
python -m mcp_server.server
```

Claude Desktop example:

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

Claude Code example:

```bash
claude mcp add thesis-butler python -m mcp_server.server --cwd "/YOUR_CLONE_PATH/RuScholar-Studio"
```

Available MCP tools:

| # | Tool | Purpose |
|---|------|---------|
| 1 | `analyze_manuscript` | Diagnose academic style, translationese, noun stacking, and PPL risk |
| 2 | `audit_citations` | Cross-check in-text citations and bibliography entries |
| 3 | `retrieve_evidence` | Retrieve evidence snippets from local references or OpenAlex |
| 4 | `suggest_revision` | Generate context-aware academic revision suggestions |
| 5 | `export_report` | Export Markdown or JSON audit reports |
| 6 | `check_model_installed` | Verify local model presence and size |
| 7 | `download_model_tool` | Download the local GGUF model |
| 8 | `register_references` | Register BibTeX text and/or local PDF paths |
| 9 | `clear_references` | Clear a session reference library |
| 10 | `list_references` | List a session reference library |

### Diagnostic Architecture

The system uses a multi-track decision process:

1. **Track A: Rule and style structure**  
   Detects noun/verb ratio, passive constructions, genitive chains, connector overuse, academic cliches, and translationese.

2. **Track B: Probabilistic signal**  
   Computes sentence perplexity with a local GGUF model and uses early-exit heuristics to reduce inference cost.

3. **Track C: Citation consistency**  
   Checks bidirectional gaps between in-text citations and bibliography entries, with local BM25 retrieval and optional OpenAlex evidence lookup.

4. **Track D: LLM/NLI evidence audit**  
   Classifies claim-evidence relationships as entailed, contradicted, or not enough information.

High-risk citation issues are surfaced first. Style and PPL anomalies trigger context-aware judge analysis. The system keeps explanations, metrics, and source snippets available for human review.

### Modes

| Mode | Local PPL | LLM Judge | Use Case |
|------|-----------|-----------|----------|
| `local` | Yes | Local Qwen | Fully offline and privacy-preserving |
| `hybrid-pro` | Yes | DeepSeek Pro | Local probability probe plus cloud deep analysis |
| `hybrid-flash` | Yes | DeepSeek Flash | Local probability probe plus fast cloud analysis |
| `cloud-pro` | No | DeepSeek Pro | Cloud-only deep diagnostics |
| `cloud-flash` | No | DeepSeek Flash | Cloud-only fast diagnostics |

### Configuration

```bash
cp .env.example .env
```

Common variables:

- `DEEPSEEK_API_KEY`: optional cloud judge key.
- `DEEPSEEK_BASE_URL`: OpenAI-compatible DeepSeek endpoint.
- `THESIS_BUTLER_MODEL_PATH`: local GGUF model path.
- `THESIS_BUTLER_MODEL_URL`: model download URL.
- `THESIS_BUTLER_RULES_PATH`: discipline-specific writing rule path.
- `THESIS_BUTLER_GPU_LAYERS`: `-1` for GPU offload, `0` for CPU-only.

### Verification

```bash
pytest -q
cd frontend && npm run build
```

The test suite covers the rule engine, PPL engine, LLM judge, citation auditing, RAG/NLI, service layer, and MCP stdio integration.

### Contributing and License

Issues and pull requests are welcome. The project is released under the MIT License.
