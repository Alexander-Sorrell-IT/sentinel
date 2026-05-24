"""Critical-finding notifiers: open a Jira issue and post a Slack alert.

Secrets are read from the environment and required — if any is missing we fail
loudly rather than silently skipping a notification.
"""
from __future__ import annotations

import os

import requests

from sentinel.contracts import Verdict

_TIMEOUT = 30


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value


def _adf(text: str) -> dict:
    """Wrap plain text in Atlassian Document Format (required by Jira Cloud v3)."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": text}]}
        ],
    }


def notify_critical(verdict: Verdict) -> dict:
    """Open a Jira issue and post a Slack alert for a failing verdict.

    Returns the two HTTP status codes. Raises if config is missing or either
    request fails.
    """
    jira_base = _require_env("JIRA_BASE_URL")
    jira_project = _require_env("JIRA_PROJECT_KEY")
    jira_email = _require_env("JIRA_EMAIL")
    jira_token = _require_env("JIRA_API_TOKEN")
    slack_webhook = _require_env("SLACK_WEBHOOK_URL")

    summary = f"[{verdict.severity.upper()}] Reliability failure: {verdict.scenario_id}"
    description = f"{verdict.reason} (failing step: {verdict.failing_step})"

    jira_resp = requests.post(
        f"{jira_base}/rest/api/3/issue",
        json={
            "fields": {
                "project": {"key": jira_project},
                "summary": summary,
                "description": _adf(description),
                "issuetype": {"name": "Bug"},
            }
        },
        auth=(jira_email, jira_token),
        timeout=_TIMEOUT,
    )
    jira_resp.raise_for_status()

    slack_resp = requests.post(
        slack_webhook,
        json={"text": f":rotating_light: {summary}\n{description}"},
        timeout=_TIMEOUT,
    )
    slack_resp.raise_for_status()

    return {"jira_status": jira_resp.status_code, "slack_status": slack_resp.status_code}
