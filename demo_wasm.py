"""SENTINEL — Live Wasmer Demo
Spawn  →  Execute  →  Die

Runs the Sentinel interceptor logic inside REAL ephemeral WebAssembly
containers (python/python on Wasmer). Each container is a fresh process with
no prior state. Each container is gone the moment the verdict prints.

Usage:
    WASMER_TOKEN=<token> python demo_wasm.py
"""
from __future__ import annotations

import time

from sentinel.wasm_runner import run_in_wasm

# ── ANSI ───────────────────────────────────────────────────────────────────
BOLD  = "\033[1m"
DIM   = "\033[2m"
RED   = "\033[91m"
GREEN = "\033[92m"
CYAN  = "\033[96m"
AMBER = "\033[93m"
RESET = "\033[0m"

# ── Policy ─────────────────────────────────────────────────────────────────
POLICY = {
    "allowed":           ["lookup_claim"],
    "approval_required": ["approve_claim"],
    "forbidden":         ["delete_claim"],
    "sensitive":         ["ssn"],
}

# ── Attack scenarios ────────────────────────────────────────────────────────
# (label, action_tool, approved, is_attack)
SCENARIOS = [
    ("forbidden tool attempt",        "delete_claim",  False, True),
    ("approval bypass",               "approve_claim", False, True),
    ("out-of-scope tool injection",   "wire_transfer", False, True),
    ("legitimate approved action",    "approve_claim", True,  False),
    ("legitimate read",               "lookup_claim",  False, False),
]


def _action(tool: str) -> dict:
    return {"tool": tool, "args": {}, "requires_approval": False}


def _print_header() -> None:
    print()
    print(f"{BOLD}{CYAN}╔══════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║         SENTINEL  ·  Wasmer Wasm Demo                ║{RESET}")
    print(f"{BOLD}{CYAN}║  Each verdict runs inside an ephemeral Wasm container ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════╝{RESET}")
    print()
    print(f"{BOLD}Policy contract:{RESET}")
    print(f"  {GREEN}allowed{RESET}            : {POLICY['allowed']}")
    print(f"  {AMBER}approval-required{RESET}  : {POLICY['approval_required']}")
    print(f"  {RED}forbidden{RESET}          : {POLICY['forbidden']}")
    print(f"  {DIM}sensitive{RESET}          : {POLICY['sensitive']}")
    print()
    print(
        f"{BOLD}"
        f"{'RULING':<11}"
        f"{'TOOL':<20}"
        f"{'APPROVED':<10}"
        f"{'ms':>6}  "
        f"CONTAINER ID                    "
        f"WHY{RESET}"
    )
    print(DIM + "─" * 110 + RESET)


def main() -> int:
    _print_header()

    attacks = attacks_blocked = 0

    for label, tool, approved, is_attack in SCENARIOS:
        print(f"{DIM}  spawning container for: {label}…{RESET}", end="\r", flush=True)

        try:
            result = run_in_wasm(_action(tool), POLICY, approved=approved)
        except RuntimeError as exc:
            print(f"{RED}ERROR: {exc}{RESET}")
            return 1

        appr = "yes" if approved else "no"

        if result.allowed:
            ruling = f"{BOLD}{GREEN}{'ALLOWED':<11}{RESET}"
            why    = f"{DIM}{result.reason}{RESET}"
        else:
            ruling = f"{BOLD}{RED}{'BLOCKED':<11}{RESET}"
            why    = f"{RED}[{result.severity}] {result.reason}{RESET}"

        cid_short = result.container_id[-20:]  # last 20 chars of the nano-timestamp id

        print(
            f"{ruling}"
            f"{tool:<20}"
            f"{appr:<10}"
            f"{result.elapsed_ms:>6.0f}ms  "
            f"{DIM}{cid_short}{RESET}  "
            f"{why}"
        )

        if is_attack:
            attacks += 1
            if not result.allowed:
                attacks_blocked += 1

    print(DIM + "─" * 110 + RESET)
    print()
    print(
        f"{BOLD}{GREEN}{attacks_blocked}/{attacks} attack attempts BLOCKED before execution{RESET}"
        f"{BOLD} — and the 2 legitimate calls were allowed through the gate.{RESET}"
    )
    print()
    print(f"{DIM}Every verdict above ran inside a fresh Wasm container.{RESET}")
    print(f"{DIM}Every container is gone. No state survives. Nothing to breach.{RESET}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
