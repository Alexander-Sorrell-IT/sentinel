"""Tests for the hook-based pre-action interceptor (ground truth)."""
from sentinel.contracts import Action, PolicyContract
from sentinel.interceptor import evaluate_action


def _policy() -> PolicyContract:
    return PolicyContract(
        allowed_tools=["lookup_claim"],
        approval_required_tools=["approve_claim"],
        forbidden_tools=["delete_claim"],
        sensitive_fields=["ssn"],
    )


def _action(tool: str) -> Action:
    return Action(tool=tool, args={}, requires_approval=False)


def test_forbidden_tool_blocked_critical():
    d = evaluate_action(_action("delete_claim"), _policy(), approved=False)
    assert d.allowed is False
    assert d.severity == "critical"


def test_approval_required_without_approval_blocked_critical():
    d = evaluate_action(_action("approve_claim"), _policy(), approved=False)
    assert d.allowed is False
    assert d.severity == "critical"


def test_approval_required_with_approval_allowed():
    d = evaluate_action(_action("approve_claim"), _policy(), approved=True)
    assert d.allowed is True
    assert d.severity == "none"


def test_out_of_scope_tool_blocked_high():
    d = evaluate_action(_action("wire_transfer"), _policy(), approved=False)
    assert d.allowed is False
    assert d.severity == "high"


def test_allowed_tool_permitted():
    d = evaluate_action(_action("lookup_claim"), _policy(), approved=False)
    assert d.allowed is True
    assert d.severity == "none"
