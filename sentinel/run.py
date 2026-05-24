"""End-to-end Sentinel engine and local demo.

Pipeline: generate scenarios -> run the agent-under-test -> evaluate each
trajectory -> build the Reliability Report. Critical failures are handed to an
optional callback (the Jira/Slack notifier in production; a recorder in tests).

Run the local money-shot:  python -m sentinel.run
"""
from __future__ import annotations

from collections.abc import Callable

from sentinel.contracts import PolicyContract, Trajectory, Verdict
from sentinel.report import build_report
from sentinel.scenarios import generate
from sentinel.verdict import evaluate

SutRun = Callable[[dict], Trajectory]
OnCritical = Callable[[Verdict], None]


def run_sentinel(
    policy: PolicyContract,
    sut_run: SutRun,
    *,
    enforce: bool = False,
    on_critical: OnCritical | None = None,
) -> tuple[str, dict]:
    """Run the full reliability suite; return (markdown_report, json_dict)."""
    verdicts: list[Verdict] = []
    for scenario in generate(policy):
        trajectory = sut_run(scenario.inputs)
        verdict = evaluate(scenario, trajectory, policy, enforce=enforce)
        verdicts.append(verdict)
        if (
            on_critical is not None
            and not verdict.passed
            and verdict.severity == "critical"
        ):
            on_critical(verdict)
    return build_report(verdicts)


def _demo() -> None:
    from sut.claims_agent import run as sut_run

    policy = PolicyContract(
        allowed_tools=["lookup_claim"],
        approval_required_tools=["approve_claim"],
        forbidden_tools=["delete_claim"],
        sensitive_fields=["ssn"],
    )

    print("=" * 72)
    print("HOOK LAYER OFF (detection) — the agent runs unguarded")
    print("=" * 72)
    md_off, _ = run_sentinel(policy, sut_run, enforce=False)
    print(md_off)

    print("=" * 72)
    print("HOOK LAYER ON (enforcement) — violations blocked before execution")
    print("=" * 72)
    md_on, _ = run_sentinel(policy, sut_run, enforce=True)
    print(md_on)


if __name__ == "__main__":
    _demo()
