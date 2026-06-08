# RuScholar Studio 🎓

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Node Version](https://img.shields.io/badge/node-18%2B-green)](https://nodejs.org/)

**RuScholar Studio** (ранее *PhD Thesis Butler*) — это профессиональная локальная рабочая среда исследователя для аудита качества научного текста и академической адаптации российских диссертаций, авторефератов, рукописей и научных статей. Система поддерживает гибридный диагностический рабочий процесс локально или в облаке.

---

### Language / Язык / 语言

[English](README.md) · [Русский](README_RU.md) · [简体中文](README_ZH.md)

---

## 📸 Интерфейс Web UI

Ниже показана визуальная панель управления гибридного аудита в действии:

![Web UI Diagnostics](docs/assets/webui-diagnostics.png)

> [!NOTE]
> Web UI подсвечивает стилистические аномалии и проблемы с источниками в реальном времени. Предложения кодируются цветом (желтый для предупреждения, красный для высокого риска) на основе нарушения правил диссертационного письма, физического показателя перплексивности (PPL) и проверки цитирования через NLI. Данные отчеты служат **помощником для рецензирования**, а не автоматическим вердиктом о плагиате или использовании ИИ.

---

## 🌟 Ключевые преимущества

*   **Без черных ящиков с "AI-процентом"**: Система уходит от упрощенной оценки «процента ИИ». Вместо этого она предоставляет понятные стилистические метрики, лингвистическую статистику и проверяемые цитаты из источников.
*   **Специфические правила для русского научного стиля**: Правила адаптированы под русский академический язык (анализ номинализации, злоупотребления пассивным залогом, нагромождения цепочек родительного падежа, отсутствия смысловых глаголов в длинных предложениях).
*   **Конфиденциальность рукописей**: Локальный запуск GGUF-модели (`Qwen3-4B`), офлайн-оценка физической перплексивности (PPL) и локальный поиск по базам PDF/BibTeX гарантируют сохранность ваших данных на вашем ПК.
*   **Аудит цитирования через NLI-судью**: Автоматически сопоставляет утверждения в тексте статьи с абстрактами источников, классифицируя логическую связь как *Entailment (Подтверждается)*, *Contradiction (Противоречит)* или *Neutral (Недостаточно данных)*.
*   **Поддержка протокола FastMCP**: Встроенный stdio JSON-RPC демон позволяет AI-агентам (таким как Claude Code, Cursor, Claude Desktop) напрямую работать с вашей локальной библиотекой и аудировать рукопись.
*   **Гибридная архитектура**: Поддерживается полностью локальный режим, гибридный режим (локальный расчет PPL + облачный анализ через DeepSeek) и чисто облачный режим.

---

## 🧠 Связь с навыком PhD Thesis Butler

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
| **Запуск** | Загружается как skill в Codex/Hermes/Claude | Запускается локально как FastAPI/React приложение |
| **Связь** | Источник академических знаний и лингвистических правил | Инженерная реализация и слой верификации доказательств |

---

## 🛠️ Системные требования

| Ресурс | Минимум | Рекомендуется |
| :--- | :--- | :--- |
| **Python** | 3.9+ | 3.10+ |
| **Node.js** | 18+ | 20+ |
| **RAM** | 8 GB (для cloud-only режима) | 16 GB+ (для локального инференса) |
| **Диск** | 500 MB (код и зависимости) | 4 GB (с учетом 2.7 GB GGUF-модели) |
| **ОС** | macOS / Windows / Linux | macOS Apple Silicon (с ускорением Metal) |

---

## 🚀 Быстрый старт

### 1. Установка

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

### 2. Локальная модель

Для использования режимов `local` или `hybrid` офлайн требуется локальная модель **Qwen3-4B-Q5_K_M GGUF** (около 2.7 GB). По умолчанию она должна находиться по пути:
```
models/Qwen3-4B-Q5_K_M.gguf
```

Загрузка через CLI:
```bash
python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
```

---

## 💻 Запуск Web UI

Запуск единого backend-сервера (FastAPI автоматически раздает сборку React):

```bash
source .venv/bin/activate
python backend/main.py
```
Откройте в браузере **`http://localhost:8000`**.

### Режим разработки (Hot Reload)
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

## 🔌 Интеграция с MCP

Чтобы AI-агенты (Claude Desktop, Claude Code, Cursor) могли напрямую проверять ссылки и делать аудит рукописей:

### 1. Claude Desktop
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

### 2. Claude Code
Запустите команду:
```bash
claude mcp add ruscholar-studio python -m mcp_server.server --cwd "<YOUR_CLONE_PATH>/RuScholar-Studio"
```

### Доступные инструменты MCP:
1.  `analyze_manuscript`: Стилистический аудит, анализ переводности и расчет PPL-риска.
2.  `audit_citations`: Проверка согласованности внутритекстовых ссылок и списка литературы.
3.  `retrieve_evidence`: Поиск цитат в локальных PDF/BibTeX или OpenAlex.
4.  `suggest_revision`: Рекомендации по переписыванию на основе правил диссертаций.
5.  `export_report`: Экспорт аудиторского отчета в Markdown/JSON.
6.  `check_model_installed`: Проверка наличия и целостности локальной модели.
7.  `download_model_tool`: Загрузка локальной модели Qwen GGUF.
8.  `register_references`: Регистрация BibTeX или локальных путей к PDF.
9.  `clear_references`: Очистка кэша источников сессии.
10. `list_references`: Список зарегистрированных источников сессии.

---

## ⚙️ Переменные окружения

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

## 🧪 Тестирование

Запуск тестов:

```bash
pytest -v
```

---

## 📝 GitHub Релиз & Инструкция по упаковке

Перед отправкой изменений в Git:
*   **Исключенные файлы**: GGUF-модели (`models/*.gguf`), node_modules (`frontend/node_modules/`), сборка фронтенда (`frontend/dist/`), кэш тестов (`.pytest_cache/`, `scratch/`) и venv (`.venv/`) корректно прописаны в `.gitignore` и не попадут в репозиторий.
*   **Файлы импорта**: Убедитесь, что все файлы `__init__.py` в папках `services/`, `mcp_server/`, `backend/` и `tests/` отслеживаются Git, чтобы избежать ошибок `ModuleNotFoundError` у конечных пользователей.

---

## 🤝 Лицензия

Проект распространяется под свободной лицензией **MIT License**.
