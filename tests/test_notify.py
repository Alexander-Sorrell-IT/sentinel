"""Tests for the Jira + Slack critical notifiers (HTTP mocked)."""
import pytest

import sentinel.notify as notify
from sentinel.contracts import Verdict

_ENV = {
    "JIRA_BASE_URL": "https://example.atlassian.net",
    "JIRA_PROJECT_KEY": "REL",
    "JIRA_EMAIL": "a@b.c",
    "JIRA_API_TOKEN": "tok",
    "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/x",
}


class _FakeResp:
    def __init__(self, status: int = 200):
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


def _verdict() -> Verdict:
    return Verdict(
        scenario_id="hitl_bypass_0",
        passed=False,
        severity="critical",
        reason="skipped approval",
        failing_step=1,
    )


def _set_env(monkeypatch):
    for k, v in _ENV.items():
        monkeypatch.setenv(k, v)


def test_posts_jira_and_slack_with_severity_and_reason(monkeypatch):
    _set_env(monkeypatch)
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return _FakeResp(200)

    monkeypatch.setattr(notify.requests, "post", fake_post)
    result = notify.notify_critical(_verdict())

    assert len(calls) == 2
    jira_call = next(c for c in calls if "atlassian" in c[0])
    slack_call = next(c for c in calls if "slack" in c[0])

    # Jira Cloud v3 requires Atlassian Document Format (ADF) for description.
    jira_json = jira_call[1]["json"]
    assert jira_json["fields"]["project"]["key"] == "REL"
    assert "critical" in jira_json["fields"]["summary"].lower()
    description = jira_json["fields"]["description"]
    assert isinstance(description, dict)
    assert description["type"] == "doc"
    assert "skipped approval" in str(description)

    assert "skipped approval" in str(slack_call[1]["json"])
    assert result["jira_status"] == 200
    assert result["slack_status"] == 200


def test_missing_env_raises(monkeypatch):
    for k in _ENV:
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(RuntimeError):
        notify.notify_critical(_verdict())
