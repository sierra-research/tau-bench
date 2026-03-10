# Copyright Sierra
# Unit tests for recovery module: confirmation heuristic, decide_recovery paths, retry/budget.

import pytest
from unittest.mock import MagicMock

from tau_bench.types import Action
from tau_bench.orchestration.task_state import create_initial_task_state
from tau_bench.orchestration.validator import ValidatorResult
from tau_bench.orchestration.policy_guard import PolicyGuardResult, CODE_MISSING_CONFIRMATION, CODE_MISSING_USER_ID
from tau_bench.orchestration.recovery import (
    check_confirmation_heuristic,
    action_retry_key,
    RecoveryState,
    RecoveryInput,
    RecoveryDecision,
    decide_recovery,
    FAILURE_VALIDATION_ERROR,
    FAILURE_POLICY_BLOCK,
    FAILURE_NO_PROGRESS,
    FAILURE_TOOL_EXECUTION_ERROR,
    FAILURE_REPEATED_SAME_ACTION,
    FAILURE_BUDGET_RISK,
    STRATEGY_ASK_USER_CONFIRMATION,
    STRATEGY_REPLAN_FROM_STATE,
    STRATEGY_SAFE_TERMINATE,
)


# --- Confirmation heuristic ---


def test_confirmation_heuristic_affirmative_returns_true():
    """Affirmative phrases (yes, confirm, ok, etc.) satisfy the heuristic."""
    assert check_confirmation_heuristic("yes", "booking_confirmed") is True
    assert check_confirmation_heuristic("Yes please", "booking_confirmed") is True
    assert check_confirmation_heuristic("I confirm", "booking_confirmed") is True
    assert check_confirmation_heuristic("go ahead", "booking_confirmed") is True
    assert check_confirmation_heuristic("ok", "booking_confirmed") is True
    assert check_confirmation_heuristic("sure", "booking_confirmed") is True
    assert check_confirmation_heuristic("please do", "booking_confirmed") is True


def test_confirmation_heuristic_negative_returns_false():
    """Strong negative phrases must not satisfy the heuristic."""
    assert check_confirmation_heuristic("no", "booking_confirmed") is False
    assert check_confirmation_heuristic("don't do it", "booking_confirmed") is False
    assert check_confirmation_heuristic("cancel", "booking_confirmed") is False
    assert check_confirmation_heuristic("wait", "booking_confirmed") is False
    assert check_confirmation_heuristic("never mind", "booking_confirmed") is False


def test_confirmation_heuristic_empty_or_non_string_returns_false():
    """Empty content or non-string does not confirm."""
    assert check_confirmation_heuristic("", "booking_confirmed") is False
    assert check_confirmation_heuristic("   ", "booking_confirmed") is False
    assert check_confirmation_heuristic(None, "booking_confirmed") is False  # type: ignore


def test_confirmation_heuristic_grounded_facts_message_does_not_confirm():
    """Grounded facts injection message must not be treated as user confirmation."""
    assert check_confirmation_heuristic("Grounded facts: user_id=u1; profile_grounded=True", "booking_confirmed") is False


# --- action_retry_key ---


def test_action_retry_key_same_action_same_kwargs_same_key():
    """Same action name and kwargs produce the same retry key."""
    a1 = Action(name="book_reservation", kwargs={"user_id": "u1", "origin": "JFK"})
    a2 = Action(name="book_reservation", kwargs={"origin": "JFK", "user_id": "u1"})
    assert action_retry_key(a1) == action_retry_key(a2)


def test_action_retry_key_different_kwargs_different_key():
    """Different kwargs produce different retry keys."""
    a1 = Action(name="book_reservation", kwargs={"user_id": "u1"})
    a2 = Action(name="book_reservation", kwargs={"user_id": "u2"})
    assert action_retry_key(a1) != action_retry_key(a2)


# --- decide_recovery: validation error ---


