# Copyright Sierra
# Unit tests for Policy Guard v1 (orchestration).

import pytest
from tau_bench.types import Action, RESPOND_ACTION_NAME, Task
from tau_bench.orchestration.policy_guard import (
    check_policy,
    PolicyGuardResult,
    get_tool_policy_metadata,
    get_tools_requiring_confirmation,
    CODE_ALLOWED,
    CODE_MISSING_USER_ID,
    CODE_NOT_AUTHENTICATED,
    CODE_MISSING_PROFILE_GROUNDING,
    CODE_MISSING_CONFIRMATION,
    CODE_MISSING_RESERVATION_CONTEXT,
    CODE_MISSING_ORDER_CONTEXT,
)
from tau_bench.orchestration.task_state import create_initial_task_state


class _MockEnv:
    """Minimal env for policy guard tests; guard only uses task_state, env is for API consistency."""
    def __init__(self):
        self.tools_map = {"book_reservation": None, "cancel_pending_order": None}
        self.tools_info = []


def _airline_state(**overrides):
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)
    for k, v in overrides.items():
        if k == "user_id":
            state.identity.user_id = v
        elif k == "profile_grounded":
            state.identity.profile_grounded = v
        elif k == "confirmations":
            state.confirmations = set(v) if isinstance(v, list) else v
        elif k == "reservation_ids":
            state.grounded["reservation_ids"] = list(v) if v else []
        elif k == "reservation_id":
            state.domain_state["reservation_id"] = v
    return state


def _retail_state(**overrides):
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="retail", task=task)
    for k, v in overrides.items():
        if k == "authenticated":
            state.identity.authenticated = v
        elif k == "user_id":
            state.identity.user_id = v
        elif k == "order_ids":
            state.grounded["order_ids"] = list(v) if v else []
        elif k == "order_id":
            state.domain_state["order_id"] = v
        elif k == "confirmations":
            state.confirmations = set(v) if isinstance(v, list) else v
    return state


def test_airline_booking_blocked_when_user_id_missing():
    """Airline book_reservation is blocked when identity.user_id is not set."""
    env = _MockEnv()
    state = _airline_state(user_id=None)
    action = Action(name="book_reservation", kwargs={"user_id": "sara_doe_496"})  # kwargs valid for validator
    r = check_policy(env, action, state)
    assert r.allowed is False
    assert r.code == CODE_MISSING_USER_ID
    assert "user_id" in r.message.lower() or "established" in r.message.lower()
    assert "user_id" in r.missing_prerequisites


def test_airline_booking_blocked_when_confirmation_missing():
    """Airline book_reservation is blocked when booking_confirmed is not in confirmations."""
    env = _MockEnv()
    state = _airline_state(user_id="sara_doe_496", profile_grounded=True, confirmations=[])
    action = Action(name="book_reservation", kwargs={"user_id": "sara_doe_496"})
    r = check_policy(env, action, state)
    assert r.allowed is False
    assert r.code == CODE_MISSING_CONFIRMATION
    assert "confirmation" in r.message.lower()
    assert "booking_confirmed" in r.missing_prerequisites


def test_airline_booking_blocked_when_profile_not_grounded():
    """Airline book_reservation is blocked when profile_grounded is False."""
    env = _MockEnv()
    state = _airline_state(user_id="sara_doe_496", profile_grounded=False)
    state.add_confirmation("booking_confirmed")
    action = Action(name="book_reservation", kwargs={"user_id": "sara_doe_496"})
    r = check_policy(env, action, state)
    assert r.allowed is False
    assert r.code == CODE_MISSING_PROFILE_GROUNDING


def test_retail_mutating_action_blocked_when_not_authenticated():
    """Retail cancel_pending_order is blocked when identity.authenticated is False."""
    env = _MockEnv()
    state = _retail_state(authenticated=False)
    action = Action(name="cancel_pending_order", kwargs={"order_id": "#W123", "reason": "no longer needed"})
    r = check_policy(env, action, state)
    assert r.allowed is False
    assert r.code == CODE_NOT_AUTHENTICATED
    assert "authenticated" in r.message.lower() or "authenticate" in r.message.lower()
    assert "authenticated" in r.missing_prerequisites


