"""End-to-end engine test: the local money-shot (OFF -> FAILED, ON -> CERTIFIED)."""
from sentinel.contracts import PolicyContract
from sentinel.run import run_sentinel
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
