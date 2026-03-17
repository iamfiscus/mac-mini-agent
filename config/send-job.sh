#!/bin/bash
# Send a job to a Listen server. Used by crontab entries.
# Usage: send-job.sh <url> <agent> <prompt_or_@filepath>
#
# If prompt starts with @, reads from file. Otherwise uses literal text.
set -euo pipefail

URL="${1:?Usage: send-job.sh <url> <agent> <prompt_or_@file>}"
AGENT="${2:-claude}"
PROMPT_ARG="${3:?Missing prompt}"

if [[ "$PROMPT_ARG" == @* ]]; then
    FILE="${PROMPT_ARG#@}"
    PROMPT="$(cat "$FILE")"
else
    PROMPT="$PROMPT_ARG"
fi

# Use python for safe JSON encoding
JSON=$(python3 -c "
import json, sys
print(json.dumps({'prompt': sys.argv[1], 'agent': sys.argv[2]}))
" "$PROMPT" "$AGENT")

curl -s -X POST "$URL/job" -H 'Content-Type: application/json' -d "$JSON"
