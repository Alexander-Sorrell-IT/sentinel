"""Core data contracts for the Sentinel reliability-testing engine.

All models forbid unknown fields (fail loud, no silent extra data).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class _Strict(BaseModel):
    """Base model that rejects unknown fields."""

    model_config = ConfigDict(extra="forbid")


class Action(_Strict):
    """A single tool call an agent attempts."""

    tool: str
    args: dict
    requires_approval: bool


class PolicyContract(_Strict):
    """The reliability policy an agent-under-test must obey."""

    allowed_tools: list[str]
    approval_required_tools: list[str]
    forbidden_tools: list[str]
    sensitive_fields: list[str]


ScenarioCategory = Literal["hitl_bypass", "wait_state_skip", "tool_scope_violation"]


class Scenario(_Strict):
    """A reliability test scenario to run against the agent-under-test."""

    id: str
    category: ScenarioCategory
    description: str
    inputs: dict


class TrajectoryStep(_Strict):
    """One step of an observed run: an attempted action and whether it was approved."""

    action: Action
    approved: bool


class Trajectory(_Strict):
    """The observed run of the agent-under-test for one scenario."""

    steps: list[TrajectoryStep]
    final_output: str


Severity = Literal["none", "high", "critical"]


class Verdict(_Strict):
    """The result of evaluating one scenario's trajectory."""

    scenario_id: str
    passed: bool
    severity: Severity
    reason: str
    failing_step: int | None = None
