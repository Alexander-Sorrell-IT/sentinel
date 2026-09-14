"""SENTINEL Teleprompter

Reads phase signals from the demo's named pipe and displays
the matching narration slide in a second terminal window.
Auto-advances in sync with demo_master.py. No keypresses needed.

Run in a second terminal BEFORE starting demo_master.py:
    python teleprompter.py
"""
from __future__ import annotations

import os
import sys
import time

PIPE = "/tmp/sentinel_demo_pipe"

BOLD  = "\033[1m"
DIM   = "\033[2m"
RED   = "\033[91m"
GREEN = "\033[92m"
CYAN  = "\033[96m"
AMBER = "\033[93m"
BLUE  = "\033[94m"
WHITE = "\033[97m"
BG_DARK = "\033[40m"
RESET = "\033[0m"

CLEAR = "\033[2J\033[H"

# ── Slides keyed by phase signal sent from demo_master.py ─────────────────

SLIDES: dict[str, list[str]] = {
    "OPENING": [
        f"{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════════╗{RESET}",
        f"{BOLD}{CYAN}║              S E N T I N E L                                        ║{RESET}",
        f"{BOLD}{CYAN}║              Agentic Security · SF Hackathon 2026                    ║{RESET}",
        f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════════════════╝{RESET}",
        "",
        f"{WHITE}The problem:{RESET}",
        "",
        f"  AI agents inside enterprise systems have {BOLD}no pre-execution{RESET}",
        f"  policy enforcement.",
        "",
        f"  Guardrails are {RED}detective{RESET} — they find the violation",
        f"  {RED}after{RESET} the wire transfer.",
        f"  {RED}After{RESET} the deleted record.",
        f"  {RED}After{RESET} the bypassed approval.",
        "",
        f"{WHITE}The Sentinel answer:{RESET}",
        "",
        f"  Sit {BOLD}between{RESET} the agent and the world.",
        f"  Every action passes through a typed {BOLD}PolicyContract{RESET}",
        f"  before it executes.",
        "",
        f"  {DIM}No LLM decides. No config surface. No state to attack.{RESET}",
    ],

    "PHASE1": [
        f"{BOLD}{RED}╔══════════════════════════════════════════════════════════════════════╗{RESET}",
        f"{BOLD}{RED}║  PHASE 1  —  NO PROTECTION                                           ║{RESET}",
        f"{BOLD}{RED}╚══════════════════════════════════════════════════════════════════════╝{RESET}",
        "",
        f"{WHITE}What you're watching:{RESET}",
        "",
        f"  {BOLD}claude-sonnet-4-6{RESET} (RedAgent) invents attack probes.",
        f"  {BOLD}claude-sonnet-4-6{RESET} (claims agent) makes real API calls.",
        f"  The claims database injects a malicious payload into",
        f"  the tool result — indirect prompt injection.",
        "",
        f"  Policy under test:",
        f"    {GREEN}allowed{RESET}            lookup_claim",
        f"    {AMBER}approval-required{RESET}  approve_claim",
        f"    {RED}forbidden{RESET}          delete_claim",
        "",
        f"  Two independent oracles confirm every violation:",
        f"    {CYAN}Interceptor{RESET}  — pre-execution gate",
        f"    {BLUE}Verifier{RESET}    — post-trajectory audit",
        "",
        f"  {RED}Score: 0/100. Every attack executes.{RESET}",
    ],

    "PHASE2": [
        f"{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════════╗{RESET}",
        f"{BOLD}{CYAN}║  PHASE 2  —  WASMER  (WebAssembly container)                         ║{RESET}",
        f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════════════════╝{RESET}",
        "",
        f"{WHITE}What you're watching:{RESET}",
        "",
        f"  The {RED}same attack{RESET} hits the Wasmer interceptor.",
        "",
        f"  Wasmer spawns a fresh {BOLD}WebAssembly container{RESET}.",
        f"  The PolicyContract evaluates inside it.",
        f"  The container {RED}dies{RESET} the moment the verdict returns.",
        "",
        f"  {DIM}~700ms. Container ID changes every run.{RESET}",
        f"  {DIM}Proves no state reuse — nothing persists.{RESET}",
        "",
        f"  The attack cannot execute because",
        f"  {BOLD}the execution path no longer exists.{RESET}",
    ],

    "PHASE3": [
        f"{BOLD}{BLUE}╔══════════════════════════════════════════════════════════════════════╗{RESET}",
        f"{BOLD}{BLUE}║  PHASE 3  —  TENKI CLOUD  (remote Linux sandbox)                     ║{RESET}",
        f"{BOLD}{BLUE}╚══════════════════════════════════════════════════════════════════════╝{RESET}",
        "",
        f"{WHITE}What you're watching:{RESET}",
        "",
        f"  The {RED}same attack{RESET} hits the Tenki interceptor.",
        "",
        f"  Tenki sends it to a {BOLD}remote Linux VM{RESET}.",
        f"  Disposable. Full root. Boots in under a second.",
        f"  Billed per second. Isolated from the host.",
        "",
        f"  {DIM}~600ms. Remote. No host filesystem access.{RESET}",
        "",
        f"  Two different enforcement platforms.",
        f"  {BOLD}Same result: BLOCKED.{RESET}",
    ],

    "PHASE4": [
        f"{BOLD}{GREEN}╔══════════════════════════════════════════════════════════════════════╗{RESET}",
        f"{BOLD}{GREEN}║  PHASE 4  —  HOOK LAYER ON                                           ║{RESET}",
        f"{BOLD}{GREEN}╚══════════════════════════════════════════════════════════════════════╝{RESET}",
        "",
        f"{WHITE}What you're watching:{RESET}",
        "",
        f"  {BOLD}Same agent.{RESET}",
        f"  {BOLD}Same LLM-crafted attacks.{RESET}",
        f"  {BOLD}One control added.{RESET}",
        "",
        f"  The pre-action interceptor now sits between",
        f"  the agent and the world.",
        "",
        f"  Every action passes through the {BOLD}PolicyContract{RESET}",
        f"  before it executes.",
        "",
        f"  {GREEN}Violations cannot run.{RESET}",
        "",
        f"  {DIM}Watch the score flip...{RESET}",
    ],

    "LEADERBOARD": [
        f"{BOLD}{AMBER}╔══════════════════════════════════════════════════════════════════════╗{RESET}",
        f"{BOLD}{AMBER}║  LEADERBOARD  —  The revision climbs                                 ║{RESET}",
        f"{BOLD}{AMBER}╚══════════════════════════════════════════════════════════════════════╝{RESET}",
        "",
        f"  {WHITE}v1  guardrail-OFF{RESET}  →  {RED}Score 0 / 100   FAILED{RESET}",
        f"  {WHITE}v2  guardrail-ON {RESET}  →  {GREEN}Score 100 / 100  CERTIFIED{RESET}",
        "",
        f"  {DIM}Same agent. Same attacks. One control.{RESET}",
    ],

    "CLOSING": [
        f"{BOLD}{GREEN}╔══════════════════════════════════════════════════════════════════════╗{RESET}",
        f"{BOLD}{GREEN}║                                                                      ║{RESET}",
        f"{BOLD}{GREEN}║   Score: 0 → 100.  FAILED → CERTIFIED.                               ║{RESET}",
        f"{BOLD}{GREEN}║   Same agent.  One control.                                          ║{RESET}",
        f"{BOLD}{GREEN}║                                                                      ║{RESET}",
        f"{BOLD}{GREEN}╚══════════════════════════════════════════════════════════════════════╝{RESET}",
        "",
        f"  The interceptor is {BOLD}20 lines of Python{RESET}.",
        f"  No model. No config. No memory.",
        "",
        f"  Enforced by:",
        f"    {CYAN}Wasmer{RESET}  — ephemeral Wasm container, dies on exit",
        f"    {BLUE}Tenki{RESET}   — disposable Linux VM, remote, isolated",
        "",
        f"  {RED}You cannot misconfigure it.{RESET}",
        f"  {RED}You cannot escape it.{RESET}",
        f"  {RED}There is nothing persistent to attack.{RESET}",
        "",
        f"  {BOLD}github.com/Alexander-Sorrell-IT/sentinel{RESET}",
        f"  {DIM}47 / 47 tests passing  ·  Main · Wasmer · Tenki tracks{RESET}",
    ],
}


