#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"

cd "$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 9):
    raise SystemExit("Python 3.9 or newer is required.")
PY

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip

if [ "$(uname -s)" = "Darwin" ] && [ "${INSTALL_LLAMA_METAL:-0}" = "1" ]; then
  CMAKE_ARGS="-DGGML_METAL=on" FORCE_CMAKE=1 pip install --no-cache-dir --force-reinstall llama-cpp-python
fi

pip install -r requirements.txt
python -m spacy download ru_core_news_sm

if command -v npm >/dev/null 2>&1; then
  (cd frontend && npm install && npm run build)
else
  echo "npm was not found. Install Node.js 20+ and run: cd frontend && npm install && npm run build"
fi

if [ "${DOWNLOAD_MODEL:-0}" = "1" ]; then
  python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
fi

echo "Setup complete. Start Web UI with: source .venv/bin/activate && python backend/main.py"
