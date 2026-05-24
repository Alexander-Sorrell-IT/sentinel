"""Reliability Report builder: render verdicts as Markdown + a JSON-able dict."""
from __future__ import annotations

from jinja2 import Template

from sentinel.contracts import Verdict
from sentinel.score import reliability_score

_TEMPLATE = Template(
    """# Sentinel Reliability Report

{% if certified %}✅ **CERTIFIED** — all {{ total }} scenario(s) passed.
{% else %}❌ **FAILED** — {{ failed }} of {{ total }} scenario(s) did not hold.
{% endif %}
**Reliability score: {{ score }} / 100**

| Scenario | Result | Severity | Failing step | Reason |
|---|---|---|---|---|
{% for v in verdicts -%}
| {{ v.scenario_id }} | {{ "PASS" if v.passed else "FAIL" }} | {{ v.severity }} | {{ v.failing_step if v.failing_step is not none else "-" }} | {{ v.reason }} |
{% endfor %}
""",
    trim_blocks=True,
    lstrip_blocks=True,
)


def build_report(verdicts: list[Verdict]) -> tuple[str, dict]:
    """Return (markdown_report, json_dict) summarizing the verdicts."""
    total = len(verdicts)
    passed = sum(1 for v in verdicts if v.passed)
    failed = total - passed
    certified = total > 0 and failed == 0
    score = reliability_score(verdicts)

    data = {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "certified": certified,
            "score": score,
        },
        "results": [v.model_dump() for v in verdicts],
    }

    markdown = _TEMPLATE.render(
        verdicts=verdicts,
        total=total,
        passed=passed,
        failed=failed,
        certified=certified,
        score=score,
    )
    return markdown, data
