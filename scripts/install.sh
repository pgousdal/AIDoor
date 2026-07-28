#!/usr/bin/env bash
set -euo pipefail

# AIDoor install script
# This script creates a Python virtual environment and installs AIDoor.
# It does NOT modify Mystic BBS configuration.

INSTALL_DIR="${1:-}"
if [ -z "$INSTALL_DIR" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    INSTALL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

if [ ! -f "$INSTALL_DIR/pyproject.toml" ]; then
    echo "Error: Cannot find pyproject.toml in $INSTALL_DIR"
    echo "Usage: $0 [path-to-aidoor-directory]"
    exit 1
fi

echo "AIDoor installer"
echo "================"
echo ""
echo "Target directory: $INSTALL_DIR"
echo ""

# Check for Python 3.11+
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" &>/dev/null; then
        version="$("$candidate" --version 2>&1 | grep -Eo '[0-9]+\.[0-9]+')"
        major="${version%.*}"
        minor="${version#*.}"
        if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python 3.11 or later is required."
    echo "Install Python 3.11+ and try again."
    exit 1
fi

echo "Using: $PYTHON ($("$PYTHON" --version))"

# Check for uv
if command -v uv &>/dev/null; then
    echo "Using uv for installation"
    cd "$INSTALL_DIR"
    uv sync --all-groups
    echo ""
    echo "Installation complete."
else
    echo "uv not found — falling back to pip/venv"
    echo "Installing uv is recommended for faster and more reliable installs."
    echo ""

    VENV_DIR="$INSTALL_DIR/.venv"
    if [ -d "$VENV_DIR" ]; then
        echo "Virtual environment already exists at $VENV_DIR"
        echo "Remove it first or use a different directory."
        echo "To remove: rm -rf $VENV_DIR"
        exit 1
    fi

    "$PYTHON" -m venv "$VENV_DIR"
    echo "Created virtual environment at $VENV_DIR"

    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -e "$INSTALL_DIR"
    "$VENV_DIR/bin/pip" install pytest ruff mypy

    echo ""
    echo "Installation complete."
    echo "Activate with: source $VENV_DIR/bin/activate"
fi

# Show Mystic configuration example
cat <<EOF

========================================
 Mystic BSS door command example
========================================

Add an external program in Mystic Config with:

  Command line:
    $INSTALL_DIR/.venv/bin/aidoor \\
      --config $INSTALL_DIR/config/aidoor.toml \\
      --door32 "%PDOOR32.SYS"

  Working directory:
    $INSTALL_DIR

  Drop file type: DOOR32

  IMPORTANT:
  - Verify the drop-file variable name for your Mystic version.
  - Test with 'aidoor --local' before adding to Mystic.
  - M0 does NOT include AI chat functionality.

========================================
EOF
