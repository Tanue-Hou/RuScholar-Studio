#!/usr/bin/env bash
set -euo pipefail

export INSTALL_LLAMA_METAL="${INSTALL_LLAMA_METAL:-1}"
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/setup.sh"
