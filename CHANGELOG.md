# Changelog

Entries are newest first. Each entry records **what** changed, **why**, and
**how it was verified**, so a later contributor (human or AI assistant) can pick
up the work without re-reading the whole diff.

---

## 2026-11-04 — Architecture review, phase 3: packaging, CI, MCP split, frontend redesign

Branch: `claude/sharp-einstein-dmbnvw` · Base commit: `7faad33` (phase 2)

### 1. Packaging and entry points
- `pyproject.toml` now has full `[project]` metadata, so `pip install -e .` works.
  - Dependencies are listed, and the package data includes the rules and calibration JSON.
  - Extras: `local` = llama-cpp-python (a native build, now optional); `dev` = pytest, httpx, pyflakes.
  - The version is read from `VERSION`.
- Console scripts: `ruscholar-web` (= `python -m backend.main`) and `ruscholar-mcp`
  (= `python -m mcp_server.server`). Both run from any directory.
- `backend/main.py` adds the project root to `sys.path` only when it is started as a
  script, so `python backend/main.py` keeps working. `setup.sh` / `setup.ps1` now run
  `pip install --no-deps -e .` and print the new commands; the README uses them.
- **Decision:** the existing top-level package names are kept (`backend`, `services`,
  `naturalization_layer`, `mcp_server`). Moving to `src/ruscholar/` would rename every
  import and break MCP client configs already in use (`python -m mcp_server.server`).
- Behaviour change: uvicorn auto-reload is now off by default. Turn it on with
  `RUSCHOLAR_RELOAD=1`.
- **Fix — fresh installs were failing:** `pymorphy3>=2.1` could never be satisfied (PyPI's
  newest release is 2.0.6), so `pip install -r requirements.txt` failed at that line. It is
  now `>=2.0`. Found by installing into a clean virtualenv.
- **Fix — Python minimum version:** the requirement is now **3.10**. `mcp` (all 1.x
  releases), fastapi and spacy all require ≥ 3.10, so the old "3.9+" claim was never true.
  Updated in `pyproject.toml`, both setup scripts and the README. `source_similarity.py`
  got `from __future__ import annotations` anyway.

### 2. CI (`.github/workflows/ci.yml`)
- **Python 3.10 and 3.12:** `pip install -e ".[dev]"`, download the spaCy model, run
  `pytest`, check that the entry points import. llama-cpp-python is not installed; the
  real-model test skips itself.
- **Frontend (Node 22):** `npm ci`, `npm run lint`, `npm run build`.
- The Python job was reproduced locally in a clean 3.12 virtualenv (all tests passed). The
  workflow itself has not run on GitHub yet.

### 3. Backend hardening
- Upload size limit: `RUSCHOLAR_MAX_UPLOAD_MB` (default 50) applies to `/api/upload` and
  `/api/upload_references`. Larger files get HTTP 413.
- Removed the four placeholder routes that only returned 501 (`/api/polish`,
  `/api/references`, `/api/format`, `/api/structure`). The frontend buttons that pointed at
  them did nothing and are gone too.
- `NLICitationJudge`: local mode without a model now returns `AUDIT_FAILED` with a clear
  "local model not installed" explanation. Before, it called `None` and logged an error.
- New tests are in `tests/test_backend_security.py`.

### 4. MCP server split
`mcp_server/server.py` (~1060 lines) became:
- `app.py`: the FastMCP instance, `get_engines()` and the argument enums;
- `core.py`: the plain functions behind the tools;
- `tools/{workflow,manuscript,citations,model,references}.py`: the 17 tool definitions,
  moved without changes;
- `server.py`: a 42-line entry point that registers the tools and re-exports every
  previously public name.

Tests that patched `mcp_server.server.get_engines` now patch `mcp_server.app.get_engines`;
the tools call it through the module, so one patch covers all of them.
**Verified:** names, descriptions and input schemas of all 17 tools are identical to the
previous version (`list_tools()` compared against `git show HEAD:mcp_server/server.py`).
A real stdio handshake via `ruscholar-mcp` lists 17 tools.

### 5. Frontend: split and redesign ("学术典藏")
The user chose the editorial direction: warm paper canvas, serif manuscript text, ink
black, and one wine-red accent. Issues appear as numbered margin notes instead of
coloured highlighting.

