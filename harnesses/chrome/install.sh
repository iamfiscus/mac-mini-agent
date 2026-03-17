#!/bin/bash
# Install the chrome harness as a CLI command
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "$0")" && pwd)"

cat > /usr/local/bin/chrome-harness << EOF
#!/bin/bash
cd "$HARNESS_DIR" && exec uv run python main.py "\$@"
EOF
chmod +x /usr/local/bin/chrome-harness

echo "Installed: chrome-harness"
echo "Usage: chrome-harness navigate <url>"