def test_decide_recovery_validation_error_returns_replan():
    """Validation failure yields REPLAN_FROM_STATE with hint."""
    inp = RecoveryInput(
        failure_type=FAILURE_VALIDATION_ERROR,
        action=Action(name="get_user_details", kwargs={}),
        step_index=1,
        validator_result=ValidatorResult(allowed=False, code="schema_mismatch", message="missing required argument: user_id"),
        recovery_state=RecoveryState(),
    )
    d = decide_recovery(inp, domain="airline")
    assert d.proposed_strategy == STRATEGY_REPLAN_FROM_STATE
    assert d.failure_type == FAILURE_VALIDATION_ERROR
    assert "user_id" in (d.replanning_hint or "")


# --- decide_recovery: policy block missing_confirmation -> ASK_USER_CONFIRMATION ---


def test_decide_recovery_missing_confirmation_returns_ask_user_confirmation():
    """Policy block with missing_confirmation for book_reservation yields ASK_USER_CONFIRMATION and state_updates."""
    action = Action(name="book_reservation", kwargs={"user_id": "u1"})
    inp = RecoveryInput(
        failure_type=FAILURE_POLICY_BLOCK,
        action=action,
        step_index=1,
        policy_result=PolicyGuardResult(
            allowed=False,
            code=CODE_MISSING_CONFIRMATION,
            message="explicit user confirmation required",
            missing_prerequisites=["booking_confirmed"],
        ),
        recovery_state=RecoveryState(),
    )
    d = decide_recovery(inp, domain="airline")
    assert d.proposed_strategy == STRATEGY_ASK_USER_CONFIRMATION
    assert d.state_updates.get("set_pending_side_effect_action") is action
    assert d.state_updates.get("pending_confirmation_key") == "booking_confirmed"


def test_decide_recovery_policy_block_missing_user_id_returns_replan():
    """Policy block with missing_user_id (not confirmation) yields REPLAN."""
    inp = RecoveryInput(
        failure_type=FAILURE_POLICY_BLOCK,
        action=Action(name="book_reservation", kwargs={"user_id": "u1"}),
        step_index=1,
        policy_result=PolicyGuardResult(
            allowed=False,
            code=CODE_MISSING_USER_ID,
            message="user_id must be established",
            missing_prerequisites=["user_id"],
        ),
        recovery_state=RecoveryState(),
    )
    d = decide_recovery(inp, domain="airline")
    assert d.proposed_strategy == STRATEGY_REPLAN_FROM_STATE


# --- decide_recovery: repeated same action while pending (no burn) ---


def test_decide_recovery_repeated_same_action_while_pending_returns_replan():
    """When pending_side_effect_action is set and same action is proposed again, return REPLAN without burning retry budget."""
    pending_action = Action(name="book_reservation", kwargs={"user_id": "u1"})
    recovery_state = RecoveryState(
        pending_side_effect_action=pending_action,
        pending_confirmation_key="booking_confirmed",
    )
    inp = RecoveryInput(
        failure_type=FAILURE_POLICY_BLOCK,
        action=pending_action,
        step_index=2,
        policy_result=PolicyGuardResult(
            allowed=False,
            code=CODE_MISSING_CONFIRMATION,
            message="confirmation required",
            missing_prerequisites=["booking_confirmed"],
        ),
        recovery_state=recovery_state,
    )
    d = decide_recovery(inp, domain="airline")
    assert d.proposed_strategy == STRATEGY_REPLAN_FROM_STATE
    assert d.failure_type == FAILURE_REPEATED_SAME_ACTION


# --- decide_recovery: retry budget ---