def test_airline_booking_allowed_when_prerequisites_satisfied():
    """Airline book_reservation is allowed when user_id, profile_grounded, and booking_confirmed are set."""
    env = _MockEnv()
    state = _airline_state(user_id="sara_doe_496", profile_grounded=True, confirmations=["booking_confirmed"])
    action = Action(name="book_reservation", kwargs={"user_id": "sara_doe_496"})
    r = check_policy(env, action, state)
    assert r.allowed is True
    assert r.code == CODE_ALLOWED
    assert r.missing_prerequisites == []


def test_retail_cancel_order_blocked_when_order_context_missing():
    """Retail cancel_pending_order is blocked when order_id is not established."""
    env = _MockEnv()
    state = _retail_state(authenticated=True, user_id="mei_kovacs_8020")  # no order_ids
    action = Action(name="cancel_pending_order", kwargs={"order_id": "#W123", "reason": "no longer needed"})
    r = check_policy(env, action, state)
    assert r.allowed is False
    assert r.code == CODE_MISSING_ORDER_CONTEXT
    assert "order" in r.message.lower()
    assert "order_context" in r.missing_prerequisites


def test_retail_cancel_order_blocked_when_confirmation_missing():
    """Retail cancel_pending_order is blocked when explicit confirmation not given."""
    env = _MockEnv()
    state = _retail_state(
        authenticated=True,
        user_id="mei_kovacs_8020",
        order_ids=["#W123"],
        confirmations=[],
    )
    action = Action(name="cancel_pending_order", kwargs={"order_id": "#W123", "reason": "no longer needed"})
    r = check_policy(env, action, state)
    assert r.allowed is False
    assert r.code == CODE_MISSING_CONFIRMATION
    assert "cancel_order_confirmed" in r.missing_prerequisites


def test_retail_mutating_action_allowed_when_authenticated():
    """Retail cancel_pending_order is allowed when authenticated, order context, and confirmation are present."""
    env = _MockEnv()
    state = _retail_state(
        authenticated=True,
        user_id="mei_kovacs_8020",
        order_ids=["#W123"],
        confirmations=["cancel_order_confirmed"],
    )
    action = Action(name="cancel_pending_order", kwargs={"order_id": "#W123", "reason": "no longer needed"})
    r = check_policy(env, action, state)
    assert r.allowed is True
    assert r.code == CODE_ALLOWED


def test_airline_cancel_reservation_blocked_when_reservation_context_missing():
    """Airline cancel_reservation is blocked when reservation_id is not established."""
    env = _MockEnv()
    state = _airline_state(user_id="sara_doe_496")  # no reservation_ids or reservation_id
    action = Action(name="cancel_reservation", kwargs={"user_id": "sara_doe_496", "reservation_id": "R1", "reason": "change of plan"})
    r = check_policy(env, action, state)
    assert r.allowed is False
    assert r.code == CODE_MISSING_RESERVATION_CONTEXT
    assert "reservation" in r.message.lower()
    assert "reservation_context" in r.missing_prerequisites


def test_airline_cancel_reservation_allowed_when_reservation_context_present():
    """Airline cancel_reservation is allowed when user_id and reservation context are established."""
    env = _MockEnv()
    state = _airline_state(user_id="sara_doe_496", reservation_ids=["R1"])
    action = Action(name="cancel_reservation", kwargs={"user_id": "sara_doe_496", "reservation_id": "R1", "reason": "change of plan"})
    r = check_policy(env, action, state)
    assert r.allowed is True
    assert r.code == CODE_ALLOWED


