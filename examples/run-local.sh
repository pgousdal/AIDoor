#!/bin/bash
# AIDoor local test mode launcher
# Run directly for testing without Mystic.

set -e

AIDOOR_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$AIDOOR_DIR"

CONFIG_ARGS=""
if [ -n "$AIDOOR_CONFIG" ]; then
    CONFIG_ARGS="--config $AIDOOR_CONFIG"
fi

exec uv run aidoor run --local $CONFIG_ARGS