- **Structure:** `App.tsx` went from 1361 lines to 222 lines of composition; the rest
  moved into:
  - `api/client.ts`: a typed client, including the POST download stream parser;
  - `types.ts`;
  - `hooks/useDiagnosis.ts`: the analysis lifecycle as a reducer, replacing about 20
    `useState` calls;
  - `hooks/useModelStatus.ts` and `hooks/useTheme.ts`;
  - `lib/labels.ts`: all label/category tables in one place;
  - `components/`: `TopBar`, `SettingsSheet`, `ImportView`, `ManuscriptPage`, `Summary`,
    `NoteList`, `Inspector`.
- **Design system** (`index.css`): colour tokens for light (paper) and dark (ink) themes;
  the Minor Third type scale; weights 400/500/600 only; hairline borders before shadows;
  motion only on transform/opacity; `prefers-reduced-motion` respected. The theme follows
  the system setting, can be toggled and is remembered; an inline script sets it before
  first paint.
- **Fonts:** Source Serif 4 (with Cyrillic) and Inter are bundled through `@fontsource`.
  The old `index.html` loaded Google Fonts, which contacted Google on every launch of this
  "offline" tool.
- **UX changes:**
  - Engine settings moved from a crowded header into a slide-over. It traps focus, closes
    on Esc and returns focus to the button that opened it.
  - Starting in local mode without a model opens that sheet instead of an `alert()`.
  - The drop zone now accepts drag-and-drop (the old one said "拖拽" but only supported
    clicking).
  - Replacing the manuscript after an analysis asks for confirmation and names the file and
    the number of results that will be lost.
  - Perplexity values are hidden by default behind a toggle.
  - Touch targets are 44 px on coarse pointers.
  - The engine value `deepseek-flash` became `cloud-flash`, consistent with MCP; the backend
    accepts both.
- The pre-existing ESLint error in `App.tsx` is gone; `npm run lint` is clean.
- `docs/assets/webui-diagnostics.png` now shows the new UI, rendered from **sample data**.
  The README captions in all three languages were updated and say so.
- **Verified (Playwright, real backend serving the built UI, `/api/*` answered by a
  fixture):** light and dark at 1440 px, 1280 px, and 375/390 px with touch:
  - no console errors and no horizontal overflow;
  - computed manuscript size 19.2 px and list text 14 px;
  - no button under 44 px on touch;
  - Esc closes the sheet and focus returns to its trigger;
  - cancelling the replace-manuscript confirmation keeps the results.
- **Not verified:** a real analysis end to end in the browser (no GGUF model or DeepSeek key
  in the container), Safari/Firefox, and screen readers.

### Remaining ideas (not started)
- Phase 4 from the roadmap below: a separate PPL scoring context, persistent sessions
  (SQLite), an evaluation set and threshold calibration.
- Frontend: optionally merge detect/session/upload into one `POST /api/analyses` call;
  add component tests (Vitest + Testing Library).

---

## 2026-11-04 — Architecture review, phase 2: service-layer consolidation

Branch: `claude/sharp-einstein-dmbnvw` · Base commit: `0c10cf5` (phase 1)

Goal: the Web adapter (`backend/main.py`) and the MCP adapter
(`mcp_server/server.py`) should only translate requests. Engine loading,
reference storage and the diagnostic pipeline each now have exactly one
implementation under `services/` or `naturalization_layer/`.

### New modules — where things live now
| Module | Responsibility | Replaces |
|---|---|---|
| `services/settings.py` | Every env var in one frozen `Settings`; loads `.env` from the project root (real env vars win; `RUSCHOLAR_SKIP_DOTENV=1` disables). | Scattered `os.getenv`; `.env` was never loaded. |
| `services/rules_config.py` | Lazily cached polishing-rule clusters and calibration; `get_discipline_rules()`, `get_calibration()`. | Duplicate loaders + `get_discipline_rules` in `main.py` and `diagnostic_service.py`. |
| `services/model_registry.py` | `registry`: lazy, thread-safe GGUF load, cached `StyleJudge`/`NLICitationJudge`, `model_lock`, `reset()` after download; a failed load is remembered (not retried per request). | Three lazy-loading blocks (main diagnose, main detect_discipline, MCP `get_engines`). |
| `services/session_store.py` | `ExpiringDict`: dict-compatible store with idle TTL. | Plain dicts that grew forever. |
| `services/reference_service.py` | Reference sessions: `ensure_reference_session`, `ingest_bibtex`, `ingest_reference_document`, `reset_reference_session`, `list_reference_keys`. | `upload_references` (Web) and `register/clear/list_references` (MCP), plus 4 copies of the session dict literal. |
| `naturalization_layer/llm_client.py` | `call_openai_compatible`, `clean_json_text`, `build_qwen_prompt`, `complete_local`, `resolve_cloud_model`, `cloud_model_for`. | Copies of `_call_deepseek_api` / `_clean_json_text` / engine-name mapping in both judges and the pipeline. |
| `naturalization_layer/discipline.py` | `DISCIPLINES`, `detect_discipline_by_keywords`. | Three keyword fallback tables (two in `main.py`, one in `llm_judge.py`), all slightly different. |
| `naturalization_layer/document_parser.py` | Added `parse_document_bytes` (PDF/DOCX/UTF-8). | `parse_docx` / `parse_pdf_bytes` in `main.py`, inline PDF parsing in MCP. |

