#!/bin/bash
# AIDoor Mystic BBS door launcher
# Configure Mystic to run this script as the door command.
# Mystic will set %DROP% to the DOOR32.SYS path.
#
# Usage (in Mystic door config):
#   /path/to/aidoor/examples/run-mystic.sh %DROP%
#
# Environment:
#   AIDOOR_CONFIG  - path to config file (optional)

set -e

AIDOOR_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOOR32_PATH="$1"

if [ -z "$DOOR32_PATH" ]; then
    echo "Error: DOOR32.SYS path not provided."
    echo "Usage: $0 <path-to-DOOR32.SYS>"
    exit 1
fi

if [ ! -f "$DOOR32_PATH" ]; then
    echo "Error: DOOR32.SYS not found: $DOOR32_PATH"
    exit 1
fi

cd "$AIDOOR_DIR"

CONFIG_ARGS=""
if [ -n "$AIDOOR_CONFIG" ]; then
    CONFIG_ARGS="--config $AIDOOR_CONFIG"
fi

exec uv run aidoor run --door32 "$DOOR32_PATH" $CONFIG_ARGS
