# Changelog

Entries are newest first. Each entry records **what** changed, **why**, and
**how it was verified**, so a later contributor (human or AI assistant) can pick
up the work without re-reading the whole diff.

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
- **Phase 2 — service consolidation:** extract `ModelRegistry` (lazy load + lock,
  currently duplicated 3× across `backend/main.py` and `mcp_server/server.py`), an
  `LLMClient` interface (local llama / OpenAI-compatible; dedupe `_call_deepseek_api`
  and `_clean_json_text` in `llm_judge.py` / `nli_judge.py`; merge
  `process_sentence_local` / `process_sentence_cloud`), a `SessionStore` with TTL
  (`session_references` is never cleaned up → memory growth), and `Settings` via
  pydantic-settings (actually load `.env`). Also dedupe rules/calibration loading and
  `get_discipline_rules` (in both `main.py` and `diagnostic_service.py`), and the
  reference-ingestion code (`upload_references` vs MCP `register_references`).
- **Phase 3:** proper package layout plus console entry points (drop the `sys.path`
  hacks); GitHub Actions CI (pytest, `npm run build`, lint); use
  `pytest.importorskip("llama_cpp")` in llama-dependent tests; split `App.tsx` into
  `api/`, `hooks/`, `components/`; upload size limits; remove the 501 placeholder routes.
- **Phase 4:** separate the PPL-scoring context from the generation context (drop
  `logits_all` for generation); persist sessions (SQLite); build an evaluation set and
  calibrate the thresholds in `calibration/calibration_config.json`.
