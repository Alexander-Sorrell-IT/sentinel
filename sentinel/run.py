"""End-to-end Sentinel engine and local demo.

Pipeline: generate scenarios -> run the agent-under-test -> evaluate each
trajectory -> build the Reliability Report. Critical failures are handed to an
optional callback (the Jira/Slack notifier in production; a recorder in tests).

Run the local end-to-end demo + leaderboard climb:  python -m sentinel.run
"""
from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path

from sentinel.contracts import PolicyContract, Scenario, Trajectory, Verdict
from sentinel.leaderboard import make_entry, record_entry, render_leaderboard
from sentinel.red_agent import RedAgent
from sentinel.report import build_report
from sentinel.scenarios import generate
from sentinel.verdict import evaluate

SutRun = Callable[[dict], Trajectory]
OnCritical = Callable[[Verdict], None]


def _scenarios(policy: PolicyContract, red_agent: RedAgent | None) -> list[Scenario]:
    return red_agent.generate(policy) if red_agent is not None else generate(policy)


def evaluate_all(
    policy: PolicyContract,
    sut_run: SutRun,
    *,
    enforce: bool = False,
    red_agent: RedAgent | None = None,
) -> list[Verdict]:
    """Run every scenario against the agent-under-test and return the verdicts.

    When `red_agent` is provided, scenarios are crafted by the adversarial LLM
    agent; otherwise the deterministic baseline in `sentinel.scenarios` is used.
    """
    return [
        evaluate(scenario, sut_run(scenario.inputs), policy, enforce=enforce)
        for scenario in _scenarios(policy, red_agent)
    ]


def run_sentinel(
    policy: PolicyContract,
    sut_run: SutRun,
    *,
    enforce: bool = False,
    on_critical: OnCritical | None = None,
    red_agent: RedAgent | None = None,
) -> tuple[str, dict]:
    """Run the full reliability suite; return (markdown_report, json_dict)."""
    verdicts = evaluate_all(policy, sut_run, enforce=enforce, red_agent=red_agent)
    if on_critical is not None:
        for verdict in verdicts:
            if not verdict.passed and verdict.severity == "critical":
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
    board = Path(tempfile.gettempdir()) / "sentinel_leaderboard.json"
    board.unlink(missing_ok=True)

    print("=" * 72)
    print("HOOK LAYER OFF (detection) — the agent runs unguarded")
    print("=" * 72)
    v1 = evaluate_all(policy, sut_run, enforce=False)
    print(build_report(v1)[0])
    record_entry(make_entry("claims-agent", "v1 (guardrail off)", "claude-opus", v1), board)

    print("=" * 72)
    print("HOOK LAYER ON (enforcement) — violations blocked before execution")
    print("=" * 72)
    v2 = evaluate_all(policy, sut_run, enforce=True)
    print(build_report(v2)[0])
    entries = record_entry(
        make_entry("claims-agent", "v2 (guardrail on)", "claude-opus", v2), board
    )

    print("=" * 72)
    print("RELIABILITY LEADERBOARD — the revision climbs from FAILED to CERTIFIED")
    print("=" * 72)
    print(render_leaderboard(entries))


if __name__ == "__main__":
    _demo()
