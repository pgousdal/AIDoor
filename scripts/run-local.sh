#!/usr/bin/env bash
set -euo pipefail

# Run AIDoor in local test mode
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

if command -v uv &>/dev/null; then
    exec uv run aidoor --local "$@"
elif [ -f "$PROJECT_DIR/.venv/bin/aidoor" ]; then
    exec "$PROJECT_DIR/.venv/bin/aidoor" --local "$@"
elif [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    exec "$PROJECT_DIR/.venv/bin/python" -m aidoor --local "$@"
else
    echo "Cannot find uv or virtual environment."
    echo "Run './scripts/install.sh' first or install with uv."
    exit 1
fi
