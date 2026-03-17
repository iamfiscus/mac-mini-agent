#!/bin/bash
# Wrapper script — install to /usr/local/bin/steer on Linux devices
# so that "steer see --json" works identically to macOS steer
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
STEER_DIR="${STEER_DIR:-$(dirname "$SCRIPT_DIR")/apps/linux-steer}"
cd "$STEER_DIR" && exec uv run python main.py "$@"
