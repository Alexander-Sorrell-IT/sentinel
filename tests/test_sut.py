"""Tests for the claims agent-under-test trajectory model."""
from sentinel.contracts import Trajectory
from sut.claims_agent import run


def test_run_returns_trajectory():
    t = run({"target_tool": "approve_claim", "grant_approval": True})
    assert isinstance(t, Trajectory)
    assert t.steps


def test_hitl_bypass_produces_unapproved_approve_step():
    t = run({"target_tool": "approve_claim", "grant_approval": False})
    approve_steps = [s for s in t.steps if s.action.tool == "approve_claim"]
    assert approve_steps
    assert approve_steps[0].approved is False


def test_wait_state_skip_produces_unapproved_approve_step():
    t = run({"target_tool": "approve_claim", "skip_wait": True})
    approve = next(s for s in t.steps if s.action.tool == "approve_claim")
    assert approve.approved is False


def test_happy_path_approves_with_approval():
    t = run({"target_tool": "approve_claim", "grant_approval": True})
    approve = next(s for s in t.steps if s.action.tool == "approve_claim")
    assert approve.approved is True


def test_scope_violation_attempts_target_tool():
    t = run({"target_tool": "delete_claim"})
    assert any(s.action.tool == "delete_claim" for s in t.steps)
