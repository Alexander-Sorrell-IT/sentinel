"""End-to-end engine test: the local key result (OFF -> FAILED, ON -> CERTIFIED)."""
from sentinel.contracts import PolicyContract
from sentinel.leaderboard import make_entry, render_leaderboard
from sentinel.run import evaluate_all, run_sentinel
from sut.claims_agent import run as sut_run


def _policy() -> PolicyContract:
    return PolicyContract(
        allowed_tools=["lookup_claim"],
        approval_required_tools=["approve_claim"],
        forbidden_tools=["delete_claim"],
        sensitive_fields=["ssn"],
    )


def test_detection_mode_fails_and_reports_critical():
    criticals = []
    md, data = run_sentinel(
        _policy(), sut_run, enforce=False, on_critical=criticals.append
    )
    assert data["summary"]["certified"] is False
    assert "FAILED" in md
    assert any(v.severity == "critical" for v in criticals)


def test_enforcement_mode_certified():
    md, data = run_sentinel(_policy(), sut_run, enforce=True)
    assert data["summary"]["certified"] is True
    assert "CERTIFIED" in md


def test_leaderboard_climb_v2_ranks_above_v1():
    policy = _policy()
    v1 = evaluate_all(policy, sut_run, enforce=False)  # guardrail OFF
    v2 = evaluate_all(policy, sut_run, enforce=True)   # guardrail ON
    e1 = make_entry("claims", "v1", "claude", v1)
    e2 = make_entry("claims", "v2", "claude", v2)
    assert e1.score == 0
    assert e2.score == 100
    md = render_leaderboard([e1, e2])
    assert md.index("v2") < md.index("v1")
