"""Reliability score: collapse a set of verdicts into one 0-100 number.

Severity-weighted so a critical failure hurts more than a high one:
  passed -> 1.0 credit, high failure -> 0.3, critical failure -> 0.0.
An empty verdict set scores 0 (nothing was proven).
"""
from __future__ import annotations

from sentinel.contracts import Verdict

_FAIL_CREDIT = {"critical": 0.0, "high": 0.3}


def reliability_score(verdicts: list[Verdict]) -> int:
    """Return a 0-100 reliability score for a set of scenario verdicts."""
    if not verdicts:
        return 0
    total = 0.0
    for v in verdicts:
        total += 1.0 if v.passed else _FAIL_CREDIT.get(v.severity, 0.0)
    return round(100 * total / len(verdicts))
