"""Tests for the reliability-scenario generator."""
from sentinel.contracts import PolicyContract
from sentinel.scenarios import generate


def _policy() -> PolicyContract:
    return PolicyContract(
        allowed_tools=["lookup_claim"],
        approval_required_tools=["approve_claim"],
        forbidden_tools=["delete_claim"],
        sensitive_fields=["ssn"],
    )


def test_generates_at_least_one_per_category():
    scenarios = generate(_policy())
    cats = {s.category for s in scenarios}
    assert cats == {"hitl_bypass", "wait_state_skip", "tool_scope_violation"}
    assert len(scenarios) >= 3


def test_scenarios_reference_real_policy_tools():
    policy = _policy()
    known = (
        set(policy.allowed_tools)
        | set(policy.approval_required_tools)
        | set(policy.forbidden_tools)
    )
    for s in generate(policy):
        assert s.inputs["target_tool"] in known


def test_hitl_bypass_withholds_approval():
    hitl = [s for s in generate(_policy()) if s.category == "hitl_bypass"]
    assert hitl
    assert hitl[0].inputs["grant_approval"] is False
    assert hitl[0].inputs["target_tool"] == "approve_claim"


def test_scenario_ids_are_unique():
    ids = [s.id for s in generate(_policy())]
    assert len(ids) == len(set(ids))
