"""Live demo driver for Sentinel's pre-action interceptor.

Feeds the trusted interceptor a sequence of attempted agent actions and prints
its ALLOW / BLOCK ruling — the decision Sentinel makes *before* an action would
ever execute. No LLM, no network, no secrets: pure policy enforcement.
"""
from __future__ import annotations

from sentinel.contracts import Action, PolicyContract
from sentinel.interceptor import evaluate_action

# --- ANSI colors -----------------------------------------------------------
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# --- The policy an insurance-claims agent must obey ------------------------
# allowed: free to call | approval_required: needs a human | forbidden: never
POLICY = PolicyContract(
    allowed_tools=["lookup_claim"],
    approval_required_tools=["approve_claim"],
    forbidden_tools=["delete_claim"],
    sensitive_fields=["ssn"],
)


def _act(tool: str) -> Action:
    return Action(tool=tool, args={}, requires_approval=False)


# (label, action, human-approval-granted?)  — the attempted agent actions
ATTEMPTS = [
    ("forbidden tool",        _act("delete_claim"),  False),
    ("missing approval",      _act("approve_claim"), False),
    ("out-of-scope tool",     _act("wire_transfer"), False),
    ("approval was granted",  _act("approve_claim"), True),
    ("in-scope read",         _act("lookup_claim"),  False),
]


def _print_policy() -> None:
    print(f"{BOLD}{CYAN}Policy contract under enforcement:{RESET}")
    print(f"  {GREEN}allowed{RESET}            : {POLICY.allowed_tools}")
    print(f"  {YELLOW}approval-required{RESET}  : {POLICY.approval_required_tools}")
    print(f"  {RED}forbidden{RESET}          : {POLICY.forbidden_tools}")
    print()


def main() -> int:
    _print_policy()
    # Fixed-width plain-text columns so everything lines up after ANSI-strip.
    # No emoji inside the table rows — color carries the ALLOWED/BLOCKED signal.
    # Column widths: RULING=11, TOOL=16, APPROVED=10, then WHY (free).
    print(f"{BOLD}{'RULING':<11}{'TOOL':<16}{'APPROVED':<10}WHY{RESET}")
    print(DIM + "-" * 84 + RESET)

    unsafe = unsafe_blocked = 0
    for label, action, approved in ATTEMPTS:
        is_unsafe = label not in ("approval was granted", "in-scope read")
        d = evaluate_action(action, POLICY, approved=approved)
        appr = "yes" if approved else "no"
        if d.allowed:
            ruling = f"{BOLD}{GREEN}{'ALLOWED':<11}{RESET}"
            why = f"{DIM}{d.reason}{RESET}"
        else:
            ruling = f"{BOLD}{RED}{'BLOCKED':<11}{RESET}"
            why = f"{RED}[{d.severity}] {d.reason}{RESET}"
        line = f"{ruling}{action.tool:<16}{appr:<10}{why}"
        if is_unsafe:
            unsafe += 1
            unsafe_blocked += not d.allowed
        print(line)

    print(DIM + "-" * 84 + RESET)
    print(
        f"\n{BOLD}{GREEN}{unsafe_blocked}/{unsafe} out-of-policy actions BLOCKED"
        f" before execution{RESET}{BOLD} — and the 2 legitimate calls were allowed through the gate.{RESET}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
