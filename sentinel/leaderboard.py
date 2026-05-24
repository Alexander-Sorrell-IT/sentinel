"""Reliability leaderboard: score each agent revision and rank them.

Each test run becomes an Entry (agent + revision + model + score). Entries are
appended to a JSON history file and rendered as a ranked markdown board, so a
team can watch a revision climb from FAILED to CERTIFIED across the loop.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from sentinel.contracts import Verdict
from sentinel.score import reliability_score


class Entry(BaseModel):
    """One leaderboard entry: a scored agent revision."""

    model_config = ConfigDict(extra="forbid")

    agent: str
    revision: str
    model: str
    score: int
    passed: int
    failed: int
    timestamp: str


def make_entry(
    agent: str,
    revision: str,
    model: str,
    verdicts: list[Verdict],
    *,
    now: datetime | None = None,
) -> Entry:
    """Build a leaderboard entry from a run's verdicts."""
    passed = sum(1 for v in verdicts if v.passed)
    moment = now or datetime.now(timezone.utc)
    return Entry(
        agent=agent,
        revision=revision,
        model=model,
        score=reliability_score(verdicts),
        passed=passed,
        failed=len(verdicts) - passed,
        timestamp=moment.isoformat(),
    )


def record_entry(entry: Entry, path: str | Path) -> list[Entry]:
    """Append an entry to the JSON history file; return the full history."""
    path = Path(path)
    history = [Entry(**row) for row in json.loads(path.read_text())] if path.exists() else []
    history.append(entry)
    path.write_text(json.dumps([e.model_dump() for e in history], indent=2))
    return history


def _ranked(entries: list[Entry]) -> list[Entry]:
    # Highest score first; tie-break on fewer failures, then most recent.
    return sorted(entries, key=lambda e: (e.score, -e.failed, e.timestamp), reverse=True)


def render_leaderboard(entries: list[Entry]) -> str:
    """Render the entries as a ranked markdown leaderboard."""
    lines = [
        "# Sentinel Reliability Leaderboard",
        "",
        "| Rank | Agent | Revision | Model | Score | Pass/Fail |",
        "|---|---|---|---|---|---|",
    ]
    for i, e in enumerate(_ranked(entries), start=1):
        rank = "🥇" if i == 1 else str(i)
        lines.append(
            f"| {rank} | {e.agent} | {e.revision} | {e.model} | "
            f"{e.score} | {e.passed}/{e.passed + e.failed} |"
        )
    return "\n".join(lines) + "\n"
