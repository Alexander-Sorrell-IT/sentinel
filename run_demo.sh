#!/bin/bash
# SENTINEL — Launch script
# Opens teleprompter in a new Terminal window, then runs the main demo here.
# Screen-record both windows side by side. No camera. No talking.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPE="/tmp/sentinel_demo_pipe"

# Clean up old pipe
rm -f "$PIPE"

# Keys — set these in your environment or a local .env file, never commit them
# export ANTHROPIC_API_KEY="sk-ant-..."
# export WASMER_TOKEN="wap_..."
# export TENKI_SESSION="<sandbox-id>"
: "${ANTHROPIC_API_KEY:?Set ANTHROPIC_API_KEY before running}"
: "${WASMER_TOKEN:?Set WASMER_TOKEN before running}"
: "${TENKI_SESSION:?Set TENKI_SESSION before running}"
VENV="$SCRIPT_DIR/.venv/bin/python"

echo ""
echo "  Opening teleprompter window..."
echo "  Arrange it on the RIGHT side of your screen."
echo ""

# Open teleprompter in a new Terminal window
osascript <<EOF
tell application "Terminal"
    do script "cd '$SCRIPT_DIR' && '$VENV' teleprompter.py"
    activate
end tell
EOF

# Give the teleprompter a moment to start and create the pipe
sleep 2

echo "  Starting demo in 3 seconds..."
echo "  Arrange THIS window on the LEFT side."
echo ""
sleep 3

# Run the main demo — signals go to the teleprompter automatically
cd "$SCRIPT_DIR"
"$VENV" demo_master.py
