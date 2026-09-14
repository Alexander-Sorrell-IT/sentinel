#!/bin/bash
# SENTINEL — One screen, split in half. Left = demo. Right = teleprompter.

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

export PYTHONUNBUFFERED=1

# ── Reset state file ───────────────────────────────────────────────────────
echo "0" > "$STATE"

# ── Ensure Terminal is not in macOS native fullscreen ──────────────────────
osascript <<'EOF' >/dev/null 2>&1
tell application "System Events"
    tell process "Terminal"
        try
            if value of attribute "AXFullScreen" of front window then
                set value of attribute "AXFullScreen" of front window to false
                delay 0.8
            end if
        end try
    end tell
end tell
EOF

# ── Get screen dimensions ──────────────────────────────────────────────────
SCREEN_INFO=$(swift -e '
import Cocoa
if let s = NSScreen.main {
    let f = s.frame
    let v = s.visibleFrame
    let menuH = max(25, Int(f.height - (v.origin.y + v.height)))
    print("\(Int(f.width)) \(Int(f.height)) \(Int(v.width / 2)) \(menuH)")
} else {
    print("1440 900 720 25")
}
')
read -r SCREEN_W SCREEN_H HALF_W MENU_H <<< "$SCREEN_INFO"

# ── Position THIS terminal window on the LEFT half ────────────────────────
osascript <<EOF >/dev/null 2>&1
tell application "Terminal"
    activate
    set bounds of front window to {0, $MENU_H, $HALF_W, $SCREEN_H}
    try
        set current settings of front window to settings set "Pro"
    end try
    set font size of front window to 14
end tell
EOF

# ── Check for flags ────────────────────────────────────────────────────────
USE_CAM=0
NO_REC=0
for arg in "$@"; do
    if [ "$arg" = "--debug" ]; then
        export SENTINEL_DEBUG=1
        echo "  [DEBUG] Debug mode active."
        echo "  [DEBUG] Teleprompter log: /tmp/sentinel_teleprompter.log"
    fi
    if [ "$arg" = "--cam" ]; then USE_CAM=1; fi
    if [ "$arg" = "--no-rec" ]; then NO_REC=1; fi
done

# ── Auto-recorder (CleanRec) setup ─────────────────────────────────────────
CLEANREC="/Users/broodierchip-m1air/Desktop/foundersmax-refund-agent/loom/cleanrec/CleanRec.app/Contents/MacOS/CleanRec"
STAMP="$(date +%H%M%S)"
TRIG="/tmp/sentinel_rec_trigger"
REC_OUT="$HOME/Desktop/sentinel_demo_${STAMP}.mp4"
rm -f "$TRIG"

REC_PID=""
if [ -x "$CLEANREC" ] && [ "$NO_REC" -eq 0 ]; then
    "$CLEANREC" --fullscreen 1 --cam "$USE_CAM" --trigger "$TRIG" --out "$REC_OUT" >/dev/null 2>&1 &
    REC_PID=$!
fi

# ── Kill any stale teleprompter instances ──────────────────────────────────
pkill -f "$DEMO_KIT/teleprompter" 2>/dev/null || true

# ── Launch Swift teleprompter (positions itself on the RIGHT half) ──────────
"$DEMO_KIT/teleprompter" "$STATE" 2>/tmp/sentinel_teleprompter.log &
TP_PID=$!
sleep 0.5

# ── Keep focus on Terminal ─────────────────────────────────────────────────
osascript -e 'tell application "Terminal" to activate' >/dev/null 2>&1

# ── Clean banner hold — ENTER starts all 3 (Demo + Prompter + Recording) ───
echo ""
echo "  ╔══════════════════════════════════════════════════════════════════╗"
echo "  ║   SENTINEL  ·  Agentic Security  ·  SF Hackathon 2026            ║"
echo "  ╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "  ✓ Windows locked 50/50 (Terminal left, Teleprompter right)"
if [ -n "$REC_PID" ]; then
    echo "  ✓ Screen recorder armed -> ~/Desktop/sentinel_demo_${STAMP}.mp4"
    echo ""
    printf "  \033[1;92m▸ Press ENTER — recording, teleprompter, and demo start together…\033[0m"
else
    echo ""
    printf "  \033[1;93m▸ Press ENTER to begin…\033[0m"
fi
read -r _ || true
echo ""
touch "$TRIG" 2>/dev/null || true

# ── Run demo ───────────────────────────────────────────────────────────────
cd "$SCRIPT_DIR"
"$VENV" demo_master.py --log /tmp/sentinel_run.txt "$@"

# ── Hold closing screen 4s for video capture ───────────────────────────────
sleep 4

# ── Stop recording and finalize MP4 ────────────────────────────────────────
if [ -n "$REC_PID" ]; then
    kill -INT "$REC_PID" 2>/dev/null || true
    wait "$REC_PID" 2>/dev/null || true
    REC_PID=""
    echo ""
    echo "  ╔══════════════════════════════════════════════════════════════════╗"
    echo "  ║  ✓ Video saved: ~/Desktop/sentinel_demo_${STAMP}.mp4"
    echo "  ╚══════════════════════════════════════════════════════════════════╝"
    echo ""
fi

# ── Clean up teleprompter ──────────────────────────────────────────────────
kill $TP_PID 2>/dev/null || true




