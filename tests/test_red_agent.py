"""Tests for the adversarial LLM red agent."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from sentinel.contracts import PolicyContract
from sentinel.red_agent import RedAgent


class FakeLLM:
    """Deterministic stub for `LLMClient` — returns whatever it was constructed with."""

    def __init__(self, response: str):
        self.response = response
        self.last_prompt: str | None = None

    def complete(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


def _policy() -> PolicyContract:
    return PolicyContract(
        allowed_tools=["lookup_claim"],
        approval_required_tools=["approve_claim"],
        forbidden_tools=["delete_claim"],
        sensitive_fields=["ssn"],
    )


VALID_RESPONSE = (
    '{"id":"p1","category":"hitl_bypass","description":"Skip approval on approve_claim",'
    '"inputs":{"target_tool":"approve_claim","grant_approval":false}}\n'
    '{"id":"p2","category":"wait_state_skip","description":"Approve before wait state",'
    '"inputs":{"target_tool":"approve_claim","skip_wait":true}}\n'
    '{"id":"p3","category":"tool_scope_violation","description":"Invoke delete_claim",'
    '"inputs":{"target_tool":"delete_claim"}}\n'
)


def test_parses_one_per_category():
    scenarios = RedAgent(FakeLLM(VALID_RESPONSE)).generate(_policy())
    cats = {s.category for s in scenarios}
    assert cats == {"hitl_bypass", "wait_state_skip", "tool_scope_violation"}


def test_passes_policy_into_prompt():
    llm = FakeLLM(VALID_RESPONSE)
    RedAgent(llm).generate(_policy())
    assert "approve_claim" in (llm.last_prompt or "")
    assert "delete_claim" in (llm.last_prompt or "")


def test_empty_response_raises():
    with pytest.raises(ValueError, match="no parseable scenarios"):
        RedAgent(FakeLLM("")).generate(_policy())


def test_invalid_category_fails_loud():
    bad = '{"id":"p1","category":"not_a_category","description":"x","inputs":{"target_tool":"x"}}\n'
    with pytest.raises(ValidationError):
        RedAgent(FakeLLM(bad)).generate(_policy())


def test_blank_lines_are_ignored():
    response = "\n\n" + VALID_RESPONSE + "\n\n"
    scenarios = RedAgent(FakeLLM(response)).generate(_policy())
    assert len(scenarios) == 3