def test_decide_recovery_max_retries_per_action_returns_safe_terminate():
    """When retry_counts for this action exceed max_retries_per_action, return SAFE_TERMINATE."""
    action = Action(name="get_user_details", kwargs={"user_id": "u1"})
    key = action_retry_key(action)
    recovery_state = RecoveryState(retry_counts={key: 3})
    inp = RecoveryInput(
        failure_type=FAILURE_VALIDATION_ERROR,
        action=action,
        step_index=2,
        validator_result=ValidatorResult(allowed=False, code="schema_mismatch", message="missing key"),
        recovery_state=recovery_state,
    )
    d = decide_recovery(inp, domain="airline", max_retries_per_action=2)
    assert d.proposed_strategy == STRATEGY_SAFE_TERMINATE
    assert d.terminal_reason == "max_retries_per_action"


def test_decide_recovery_budget_exhausted_returns_safe_terminate():
    """When recovery_count_this_run >= max_recovery_per_run, return SAFE_TERMINATE."""
    recovery_state = RecoveryState(recovery_count_this_run=10)
    inp = RecoveryInput(
        failure_type=FAILURE_VALIDATION_ERROR,
        action=Action(name="x", kwargs={}),
        step_index=5,
        validator_result=ValidatorResult(allowed=False, code="tool_not_found", message="unknown"),
        recovery_state=recovery_state,
    )
    d = decide_recovery(inp, domain="airline", max_recovery_per_run=10)
    assert d.proposed_strategy == STRATEGY_SAFE_TERMINATE
    assert d.terminal_reason == "max_recovery_per_run"


# --- decide_recovery: no_progress ---


def test_decide_recovery_no_progress_same_action_three_times_returns_replan():
    """When last 3 actions are the same as current, return REPLAN (no_progress)."""
    inp = RecoveryInput(
        failure_type=FAILURE_VALIDATION_ERROR,
        action=Action(name="book_reservation", kwargs={"user_id": "u1"}),
        step_index=4,
        validator_result=ValidatorResult(allowed=False, code="schema_mismatch", message="err"),
        recovery_state=RecoveryState(),
        recent_action_names=["book_reservation", "book_reservation", "book_reservation"],
    )
    d = decide_recovery(inp, domain="airline")
    assert d.proposed_strategy == STRATEGY_REPLAN_FROM_STATE
    assert d.failure_type == FAILURE_NO_PROGRESS


# --- decide_recovery: tool execution error ---


def test_decide_recovery_tool_execution_error_returns_replan():
    """Tool execution error (observation starts with Error:) yields REPLAN with hint."""
    inp = RecoveryInput(
        failure_type=FAILURE_TOOL_EXECUTION_ERROR,
        action=Action(name="get_user_details", kwargs={"user_id": "unknown"}),
        step_index=1,
        observation="Error: user not found",
        recovery_state=RecoveryState(),
    )
    d = decide_recovery(inp, domain="airline")
    assert d.proposed_strategy == STRATEGY_REPLAN_FROM_STATE
    assert d.failure_type == FAILURE_TOOL_EXECUTION_ERROR
    assert d.replanning_hint is not None


# --- RecoveryState / RecoveryDecision ---


def test_recovery_state_defaults():
    """RecoveryState has expected defaults for pending and counters."""
    s = RecoveryState()
    assert s.pending_side_effect_action is None
    assert s.pending_confirmation_key is None
    assert s.retry_counts == {}
    assert s.recovery_count_this_run == 0
    assert s.retry_key_just_confirmed is None


def test_recovery_decision_has_required_fields():
    """RecoveryDecision is frozen and has strategy, terminal_reason, state_updates."""
    d = RecoveryDecision(
        failure_type=FAILURE_POLICY_BLOCK,
        diagnosis="blocked",
        confidence=1.0,
        recoverable=True,
        proposed_strategy=STRATEGY_ASK_USER_CONFIRMATION,
        state_updates={"set_pending_side_effect_action": None},
        retry_key="book_reservation|{}",
        trace_metadata={},
    )
    assert d.proposed_strategy == STRATEGY_ASK_USER_CONFIRMATION
    assert "set_pending_side_effect_action" in d.state_updates