`services/shared_state.py` still exports `session_references`, `model_lock` and
`MODEL_PATH` (now `session_references` is an `ExpiringDict`), plus the new
`pending_analyses` (was `active_sessions` in `main.py`).

### Merged code paths
- **Diagnostic pipeline** (`services/diagnostic_service.py`, 554 → 390 lines):
  `process_sentence_local` and `process_sentence_cloud` (about 180 near-identical lines
  each), plus their duplicated aggregation loops, are now one `process_sentence`. Mode
  differences are explicit branches: local = PPL early exit and suspicion gating under
  `model_lock`; hybrid = local PPL with no early exit, then the cloud judge; cloud =
  judge only. The shared steps are small helpers (`_apply_judgement`, which includes the
  low-PPL veto, `_apply_citation_audits`, `_RunningRisks`, and so on).
- **Reference lookup** (`services/citation_audit_service.resolve_reference`): local
  BM25 → online cache → OpenAlex. This was written out three times
  (`perform_nli_citation_audit`, `bind_evidence`, MCP `retrieve_evidence`).
- **Judges** (`llm_judge.py`, `nli_judge.py`): prompts are unchanged and built with
  `build_qwen_prompt`. `_call_deepseek_api` / `_clean_json_text` remain as one-line
  delegate methods because tests patch them per instance.
- Adapters shrank: `backend/main.py` 468 → 267 lines; the helper section of
  `mcp_server/server.py` shrank by about half (the file is 1195 → ~1060 lines; the rest
  is the 17 decorated tool wrappers and their docstrings).

### Behaviour changes (intentional, small)
1. `.env` is now actually loaded. `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` act as
   fallbacks when a cloud/hybrid request has an empty key. Discipline auto-detection
   still only goes to the cloud when the request itself carries a key.
2. Sessions expire after `RUSCHOLAR_SESSION_TTL` seconds of inactivity (default 7200).
   This covers both pending analyses and uploaded references.
3. A model that fails to load is not reloaded on every request. `registry.reset()`
   (called automatically after a model download) allows a retry.
4. MCP `get_engines("local")` with a model file that fails to load now raises
   `ValueError("... failed to load: <reason>")` instead of the raw loader exception.
5. MCP `register_references` now also accepts `.docx`, via the shared parser.
6. `/api/detect_discipline`'s keyword fallback now uses the full shared table (it
   includes `ARTS_SPORTS`). The old copy in `main.py` was shorter.
7. `/api/upload` returns 400 instead of 500 when a file cannot be read.
8. MCP `thesis_judge_claim_evidence_nli` now holds `model_lock` for local inference.
   It was the only local llama.cpp call without the lock.
9. MCP `retrieve_evidence` now caches failed OpenAlex lookups, like the Web path does.
10. `NLICitationJudge` JSON cleaning now also handles output that has `</think>` but no
    opening tag. It gets this from the shared `clean_json_text`.
11. The MCP citation judge is no longer stuck permanently as a model-less judge when
    the model appears after the first call.

New env vars are documented in `.env.example` and in the README tables:
`RUSCHOLAR_SESSION_TTL`, `RUSCHOLAR_CORS_ORIGINS`, `RUSCHOLAR_CALIBRATION_PATH`,
`RUSCHOLAR_CLOUD_TIMEOUT`.

### Verification
- **Golden snapshot:** before refactoring, the output of `run_sentence_diagnose_stream`
  was recorded with deterministic mock engine/judge/NLI/OpenAlex. It covers 6 runs
  (local, hybrid-pro, cloud-flash × model present/absent), 114 events, and includes the
  early-exit, rule-pass, low-PPL-veto, citation-gap and citation-audit paths. After the
  refactor the JSON is **byte-identical**. The script lived in the session scratchpad and
  is not committed; `tests/test_service_layer.py` covers the same mode branches.