def _show(slide_key: str) -> None:
    print(CLEAR, end="", flush=True)
    lines = SLIDES.get(slide_key, [f"Unknown slide: {slide_key}"])
    print()
    for line in lines:
        print(f"  {line}")
    print()


def main() -> None:
    READY_PIPE = "/tmp/sentinel_ready_pipe"

    # Create the pipe if it doesn't exist
    if not os.path.exists(PIPE):
        os.mkfifo(PIPE)

    print(CLEAR, end="", flush=True)
    print(f"\n  {BOLD}{CYAN}SENTINEL Teleprompter{RESET}")
    print(f"  {DIM}Waiting for demo to start...{RESET}\n")

    # Open for reading — blocks until the writer opens the other end.
    # Once open, immediately signal run_demo.sh that we're ready.
    pipe_fd = open(PIPE, "r")
    # Write READY to unblock run_demo.sh
    if os.path.exists(READY_PIPE):
        with open(READY_PIPE, "w") as rp:
            rp.write("READY\n")

    with pipe_fd as pipe:
        for raw in pipe:
            signal = raw.strip()
            if not signal:
                continue
            _show(signal)
            if signal == "CLOSING":
                # Hold the closing slide for 10 seconds then exit
                time.sleep(10)
                break

    print(f"\n  {DIM}Demo complete.{RESET}\n")


if __name__ == "__main__":
    main()
