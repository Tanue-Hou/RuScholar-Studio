#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

MODEL_URL="https://modelscope.cn/models/Qwen/Qwen3-8B-GGUF/resolve/master/Qwen3-8B-Q5_K_M.gguf"
DEST_PATH="$PROJECT_ROOT/models/Qwen3-8B-Q5_K_M.gguf"
TMP_PATH="$DEST_PATH.tmp"
EXPECTED_SIZE=5851112224
OLD_4B_PATH="$PROJECT_ROOT/models/Qwen3-4B-Q5_K_M.gguf"

echo "=========================================================="
echo " [RuScholar Studio] Background 8B Model Upgrade Pipeline "
echo "=========================================================="
echo "Target Model: Qwen3-8B-Q5_K_M.gguf"
echo "Expected File Size: $EXPECTED_SIZE bytes (~5.45 GB)"
echo "Download URL: $MODEL_URL"
echo ""

echo ">>> [Stage 1/5] Downloading 8B model (resuming if partial)..."
while true; do
    CURRENT_SIZE=$(stat -f%z "$TMP_PATH" 2>/dev/null || stat -c%s "$TMP_PATH" 2>/dev/null || echo 0)
    if [ "$CURRENT_SIZE" -ge "$EXPECTED_SIZE" ]; then
        echo "Download reached expected target size: $CURRENT_SIZE bytes."
        break
    fi
    echo "Resuming download from $CURRENT_SIZE / $EXPECTED_SIZE bytes..."
    curl -L -C - --retry 999 --retry-delay 3 "$MODEL_URL" -o "$TMP_PATH" || true
    sleep 2
done

echo ""
echo ">>> [Stage 2/5] Validating downloaded file integrity..."
ACTUAL_SIZE=$(stat -f%z "$TMP_PATH" 2>/dev/null || stat -c%s "$TMP_PATH" 2>/dev/null)
echo "Downloaded size: $ACTUAL_SIZE bytes"

if [ "$ACTUAL_SIZE" -ne "$EXPECTED_SIZE" ]; then
    echo "❌ ERROR: File size mismatch! Expected $EXPECTED_SIZE bytes, but got $ACTUAL_SIZE bytes."
    exit 1
fi
echo "✅ File size validated successfully."

echo ""
echo ">>> [Stage 3/5] Activating Qwen3 8B model..."
mv "$TMP_PATH" "$DEST_PATH"
echo "✅ Moved to: $DEST_PATH"

echo ""
echo ">>> [Stage 4/5] Cleaning up legacy 4B model..."
if [ -f "$OLD_4B_PATH" ]; then
    rm -f "$OLD_4B_PATH"
    echo "✅ Removed legacy 4B model to reclaim 2.88 GB disk space."
fi
rm -f "$PROJECT_ROOT/models/qwen2.5-3b-instruct-q5_k_m.gguf"

echo ""
echo ">>> [Stage 5/5] Running verification test suite with 8B model..."
"$PROJECT_ROOT/.venv/bin/python" "$PROJECT_ROOT/scripts/verify_8b_model.py"

echo ""
echo "=========================================================="
echo " 🎉 8B Model Upgrade & Verification Completed! "
echo " Restarting RuScholar Studio Backend on Port 6666... "
echo "=========================================================="

export RUSCHOLAR_PORT=6666
exec "$PROJECT_ROOT/.venv/bin/python" "$PROJECT_ROOT/backend/main.py"