- `pytest` → **80 passed, 1 skipped** (the skip is the real-GGUF test). New:
  `tests/test_service_layer.py` (18 tests: settings/.env, TTL store, LLM client and
  env-key fallback, keyword classifier, registry load and caching, MCP load-failure
  message, reference ingestion, `resolve_reference` order and failure cache, and the
  local/hybrid/cloud pipeline branches).
- `tests/test_llm_judge.py` now imports `llama_cpp` only inside the real-model test, so
  its mock tests run without llama-cpp-python installed.
- End-to-end with FastAPI TestClient and no model: check_model → detect_discipline →
  upload → session → upload_references → diagnose SSE (`init`/`result`/`done`, local
  citation audit present) → replaying the same session returns "Session expired".
- **Not verified:** a run with a real GGUF model, real DeepSeek calls, or a browser.

### Follow-ups found during this phase (not done)
- Local mode without a model still attempts NLI with `NLICitationJudge(None)`, which logs
  `'NoneType' object is not callable` and yields `AUDIT_FAILED`. This is old behaviour.
  The pipeline should skip NLI (or report "model unavailable") when no LLM is present.
- `mcp_server/server.py` is still about 1060 lines of tool wrappers. Next step: split them
  into `mcp_server/tools/*.py` by area (workflow, manuscript, citations, references, model).
- Remaining phase 3/4 items from the roadmap below are unchanged.

---

## 2026-11-04 — Architecture review, phase 1 fixes (correctness / performance / security / repo hygiene)

Branch: `claude/sharp-einstein-dmbnvw` · Base commit: `078365e`

This is phase 1 of an architecture review. Phases 2–4 are listed under
"Follow-up roadmap" below and have **not** been started.

### 1. Dependency: MCP server failed to start on a fresh install
- **Problem:** `requirements.txt` had `mcp>=1.0.0`. pip now resolves mcp 2.x, which
  removed `mcp.server.fastmcp` → `ModuleNotFoundError` when importing `mcp_server/server.py`.
- **Fix:** `mcp>=1.0.0,<2`. Migrating to mcp 2.x (`MCPServer`) is a separate task.
- Also removed `streamlit` (only used by the deleted legacy UI) and added `numpy`
  explicitly (now imported directly by `ppl_engine.py`).

### 2. Performance: PPL computed with a pure-Python softmax
- **Problem:** `naturalization_layer/ppl_engine.py` looped in Python over the full
  vocabulary (~150k for Qwen3) for every token → hundreds of thousands of `math.exp`
  calls per sentence.
- **Fix:** new vectorised `sequence_nll(scores, tokens, n_tokens)` (numpy log-sum-exp).
  Behaviour is unchanged (same early-exit logic, same return values).
- Tests: `tests/test_ppl_engine.py` now feeds real numpy arrays instead of a
  `MagicMock` with `__getitem__`; added `test_sequence_nll_matches_reference_loop`,
  which checks the numpy result against the old loop formula.
- **Not done yet:** the engine still uses `logits_all=True, n_ctx=3072` on the same
  `Llama` instance that also generates text (~1.8 GB logits buffer). See roadmap.

### 3. Correctness: spaCy reloaded every call and fell back silently
- **Problem:** `analyze_text_rules` called `spacy.load("ru_core_news_sm")` on every
  call. If the model was missing it silently used a mock tokenizer (capitalised
  word = noun, others = verb), so the noun/verb ratio, passive voice and genitive-chain
  metrics were wrong while looking normal in the UI.
- **Fix (`naturalization_layer/rules_engine.py`):**
  - `get_nlp()`: loads the model once per process (`functools.lru_cache`) and logs a
    warning with the install command if it is missing.
  - `analyze_text_rules()` result has a new key `nlp_backend`: `"spacy"` or `"fallback"`.
  - `services/diagnostic_service.py`: the SSE `init` event now includes `nlp_backend`.
  - `frontend/src/App.tsx`: shows a warning card when `nlp_backend === "fallback"`.
- New tests in `tests/test_rules_engine.py`: fallback is reported; model is cached.
- Note: the earlier failures of `test_analyze_text_rules_advanced` and
  `test_mcp_e2e_references_flow` were both caused by the missing spaCy model. They
  pass once `python -m spacy download ru_core_news_sm` has been run (as `setup.sh` does).

