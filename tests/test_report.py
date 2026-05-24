"""Tests for the Reliability Report builder."""
import json

from sentinel.contracts import Verdict
from sentinel.report import build_report


def test_mixed_verdicts_failed_banner_and_counts():
    verdicts = [
        Verdict(scenario_id="s1", passed=True, severity="none", reason="ok"),
        Verdict(
            scenario_id="s2",
            passed=False,
            severity="critical",
            reason="skipped approval",
            failing_step=1,
        ),
    ]
    md, data = build_report(verdicts)
    assert "FAILED" in md
    assert "s2" in md
    assert "critical" in md
    assert data["summary"] == {
        "total": 2,
        "passed": 1,
        "failed": 1,
        "certified": False,
        "score": 50,
    }
    assert "50" in md  # reliability score shown in the report
    # JSON must be serializable
    json.dumps(data)


def test_all_pass_certified_banner():
    verdicts = [Verdict(scenario_id="s1", passed=True, severity="none", reason="ok")]
    md, data = build_report(verdicts)
    assert "CERTIFIED" in md
    assert "FAILED" not in md
    assert data["summary"]["certified"] is True


def test_empty_is_not_certified():
    _md, data = build_report([])
    assert data["summary"]["certified"] is False
    assert data["summary"]["total"] == 0
