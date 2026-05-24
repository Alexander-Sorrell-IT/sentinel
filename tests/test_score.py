"""Tests for the reliability score."""
from sentinel.contracts import Verdict
from sentinel.score import reliability_score


def _v(passed: bool, severity: str) -> Verdict:
    return Verdict(
        scenario_id="s",
        passed=passed,
        severity=severity,
        reason="r",
        failing_step=None if passed else 0,
    )


def test_all_pass_is_100():
    assert reliability_score([_v(True, "none"), _v(True, "none")]) == 100


def test_all_critical_fail_is_0():
    assert reliability_score([_v(False, "critical"), _v(False, "critical")]) == 0


def test_empty_is_0():
    assert reliability_score([]) == 0


def test_high_failure_scores_above_critical():
    assert reliability_score([_v(False, "high")]) > reliability_score(
        [_v(False, "critical")]
    )


def test_mixed_pass_and_critical_is_50():
    assert reliability_score([_v(True, "none"), _v(False, "critical")]) == 50
