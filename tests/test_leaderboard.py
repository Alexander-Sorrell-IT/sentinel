"""Tests for the reliability leaderboard."""
import json

from sentinel.contracts import Verdict
from sentinel.leaderboard import make_entry, record_entry, render_leaderboard


def _verdicts(n_pass: int, n_crit: int) -> list[Verdict]:
    vs = [
        Verdict(scenario_id=f"p{i}", passed=True, severity="none", reason="ok")
        for i in range(n_pass)
    ]
    vs += [
        Verdict(
            scenario_id=f"f{i}",
            passed=False,
            severity="critical",
            reason="bad",
            failing_step=0,
        )
        for i in range(n_crit)
    ]
    return vs


def test_make_entry_computes_score_and_counts():
    e = make_entry("claims", "v1", "claude", _verdicts(3, 1))
    assert e.passed == 3
    assert e.failed == 1
    assert e.score == 75
    assert e.agent == "claims"
    assert e.revision == "v1"
    assert e.timestamp


def test_record_entry_persists_and_appends(tmp_path):
    path = tmp_path / "lb.json"
    record_entry(make_entry("claims", "v1", "claude", _verdicts(0, 3)), path)
    entries = record_entry(make_entry("claims", "v2", "claude", _verdicts(3, 0)), path)
    assert len(entries) == 2
    assert len(json.loads(path.read_text())) == 2


def test_render_ranks_by_score_desc_with_top_marked():
    e_low = make_entry("claims", "v1", "claude", _verdicts(0, 3))   # score 0
    e_high = make_entry("claims", "v2", "claude", _verdicts(3, 0))  # score 100
    md = render_leaderboard([e_low, e_high])
    assert md.index("v2") < md.index("v1")
    assert "🥇" in md
    assert "100" in md
