#!/bin/bash
# Install the firefox harness as a CLI command
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "$0")" && pwd)"

cat > /usr/local/bin/firefox-harness << EOF
#!/bin/bash
cd "$HARNESS_DIR" && exec uv run python main.py "\$@"
EOF
chmod +x /usr/local/bin/firefox-harness

echo "Installed: firefox-harness"
echo "Usage: firefox-harness navigate <url>"
