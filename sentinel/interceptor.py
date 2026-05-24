"""Hook-based pre-action interceptor — the ground-truth reliability check.

Given an attempted Action, the agent's PolicyContract, and whether human
approval was granted, decide ALLOW or BLOCK *before* the action executes, and
say why. This is the trusted oracle the verdict layer compares observed runs
against. No fallbacks: an action that isn't explicitly permitted is blocked.
"""
from __future__ import annotations

from dataclasses import dataclass

from sentinel.contracts import Action, PolicyContract, Severity


@dataclass(frozen=True)
class Decision:
    """The interceptor's ruling on a single attempted action."""

    allowed: bool
    severity: Severity
    reason: str


def evaluate_action(action: Action, policy: PolicyContract, approved: bool) -> Decision:
    """Rule on one attempted action against the policy contract."""
    tool = action.tool

    if tool in policy.forbidden_tools:
        return Decision(False, "critical", f"forbidden tool '{tool}' was attempted")

    if tool in policy.approval_required_tools and not approved:
        return Decision(
            False,
            "critical",
            f"tool '{tool}' requires human approval but none was granted",
        )

    in_scope = tool in policy.allowed_tools or tool in policy.approval_required_tools
    if not in_scope:
        return Decision(
            False, "high", f"tool '{tool}' is outside the agent's allowed scope"
        )

    return Decision(True, "none", f"tool '{tool}' permitted")