def test_airline_update_reservation_flights_blocked_when_reservation_context_missing():
    """Airline update_reservation_flights is blocked when reservation context is missing (before confirmation)."""
    env = _MockEnv()
    state = _airline_state(user_id="sara_doe_496")  # no reservation context
    action = Action(name="update_reservation_flights", kwargs={"user_id": "sara_doe_496", "reservation_id": "R1"})
    r = check_policy(env, action, state)
    assert r.allowed is False
    assert r.code == CODE_MISSING_RESERVATION_CONTEXT


def test_respond_always_allowed():
    """Respond action is always allowed by policy guard."""
    env = _MockEnv()
    state = _airline_state()
    action = Action(name=RESPOND_ACTION_NAME, kwargs={"content": "Here is the answer."})
    r = check_policy(env, action, state)
    assert r.allowed is True
    assert r.code == CODE_ALLOWED


def test_airline_readonly_tool_allowed_without_user_id():
    """Airline read-only tools (e.g. get_user_details) are allowed without user_id in state."""
    env = _MockEnv()
    env.tools_map["get_user_details"] = None
    state = _airline_state(user_id=None)
    action = Action(name="get_user_details", kwargs={"user_id": "sara_doe_496"})
    r = check_policy(env, action, state)
    assert r.allowed is True


def test_policy_guard_result_to_dict():
    """PolicyGuardResult.to_dict returns expected keys."""
    r = PolicyGuardResult(
        allowed=False,
        code=CODE_MISSING_USER_ID,
        message="user_id required",
        missing_prerequisites=["user_id"],
    )
    d = r.to_dict()
    assert d["allowed"] is False
    assert d["code"] == CODE_MISSING_USER_ID
    assert "user_id" in d["message"]
    assert d["missing_prerequisites"] == ["user_id"]


def test_get_tool_policy_metadata_returns_metadata_for_guarded_tools():
    """Policy metadata is looked up by (domain, tool_name); airline mutating tools have distinct confirmation keys."""
    meta = get_tool_policy_metadata("airline", "book_reservation")
    assert meta.get("requires_user_id") is True
    assert meta.get("requires_profile_grounded") is True
    assert meta.get("requires_confirmation_key") == "booking_confirmed"

    assert get_tool_policy_metadata("airline", "update_reservation_flights").get("requires_confirmation_key") == "flights_update_confirmed"
    assert get_tool_policy_metadata("airline", "update_reservation_baggages").get("requires_confirmation_key") == "baggage_update_confirmed"
    assert get_tool_policy_metadata("airline", "update_reservation_passengers").get("requires_confirmation_key") == "passengers_update_confirmed"

    assert get_tool_policy_metadata("airline", "cancel_reservation").get("requires_reservation_context") is True
    assert get_tool_policy_metadata("airline", "update_reservation_flights").get("requires_reservation_context") is True

    meta_retail = get_tool_policy_metadata("retail", "cancel_pending_order")
    assert meta_retail.get("requires_authenticated") is True
    assert meta_retail.get("requires_order_context") is True
    assert meta_retail.get("requires_confirmation_key") == "cancel_order_confirmed"

    meta_user_addr = get_tool_policy_metadata("retail", "modify_user_address")
    assert meta_user_addr.get("requires_authenticated") is True
    assert meta_user_addr.get("requires_confirmation_key") == "user_address_modify_confirmed"
    assert meta_user_addr.get("requires_order_context") is None or meta_user_addr.get("requires_order_context") is False


def test_get_tool_policy_metadata_empty_for_unknown_or_readonly():
    """Unknown tool or read-only tool returns empty dict (no guard requirements)."""
    assert get_tool_policy_metadata("airline", "get_user_details") == {}
    assert get_tool_policy_metadata("other_domain", "book_reservation") == {}


