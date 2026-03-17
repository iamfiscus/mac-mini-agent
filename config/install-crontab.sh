#!/bin/bash
# Generate crontab entries from config/schedules.yaml
# Usage: bash config/install-crontab.sh [--dry-run]
#
# Reads schedules.yaml and appends entries to the current user's crontab.
# Existing mini-agent entries (marked with # mini-agent:) are replaced.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCHEDULES="$REPO_DIR/config/schedules.yaml"
SEND="$REPO_DIR/config/send-job.sh"
DRY_RUN="${1:-}"

if [ ! -f "$SCHEDULES" ]; then
    echo "Error: $SCHEDULES not found"
    exit 1
fi

# Parse YAML → cron|name|url|agent|prompt_or_@file
entries=$(python3 -c "
import yaml
with open('$SCHEDULES') as f:
    data = yaml.safe_load(f)
for s in data.get('schedules', []):
    cron = s['cron']
    name = s['name']
    url = s.get('url', 'http://localhost:7600')
    agent = s.get('agent', 'claude')
    if 'prompt_file' in s:
        print(f'{cron}|{name}|{url}|{agent}|@$REPO_DIR/{s[\"prompt_file\"]}')
    else:
        # Replace pipes in prompt to avoid IFS issues
        prompt = s['prompt'].replace('|', ' ')
        print(f'{cron}|{name}|{url}|{agent}|{prompt}')
")

MARKER="# mini-agent:"
new_entries=""

while IFS='|' read -r cron name url agent prompt; do
    cmd="$SEND '$url' '$agent' '$prompt'"
    new_entries+="$cron $cmd $MARKER $name"$'\n'
done <<< "$entries"

if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "Would install these crontab entries:"
    echo "---"
    echo "$new_entries"
    exit 0
fi

# Remove old mini-agent entries, append new ones
existing=$(crontab -l 2>/dev/null || true)
filtered=$(echo "$existing" | grep -v "$MARKER" || true)
echo "${filtered}
${new_entries}" | crontab -

echo "Installed $(echo "$new_entries" | grep -c .) crontab entries"
crontab -l | grep "$MARKER"
