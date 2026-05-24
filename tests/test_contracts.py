"""Tests for the core Sentinel data contracts."""
import pytest
from pydantic import ValidationError

from sentinel.contracts import (
    Action,
    PolicyContract,
    Scenario,
    Trajectory,
    TrajectoryStep,
    Verdict,
)


def _policy() -> PolicyContract:
    return PolicyContract(
        allowed_tools=["lookup_claim"],
        approval_required_tools=["approve_claim"],
        forbidden_tools=["delete_claim"],
        sensitive_fields=["ssn"],
    )


def test_action_valid():
    a = Action(tool="approve_claim", args={"id": 1}, requires_approval=True)
    assert a.tool == "approve_claim"
    assert a.requires_approval is True


def test_policy_contract_valid():
    p = _policy()
    assert "approve_claim" in p.approval_required_tools
    assert "delete_claim" in p.forbidden_tools


def test_policy_contract_rejects_unknown_field():
    with pytest.raises(ValidationError):
        PolicyContract(
            allowed_tools=[],
            approval_required_tools=[],
            forbidden_tools=[],
            sensitive_fields=[],
            bogus=123,
        )


def test_scenario_rejects_invalid_category():
    with pytest.raises(ValidationError):
        Scenario(id="s1", category="not_a_category", description="x", inputs={})


def test_scenario_valid_category():
    s = Scenario(id="s1", category="hitl_bypass", description="x", inputs={})
    assert s.category == "hitl_bypass"


def test_trajectory_and_steps():
    step = TrajectoryStep(
        action=Action(tool="approve_claim", args={}, requires_approval=True),
        approved=False,
    )
    traj = Trajectory(steps=[step], final_output="approved")
    assert traj.steps[0].approved is False
    assert traj.final_output == "approved"


def test_verdict_valid():
    v = Verdict(
        scenario_id="s1",
        passed=False,
        severity="critical",
        reason="skipped approval",
        failing_step=0,
    )
    assert v.passed is False
    assert v.severity == "critical"
    assert v.failing_step == 0


def test_verdict_failing_step_optional():
    v = Verdict(scenario_id="s1", passed=True, severity="none", reason="ok")
    assert v.failing_step is None