def test_get_tools_requiring_confirmation_derived_from_metadata():
    """Tools requiring confirmation are derived from POLICY_METADATA, not hard-coded list."""
    airline = get_tools_requiring_confirmation("airline")
    assert "book_reservation" in airline
    assert "update_reservation_flights" in airline
    assert "update_reservation_baggages" in airline
    assert "update_reservation_passengers" in airline
    assert "cancel_reservation" not in airline

    retail = get_tools_requiring_confirmation("retail")
    assert "cancel_pending_order" in retail
    assert "modify_pending_order_address" in retail
    assert "return_delivered_order_items" in retail
    assert "exchange_delivered_order_items" in retail
    assert "modify_user_address" in retail


def test_check_policy_allow_block_follows_metadata_not_tool_name_branch():
    """check_policy allow/block is driven by get_tool_policy_metadata; metadata fields control behavior."""
    env = _MockEnv()
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="retail", task=task)
    state.identity.authenticated = False
    state.identity.user_id = "u1"
    state.grounded["order_ids"] = ["#W1"]
    state.confirmations = {"cancel_order_confirmed"}
    action = Action(name="cancel_pending_order", kwargs={"order_id": "#W1", "reason": "no longer needed"})
    r = check_policy(env, action, state)
    assert r.allowed is False
    assert r.code == CODE_NOT_AUTHENTICATED
    meta = get_tool_policy_metadata("retail", "cancel_pending_order")
    assert meta.get("requires_authenticated") is True
    state.identity.authenticated = True
    r2 = check_policy(env, action, state)
    assert r2.allowed is True
    assert r2.code == CODE_ALLOWED


def test_check_policy_tool_not_in_metadata_allowed():
    """Tool not in POLICY_METADATA is allowed regardless of state (check_policy uses metadata lookup)."""
    env = _MockEnv()
    env.tools_map["list_all_airports"] = None
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)
    state.identity.user_id = None
    action = Action(name="list_all_airports", kwargs={})
    assert get_tool_policy_metadata("airline", "list_all_airports") == {}
    r = check_policy(env, action, state)
    assert r.allowed is True


def test_run_loop_policy_guard_blocks_before_executor():
    """When policy guard blocks, executor (env.step) is not called and task_state.last_error is set."""
    from unittest.mock import MagicMock, patch
    from tau_bench.orchestration.run_loop import run_orchestrated_loop
    from tau_bench.orchestration.task_state import create_initial_task_state

    created_states = []

    def capture_create(domain, task, initial_observation=None):
        state = create_initial_task_state(domain=domain, task=task, initial_observation=initial_observation)
        created_states.append(state)
        return state

    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="Book flight", outputs=[])
    mock_env.tools_map = {"book_reservation": None}
    mock_env.tools_info = [
        {
            "type": "function",
            "function": {
                "name": "book_reservation",
                "parameters": {
                    "type": "object",
                    "properties": {"user_id": {"type": "string"}},
                    "required": ["user_id"],
                },
            },
        },
    ]
    mock_env.reset.return_value = MagicMock(observation="I want to book a flight", info=MagicMock(model_dump=lambda: {}))

    class ProposeBookReservationProposer:
        """Proposes book_reservation (passes validator) but state has no user_id -> policy guard blocks."""
        def generate_next_step(self, messages):
            return (
                {
                    "role": "assistant",
                    "tool_calls": [
                        {"id": "tc_1", "function": {"name": "book_reservation", "arguments": "{\"user_id\":\"sara_doe_496\"}"}},
                    ],
                },
                Action(name="book_reservation", kwargs={"user_id": "sara_doe_496"}),
                0.0,
            )

    mock_logger = MagicMock()

    with patch("tau_bench.orchestration.run_loop.create_initial_task_state", side_effect=capture_create):
        run_orchestrated_loop(
            env=mock_env,
            proposer=ProposeBookReservationProposer(),
            run_logger=mock_logger,
            task_index=0,
            max_num_steps=2,
            domain="airline",
        )

    assert len(created_states) == 1
    task_state = created_states[0]
    assert task_state.last_error is not None
    assert "Policy blocked" in task_state.last_error
    assert "missing_user_id" in task_state.last_error
    mock_env.step.assert_not_called()
