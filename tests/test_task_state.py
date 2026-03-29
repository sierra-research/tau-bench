# Copyright Sierra
# Unit tests for TaskState (Phase 3 orchestration).

import pytest
from tau_bench.types import Task
from tau_bench.orchestration.task_state import (
    TaskState,
    IntentState,
    IdentityState,
    ChecklistState,
    create_initial_task_state,
)


def test_task_state_initialization():
    """TaskState is created with domain and safe defaults."""
    task = Task(user_id="u1", actions=[], instruction="Book a flight", outputs=[])
    state = create_initial_task_state(domain="airline", task=task, initial_observation="Hi")
    assert state.domain == "airline"
    assert state.intent.initial_instruction == "Book a flight"
    assert state.intent.status == "in_progress"
    assert state.identity.user_id is None
    assert state.identity.authenticated is False
    assert state.identity.profile_grounded is False
    assert state.checklist.required_prerequisites == []
    assert state.last_tool_result is None
    assert state.last_error is None


def test_task_state_initialization_retail():
    """TaskState for retail has domain retail and same safe defaults."""
    task = Task(user_id="u2", actions=[], instruction="Return my order", outputs=[])
    state = create_initial_task_state(domain="retail", task=task)
    assert state.domain == "retail"
    assert state.identity.authenticated is False
    assert state.identity.profile_grounded is False


def test_domain_substate_airline():
    """Airline domain_state has expected placeholder keys."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)
    assert "reservation_id" in state.domain_state
    assert "booking_flow_stage" in state.domain_state
    assert "payment_methods_from_profile" in state.domain_state
    assert "selected_itinerary" in state.domain_state
    assert state.domain_state["payment_methods_from_profile"] == []


def test_domain_substate_retail():
    """Retail domain_state has expected placeholder keys."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="retail", task=task)
    assert "order_id" in state.domain_state
    assert "auth_method_used" in state.domain_state
    assert "user_id_from_lookup" in state.domain_state


def test_safe_defaults():
    """No assumption of authenticated, profile_grounded, or confirmation."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)
    assert state.identity.authenticated is False
    assert state.identity.profile_grounded is False
    assert state.identity.user_id is None
    assert len(state.confirmations) == 0
    assert state.checklist.completed_milestones == []


def test_update_helpers():
    """set_user_id, add_grounded, set_last_error, update_after_step update state."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)

    state.set_user_id("user_123")
    assert state.identity.user_id == "user_123"

    state.set_authenticated(method="email")
    assert state.identity.authenticated is True
    assert state.identity.auth_method == "email"

    state.add_grounded("payment_methods", ["cert_1", "cc_2"])
    assert state.grounded["payment_methods"] == ["cert_1", "cc_2"]

    state.set_last_error("Validation failed: unknown tool")
    assert state.last_error == "Validation failed: unknown tool"

    state.update_after_step("get_user_details", '{"name": "Mia"}')
    assert state.last_tool_result == '{"name": "Mia"}'
    assert state.last_error is None

    state.update_after_step("book_reservation", "Error: payment method not found")
    assert state.last_error == "Error: payment method not found"

    state.add_confirmation("booking_confirmed")
    assert "booking_confirmed" in state.confirmations

    state.checklist.required_prerequisites = ["get_user_id", "get_confirmation"]
    state.mark_prerequisite_done("get_user_id")
    assert "get_user_id" in state.checklist.completed_milestones
    assert state.checklist.required_prerequisites == ["get_confirmation"]


def test_checklist_structure():
    """Checklist has required_prerequisites, completed_milestones, pending, version."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)
    assert hasattr(state.checklist, "required_prerequisites")
    assert hasattr(state.checklist, "completed_milestones")
    assert hasattr(state.checklist, "pending")
    assert hasattr(state.checklist, "next_step_candidates")
    assert hasattr(state.checklist, "version")
    assert state.checklist.version == 0


def test_run_loop_creates_task_state():
    """run_orchestrated_loop creates TaskState and runs without error; domain must be passed explicitly."""
    from unittest.mock import MagicMock, patch
    from tau_bench.orchestration.run_loop import run_orchestrated_loop
    from tau_bench.types import SolveResult, Action, RESPOND_ACTION_NAME

    created_states = []

    def capture_create(domain, task, initial_observation=None):
        state = create_initial_task_state(domain=domain, task=task, initial_observation=initial_observation)
        created_states.append(state)
        return state

    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="Book flight", outputs=[])
    mock_env.tools_map = {}
    mock_env.tools_info = []
    mock_env.reset.return_value = MagicMock(observation="I want to book a flight", info=MagicMock(model_dump=lambda: {}))
    mock_env.step.return_value = MagicMock(
        observation="###STOP###",
        reward=1.0,
        done=True,
        info=MagicMock(model_dump=lambda: {}),
    )

    class OneStepProposer:
        def generate_next_step(self, messages):
            return (
                {"role": "assistant", "content": "Here is your confirmation. ###STOP###"},
                Action(name=RESPOND_ACTION_NAME, kwargs={"content": "Here is your confirmation. ###STOP###"}),
                0.0,
            )

    mock_logger = MagicMock()

    with patch("tau_bench.orchestration.run_loop.create_initial_task_state", side_effect=capture_create):
        result = run_orchestrated_loop(
            env=mock_env,
            proposer=OneStepProposer(),
            run_logger=mock_logger,
            task_index=0,
            max_num_steps=5,
            domain="retail",
        )

    assert isinstance(result, SolveResult)
    assert result.reward == 1.0
    assert len(created_states) == 1
    assert created_states[0].domain == "retail"


def test_run_loop_requires_domain_raises():
    """run_orchestrated_loop raises ValueError when domain is None (no default)."""
    from unittest.mock import MagicMock
    from tau_bench.orchestration.run_loop import run_orchestrated_loop

    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    mock_env.tools_map = {}
    mock_env.tools_info = []
    mock_env.reset.return_value = MagicMock(observation="Hi", info=MagicMock(model_dump=lambda: {}))
    mock_logger = MagicMock()

    with pytest.raises(ValueError, match="domain is required"):
        run_orchestrated_loop(
            env=mock_env,
            proposer=MagicMock(),
            run_logger=mock_logger,
            task_index=0,
            max_num_steps=1,
            domain=None,
        )
