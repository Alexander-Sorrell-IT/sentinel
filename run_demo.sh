#!/bin/bash
# SENTINEL — One command. Hit enter. Everything happens automatically.
# - Sources .env for keys (never committed)
# - Opens teleprompter in a NEW Terminal window, positioned RIGHT half
# - Positions THIS window on the LEFT half
# - Counts down 3 seconds
# - Runs the full demo — teleprompter advances in sync
# No camera. No talking. No window arranging.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPE="/tmp/sentinel_demo_pipe"
VENV="$SCRIPT_DIR/.venv/bin/python"
ENV_FILE="$SCRIPT_DIR/.env"

# ── Load keys from .env ────────────────────────────────────────────────────
if [ -f "$ENV_FILE" ]; then
    set -o allexport
    source "$ENV_FILE"
    set +o allexport
fi

: "${ANTHROPIC_API_KEY:?Missing — add ANTHROPIC_API_KEY to .env}"
: "${WASMER_TOKEN:?Missing — add WASMER_TOKEN to .env}"
: "${TENKI_SESSION:?Missing — add TENKI_SESSION to .env}"

# ── Clean up old pipe ──────────────────────────────────────────────────────
rm -f "$PIPE"

# ── Get screen dimensions ──────────────────────────────────────────────────
SCREEN=$(osascript -e 'tell application "Finder" to get bounds of window of desktop')
# SCREEN is like "0, 0, 2560, 1440" — grab 3rd and 4th comma-separated fields
W=$(echo "$SCREEN" | tr -d ' ' | cut -d',' -f3)
H=$(echo "$SCREEN" | tr -d ' ' | cut -d',' -f4)
# Fallback to sensible defaults if detection fails
W=${W:-1920}
H=${H:-1080}
HALF=$(( W / 2 ))

# ── Open teleprompter on the RIGHT ────────────────────────────────────────
osascript <<APPLESCRIPT
tell application "Terminal"
    set tpWin to do script "cd '$SCRIPT_DIR' && '$VENV' teleprompter.py"
    delay 0.6
    set bounds of front window to {$HALF, 0, $W, $H}
    try
        set current settings of front window to settings set "Pro"
    end try
    set font size of front window to 16
end tell
APPLESCRIPT

# ── Position demo window on the LEFT ──────────────────────────────────────
osascript <<APPLESCRIPT
tell application "Terminal"
    set bounds of front window to {0, 0, $HALF, $H}
    try
        set current settings of front window to settings set "Pro"
    end try
    set font size of front window to 15
    activate
end tell
APPLESCRIPT

# ── Wait for teleprompter pipe ─────────────────────────────────────────────
echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   SENTINEL  ·  Demo launching...     ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

for i in $(seq 1 20); do
    [ -e "$PIPE" ] && break
    sleep 0.3
done

[ ! -e "$PIPE" ] && echo "  WARNING: teleprompter not ready — continuing anyway"

echo "  3..."
sleep 1
echo "  2..."
sleep 1
echo "  1..."
sleep 1
echo ""

# ── Run ───────────────────────────────────────────────────────────────────
cd "$SCRIPT_DIR"
"$VENV" demo_master.py