### 4. Security: API exposed on the network, CSRF-able download
- `backend/main.py`:
  - Default `RUSCHOLAR_HOST` changed from `0.0.0.0` to `127.0.0.1`. The API has no
    auth, and the product promises that unpublished manuscripts stay local.
  - CORS: was `allow_origins=["*"]` with credentials. It now allows only the Vite dev
    origins (`localhost:5173`, `127.0.0.1:5173`) without credentials. Override with
    `RUSCHOLAR_CORS_ORIGINS` (comma-separated). The built UI is same-origin and needs no CORS.
  - `/api/download_model` changed from **GET → POST**. A GET with a 2.7 GB side effect
    could be triggered by any web page.
- `frontend/src/App.tsx`: `downloadLocalModel` now uses `fetch(POST)` and parses the
  SSE stream manually, because `EventSource` can only send GET.
- New `tests/test_backend_security.py` (POST-only download, non-wildcard CORS).
- Docs: README (zh/ru/en env tables) and `.env.example` updated to `127.0.0.1`.
- Port alignment: `.env.example` said 6666 and the Vite proxy pointed at 6666, while
  `backend/main.py` and the README default to 8000. Both now use 8000; the Vite proxy
  reads `RUSCHOLAR_PORT`. Note that `.env` is still **not loaded** by any code
  (no python-dotenv); see roadmap.

### 5. Repository hygiene (files removed from the working tree)
| Removed | Reason |
|---|---|
| `docs/superpowers/plans/纵横垂协同控制论文引言_草稿.md`, `…_俄文草稿.md` | Unpublished thesis drafts; conflicts with the privacy-first positioning. **They are still in git history** — rewriting history (e.g. `git filter-repo`) is the owner's decision and was not done. |
| `phd-thesis-butler-landing/` | Old-brand landing page, ~2.5 MB of PNGs, not linked from anywhere. |
| `scripts/web_app.py` | Legacy 709-line Streamlit UI, replaced by FastAPI + React. |
| `scratch/` (incl. the `scratch/impeccable` gitlink) | Already listed in `.gitignore` but had been committed. |
| `test_input.txt`, `backend/test_judge.py` | Stray manual test files outside `tests/`. |
| `frontend/src/assets/{react.svg,vite.svg,hero.png}` | Unused Vite scaffold assets. |

To restore any of them: `git show 078365e:<path> > <path>`.

### Verification (in a cloud container, Python 3.13)
- `pytest --ignore=tests/test_llm_judge.py` → **60 passed** (llama-cpp-python is not
  installed in that container; `test_llm_judge.py` imports it at module level).
- `cd frontend && npm ci && npm run build` → OK.
- `eslint src/App.tsx` → 1 error at line 73 (`no-explicit-any`). It predates this
  change and was not touched.
- `POST /api/download_model` via TestClient with a mocked downloader: emits
  `data: {...}\r\n\r\n` frames, which the new frontend parser handles. `GET` no
  longer triggers a download.
- **Not verified:** a real GGUF model run (no model in the container), and clicking
  through the UI in a browser.

### Follow-up roadmap (not started)
- ~~**Phase 2 — service consolidation:**~~ **Done — see the phase 2 entry above.** extract `ModelRegistry` (lazy load + lock,
  currently duplicated 3× across `backend/main.py` and `mcp_server/server.py`), an
  `LLMClient` interface (local llama / OpenAI-compatible; dedupe `_call_deepseek_api`
  and `_clean_json_text` in `llm_judge.py` / `nli_judge.py`; merge
  `process_sentence_local` / `process_sentence_cloud`), a `SessionStore` with TTL
  (`session_references` is never cleaned up → memory growth), and `Settings` via
  pydantic-settings (actually load `.env`). Also dedupe rules/calibration loading and
  `get_discipline_rules` (in both `main.py` and `diagnostic_service.py`), and the
  reference-ingestion code (`upload_references` vs MCP `register_references`).
- ~~**Phase 3:**~~ **Done — see the phase 3 entry above.** proper package layout plus console entry points (drop the `sys.path`
  hacks); GitHub Actions CI (pytest, `npm run build`, lint); use
  `pytest.importorskip("llama_cpp")` in llama-dependent tests; split `App.tsx` into
  `api/`, `hooks/`, `components/`; upload size limits; remove the 501 placeholder routes.
- **Phase 4:** separate the PPL-scoring context from the generation context (drop
  `logits_all` for generation); persist sessions (SQLite); build an evaluation set and
  calibrate the thresholds in `calibration/calibration_config.json`.
