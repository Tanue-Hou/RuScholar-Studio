# PhD Thesis Butler / RuScholar Studio

**Версия: v5.2.0-alpha**  
**Языки:** [English](README.md) | [中文](README_ZH.md) | **Русский**

Система доказательного аудита академического письма для диссертаций, рукописей и научных статей. Проект продолжает исходный навык **PhD Thesis Butler** и оформляет его как **RuScholar Studio**: локальную рабочую среду исследователя с Web UI и MCP-инструментами для AI-агентов.

Система не сводит анализ к простому "проценту AI-текста". Вместо этого используется трассируемая архитектура: **локальный rule engine, локальный PPL-зонд, локальный/онлайн поиск источников и LLM-as-NLI аудит цитирования**. Результаты следует рассматривать как сигналы риска и доказательную цепочку, а не как автоматический вердикт о нарушении.

Именование версии следует исходной линии правил: `polishing_rules_v5.json` сейчас имеет версию правил `5.1.3`; этот репозиторий добавляет Web UI, MCP, общий service layer, GitHub setup scripts и трехъязычную документацию, поэтому релиз назван `v5.2.0-alpha`.

![Web UI diagnostics](docs/assets/webui-diagnostics.png)

На скриншоте показан гибридный режим: слева находится русский текст рукописи с подсветкой предложений, справа — дисциплина, средняя PPL, риски стиля, предсказуемости, переводности, избыточности и объяснение по выбранному предложению. Желтая и красная подсветка означает сигнал для проверки, а не окончательный вывод.

## Требования

| Параметр | Минимум | Рекомендуется |
|----------|---------|---------------|
| Python | 3.9+ | 3.10+ |
| Node.js | 18+ | 20+ |
| RAM | 8 GB для cloud-only режима | 16 GB для локальной модели |
| Диск | 500 MB для исходного кода и зависимостей | 4 GB с учетом 2.7 GB GGUF модели |
| ОС | macOS / Linux / Windows | macOS Apple Silicon + Metal |

Пользователи Apple Silicon могут использовать Metal-ускорение. Пользователи Linux и Windows могут избежать локальной компиляции модели, выбрав `cloud-pro` или `cloud-flash`.

## Быстрый старт

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

## Локальная модель

Для защиты приватности рукописей локальный PPL-зонд и локальный NLI/style judge могут использовать **Qwen3-4B-Q5_K_M GGUF**. Модель занимает около 2.7 GB и по умолчанию хранится здесь:

```text
models/Qwen3-4B-Q5_K_M.gguf
```

Ручная загрузка:

```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

Также можно вызвать MCP-инструмент `download_model_tool`. Без локальной модели режимы `local` и `hybrid` недоступны, но cloud-only режимы продолжают работать.

## Web UI

Запуск собранного frontend через backend:

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

## MCP-интеграция

Проект поддерживает **MCP (Model Context Protocol)**, поэтому Claude Code, Cursor, Claude Desktop, Codex и другие агенты могут напрямую вызывать локальные инструменты аудита.

Запуск MCP server:

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

## Диагностическая архитектура

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

## Режимы

| Режим | Локальный PPL | LLM Judge | Сценарий |
|-------|---------------|-----------|----------|
| `local` | Да | Локальный Qwen | Полностью офлайн и приватно |
| `hybrid-pro` | Да | DeepSeek Pro | Локальный вероятностный зонд + глубокий облачный анализ |
| `hybrid-flash` | Да | DeepSeek Flash | Локальный вероятностный зонд + быстрый облачный анализ |
| `cloud-pro` | Нет | DeepSeek Pro | Cloud-only глубокая диагностика |
| `cloud-flash` | Нет | DeepSeek Flash | Cloud-only быстрая диагностика |

## Конфигурация

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

## Проверка

```bash
pytest -q
cd frontend && npm run build
```

Тесты покрывают rule engine, PPL engine, LLM judge, аудит цитирования, RAG/NLI, service layer и MCP stdio integration.

## Участие и лицензия

Issues и pull requests приветствуются. Проект распространяется по MIT License.
