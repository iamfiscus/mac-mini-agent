#!/bin/bash
# Start listen server with brain integration
export PATH="$HOME/.local/bin:$HOME/.opencode/bin:$PATH"
export BRAIN_MCP_URL="http://gertie.local:3300/mcp"
export BRAIN_KEY="brk_acd21468f30dd3a895a4f0618f79211be3f003e95e62bd8a66b1eef80db9d380"
export DEVICE_ID="hal9000"
export DISPLAY=":1"
export XAUTHORITY="/run/user/1000/gdm/Xauthority"

cd "$(dirname "$0")/../apps/listen"
exec uv run python main.py
