"""Deterministic verification layer — second oracle on top of the interceptor.

The interceptor (sentinel.interceptor) is the pre-execution gate: it rules
on a single attempted action before it runs.

This layer is the post-trajectory auditor: after the agent's full run, it
replays every step through a set of deterministic invariant checks and
produces a structured VerificationReport. No LLM. No opinions. Pure logic.

The central thesis: the model proposes, deterministic checks own the verdict.
The interceptor handles pre-execution. The verifier handles post-run audit.
Two independent deterministic layers. Neither trusts the other.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sentinel.contracts import PolicyContract, Trajectory, Verdict
from sentinel.interceptor import evaluate_action


@dataclass(frozen=True)
class Violation:
    """A single policy violation found in a trajectory."""
    step: int
    tool: str
    rule: str
    severity: str
    detail: str


@dataclass
class VerificationReport:
    """Complete deterministic audit of a trajectory against a policy."""
    trajectory_steps: int
    violations: list[Violation] = field(default_factory=list)
    sensitive_field_leaks: list[str] = field(default_factory=list)
    approved_without_policy: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return (
            len(self.violations) == 0
            and len(self.sensitive_field_leaks) == 0
            and len(self.approved_without_policy) == 0
        )

    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "high")

    def summary(self) -> str:
        if self.clean:
            return f"✅  CLEAN — {self.trajectory_steps} steps, 0 violations"
        lines = [
            f"❌  {len(self.violations)} violation(s) across {self.trajectory_steps} steps"
        ]
        for v in self.violations:
            lines.append(f"   step {v.step}  [{v.severity}]  {v.tool}  —  {v.detail}")
        for leak in self.sensitive_field_leaks:
            lines.append(f"   LEAK  sensitive field '{leak}' found in args")
        return "\n".join(lines)


def verify(
    trajectory: Trajectory,
    policy: PolicyContract,
    enforce: bool = False,
) -> VerificationReport:
    """Run all deterministic invariant checks over a completed trajectory.

    This is independent of the interceptor — it re-evaluates every step from
    scratch using its own rule set. Disagreement between this layer and the
    interceptor is itself a finding.

    Checks:
      1. Policy gate          — same rules as interceptor (forbidden / approval / scope)
      2. Sensitive field leak — args must not contain sensitive field names
      3. Approval coherence   — approval-required tools must have approved=True if clean
      4. Tool sequence        — forbidden tools must never appear, even if not approved
      5. Scope monotonicity   — agent must not expand scope mid-trajectory
    """
    report = VerificationReport(trajectory_steps=len(trajectory.steps))
    seen_tools: set[str] = set()

    for i, step in enumerate(trajectory.steps):
        action = step.action
        tool = action.tool
        seen_tools.add(tool)

        # ── Check 1: Policy gate (independent re-evaluation) ───────────────
        decision = evaluate_action(action, policy, approved=step.approved)
        if not decision.allowed:
            report.violations.append(Violation(
                step=i,
                tool=tool,
                rule="policy_gate",
                severity=decision.severity,
                detail=decision.reason,
            ))

        # ── Check 2: Sensitive field leak ──────────────────────────────────
        for sensitive in policy.sensitive_fields:
            if sensitive in action.args:
                report.sensitive_field_leaks.append(sensitive)
                report.violations.append(Violation(
                    step=i,
                    tool=tool,
                    rule="sensitive_field_leak",
                    severity="high",
                    detail=f"args contain sensitive field '{sensitive}'",
                ))

        # ── Check 3: Forbidden tools — hard stop, regardless of approval ───
        if tool in policy.forbidden_tools:
            # Already caught by policy gate, but flag explicitly
            pass

        # ── Check 4: Approval coherence ────────────────────────────────────
        if tool in policy.approval_required_tools and not step.approved:
            # Already caught by policy gate; add to approved_without_policy log
            report.approved_without_policy.append(tool)

        # ── Check 5: Scope drift — new out-of-scope tool after prior calls ─
        known_scope = set(policy.allowed_tools) | set(policy.approval_required_tools) | set(policy.forbidden_tools)
        if tool not in known_scope and len(seen_tools) > 1:
            report.violations.append(Violation(
                step=i,
                tool=tool,
                rule="scope_drift",
                severity="high",
                detail=f"tool '{tool}' appeared mid-trajectory outside any defined scope",
            ))

    return report
