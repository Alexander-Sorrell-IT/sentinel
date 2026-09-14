#!/bin/bash
# SENTINEL — One command. Hit enter. Everything happens automatically.
# - Launches the Swift teleprompter (follows demo via /tmp/sentinel_state)
# - Runs demo_master.py — writes state file at each phase
# No camera. No talking. No window arranging.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEMO_KIT="$(dirname "$SCRIPT_DIR")"
VENV="$SCRIPT_DIR/.venv/bin/python"
ENV_FILE="$SCRIPT_DIR/.env"
STATE="/tmp/sentinel_state"

# ── Load keys ─────────────────────────────────────────────────────────────
if [ -f "$ENV_FILE" ]; then
    set -o allexport
    source "$ENV_FILE"
    set +o allexport
fi

: "${ANTHROPIC_API_KEY:?Missing — add ANTHROPIC_API_KEY to .env}"
: "${WASMER_TOKEN:?Missing — add WASMER_TOKEN to .env}"
: "${TENKI_SESSION:?Missing — add TENKI_SESSION to .env}"

# ── Reset state file ───────────────────────────────────────────────────────
echo "0" > "$STATE"

# ── Launch Swift teleprompter (floats above terminal, polls state file) ────
"$DEMO_KIT/teleprompter" "$STATE" &
TP_PID=$!

# Give the window time to appear
sleep 1

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   SENTINEL  ·  Demo starting...      ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# ── Run demo ───────────────────────────────────────────────────────────────
cd "$SCRIPT_DIR"
"$VENV" demo_master.py

# ── Clean up teleprompter ──────────────────────────────────────────────────
wait $TP_PID 2>/dev/null || true
