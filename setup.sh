#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-$HOME/.venvs/ruscholar}"

cd "$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or newer is required (the mcp package needs it).")
PY

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip

if [ "$(uname -s)" = "Darwin" ] && [ "${INSTALL_LLAMA_METAL:-0}" = "1" ]; then
  CMAKE_ARGS="-DGGML_METAL=on" FORCE_CMAKE=1 pip install --no-cache-dir --force-reinstall llama-cpp-python
fi

pip install -r requirements-dev.txt   # 含 requirements.txt 与测试依赖
pip install --no-deps -e .
python -m spacy download ru_core_news_sm

if command -v npm >/dev/null 2>&1; then
  FRONTEND_STAGE="$(mktemp -d "${TMPDIR:-/tmp}/ruscholar-frontend.XXXXXX")"
  trap 'rm -rf "$FRONTEND_STAGE"' EXIT
  python - "$ROOT_DIR/frontend" "$FRONTEND_STAGE/frontend" <<'PY'
from pathlib import Path
import shutil, sys
shutil.copytree(Path(sys.argv[1]), Path(sys.argv[2]),
                ignore=shutil.ignore_patterns('node_modules', 'dist', '.DS_Store'))
PY
  (cd "$FRONTEND_STAGE/frontend" && npm ci && npm run build)
  python - "$FRONTEND_STAGE/frontend/dist" "$ROOT_DIR/frontend/dist" <<'PY'
from pathlib import Path
import shutil, sys
target = Path(sys.argv[2])
if target.exists():
    shutil.rmtree(target)
shutil.copytree(Path(sys.argv[1]), target)
PY
else
  echo "npm was not found. Install Node.js 20+ and run: cd frontend && npm install && npm run build"
fi

if [ "${DOWNLOAD_MODEL:-0}" = "1" ]; then
  python -c "from naturalization_layer.model_downloader import download_model; from services.shared_state import MODEL_PATH; download_model(MODEL_PATH)"
fi

echo "Setup complete. Start Web UI with: \"$VENV_DIR/bin/ruscholar-web\""
echo "MCP server (stdio): \"$VENV_DIR/bin/ruscholar-mcp\""
