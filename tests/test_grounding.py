# Copyright Sierra
# Unit tests for grounding layer: extractors, apply_grounding, run_loop integration.

import json
import pytest
from unittest.mock import MagicMock, patch

from tau_bench.types import Task, Action, RESPOND_ACTION_NAME
from tau_bench.orchestration.task_state import create_initial_task_state
from tau_bench.orchestration.grounding import (
    apply_grounding,
    build_grounded_facts_summary,
    USER_ID_LOOKUP_AUTH_METHOD,
)


# Sample airline get_user_details success (real IDs preserved)
AIRLINE_USER_PROFILE_JSON = json.dumps({
    "name": {"first_name": "Mia", "last_name": "Li"},
    "dob": "1990-04-05",
    "payment_methods": {
        "credit_card_4421486": {"source": "credit_card", "brand": "visa", "last_four": "7447", "id": "credit_card_4421486"},
        "certificate_4856383": {"source": "certificate", "amount": 100, "id": "certificate_4856383"},
    },
    "membership": "gold",
    "reservations": ["NO6JO3", "AIXC49"],
})

# Sample retail user profile with orders
RETAIL_USER_PROFILE_JSON = json.dumps({
    "name": {"first_name": "Noah", "last_name": "Brown"},
    "email": "noah@example.com",
    "payment_methods": {
        "paypal_5727330": {"source": "paypal", "id": "paypal_5727330"},
        "credit_card_7815826": {"source": "credit_card", "brand": "mastercard", "last_four": "9212", "id": "credit_card_7815826"},
    },
    "orders": ["#W7678072"],
})


def test_grounding_airline_get_user_details_populates_grounded_and_identity():
    """Grounding airline get_user_details result sets grounded and identity; real payment IDs preserved."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)
    action = Action(name="get_user_details", kwargs={"user_id": "mia_li_3668"})
    mock_env = MagicMock()
    mock_env.tools_map = {"get_user_details": MagicMock()}

    apply_grounding(
        mock_env,
        "airline",
        action,
        AIRLINE_USER_PROFILE_JSON,
        state,
    )

    assert state.grounded["user_id"] == "mia_li_3668"
    assert state.identity.user_id == "mia_li_3668"
    assert state.identity.profile_grounded is True
    assert "credit_card_4421486" in state.grounded["known_payment_method_ids"]
    assert "certificate_4856383" in state.grounded["known_payment_method_ids"]
    assert state.domain_state["payment_methods_from_profile"] == ["credit_card_4421486", "certificate_4856383"]
    assert state.grounded["reservation_ids"] == ["NO6JO3", "AIXC49"]
    assert state.grounded["user_profile"]["dob"] == "1990-04-05"
    assert state.grounded["user_profile"]["membership"] == "gold"


def test_grounding_retail_get_user_details():
    """Grounding retail get_user_details populates grounded and domain_state."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="retail", task=task)
    action = Action(name="get_user_details", kwargs={"user_id": "noah_brown_6181"})
    mock_env = MagicMock()
    mock_env.tools_map = {"get_user_details": MagicMock()}

    apply_grounding(
        mock_env,
        "retail",
        action,
        RETAIL_USER_PROFILE_JSON,
        state,
    )

    assert state.grounded["user_id"] == "noah_brown_6181"
    assert state.identity.profile_grounded is True
    assert "paypal_5727330" in state.grounded["known_payment_method_ids"]
    assert "credit_card_7815826" in state.grounded["known_payment_method_ids"]
    assert state.grounded["order_ids"] == ["#W7678072"]
    assert state.domain_state["payment_methods_from_profile"] == ["paypal_5727330", "credit_card_7815826"]


def test_user_id_lookup_auth_method_map():
    """Auth method is driven by USER_ID_LOOKUP_AUTH_METHOD map (not substring in action.name)."""
    assert USER_ID_LOOKUP_AUTH_METHOD.get("find_user_id_by_email") == "email"
    assert USER_ID_LOOKUP_AUTH_METHOD.get("find_user_id_by_name_zip") == "name_zip"


def test_grounding_retail_find_user_id_by_email():
    """Grounding find_user_id_by_email success sets identity and domain_state."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="retail", task=task)
    action = Action(name="find_user_id_by_email", kwargs={"email": "noah@example.com"})
    mock_env = MagicMock()
    mock_env.tools_map = {"find_user_id_by_email": MagicMock()}

    apply_grounding(
        mock_env,
        "retail",
        action,
        "noah_brown_6181",
        state,
    )

    assert state.grounded["user_id"] == "noah_brown_6181"
    assert state.identity.user_id == "noah_brown_6181"
    assert state.identity.authenticated is True
    assert state.identity.auth_method == "email"
    assert state.domain_state["user_id_from_lookup"] == "noah_brown_6181"
    assert state.domain_state["auth_method_used"] == "email"


def test_grounding_retail_find_user_id_by_name_zip():
    """Grounding find_user_id_by_name_zip success sets auth_method from USER_ID_LOOKUP_AUTH_METHOD map."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="retail", task=task)
    action = Action(name="find_user_id_by_name_zip", kwargs={"first_name": "Noah", "last_name": "Brown", "zip": "80279"})
    mock_env = MagicMock()
    mock_env.tools_map = {"find_user_id_by_name_zip": MagicMock()}

    apply_grounding(
        mock_env,
        "retail",
        action,
        "noah_brown_6181",
        state,
    )

    assert state.identity.authenticated is True
    assert state.identity.auth_method == USER_ID_LOOKUP_AUTH_METHOD["find_user_id_by_name_zip"]
    assert state.domain_state["user_id_from_lookup"] == "noah_brown_6181"


def test_grounding_error_observation_does_not_set_profile_or_authenticated():
    """Error observations must not set profile_grounded or authenticated."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)
    action = Action(name="get_user_details", kwargs={"user_id": "unknown_user"})
    mock_env = MagicMock()
    mock_env.tools_map = {"get_user_details": MagicMock()}

    apply_grounding(
        mock_env,
        "airline",
        action,
        "Error: user not found",
        state,
    )

    assert state.identity.profile_grounded is False
    assert state.identity.authenticated is False
    assert state.identity.user_id is None
    assert "user_id" not in state.grounded or state.grounded.get("user_id") is None


def test_grounding_find_user_id_error_does_not_authenticate():
    """find_user_id returning Error must not set authenticated."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="retail", task=task)
    action = Action(name="find_user_id_by_email", kwargs={"email": "nobody@example.com"})
    mock_env = MagicMock()
    mock_env.tools_map = {"find_user_id_by_email": MagicMock()}

    apply_grounding(
        mock_env,
        "retail",
        action,
        "Error: user not found",
        state,
    )

    assert state.identity.authenticated is False
    assert state.identity.user_id is None


def test_grounding_unknown_tool_skipped():
    """Tools not in registry do not update grounded state."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)
    action = Action(name="calculate", kwargs={"expression": "2 + 2"})
    mock_env = MagicMock()
    mock_env.tools_map = {"calculate": MagicMock()}

    apply_grounding(
        mock_env,
        "airline",
        action,
        "4",
        state,
    )

    assert state.identity.profile_grounded is False
    assert "user_id" not in state.grounded or state.grounded.get("user_id") is None


def test_grounding_reservation_details():
    """get_reservation_details populates reservation_details and domain_state."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)
    action = Action(name="get_reservation_details", kwargs={"reservation_id": "NO6JO3"})
    mock_env = MagicMock()
    mock_env.tools_map = {"get_reservation_details": MagicMock()}
    obs = json.dumps({"reservation_id": "NO6JO3", "status": "confirmed", "flights": []})

    apply_grounding(mock_env, "airline", action, obs, state)

    assert state.grounded["reservation_details"]["NO6JO3"]["status"] == "confirmed"
    assert state.domain_state["reservation_id"] == "NO6JO3"
    assert "NO6JO3" in state.grounded["reservation_ids"]


def test_grounding_order_details():
    """get_order_details populates order_details and domain_state."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="retail", task=task)
    action = Action(name="get_order_details", kwargs={"order_id": "#W7678072"})
    mock_env = MagicMock()
    mock_env.tools_map = {"get_order_details": MagicMock()}
    obs = json.dumps({"order_id": "#W7678072", "status": "delivered"})

    apply_grounding(mock_env, "retail", action, obs, state)

    assert state.grounded["order_details"]["#W7678072"]["status"] == "delivered"
    assert state.domain_state["order_id"] == "#W7678072"
    assert "#W7678072" in state.grounded["order_ids"]


def test_grounded_facts_summary_starts_with_contract_prefix():
    """Summary string starts with 'Grounded facts:' (contract for run_loop injection and heuristic skip)."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)
    summary = build_grounded_facts_summary(state)
    assert summary.strip().startswith("Grounded facts:")


def test_build_grounded_facts_summary_no_tool_names():
    """Summary string must not contain tool names; only grounded fact labels."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)
    summary = build_grounded_facts_summary(state)
    assert "get_user_details" not in summary
    assert "user_id=" in summary
    assert "profile_grounded=" in summary
    assert "not yet established" in summary or "user_id=None" in summary or "user_id=none" in summary.lower()


def test_build_grounded_facts_summary_with_grounded_data():
    """Summary includes grounded user_id and payment IDs when set."""
    task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    state = create_initial_task_state(domain="airline", task=task)
    state.grounded["user_id"] = "mia_li_3668"
    state.identity.profile_grounded = True
    state.grounded["known_payment_method_ids"] = ["credit_card_4421486"]
    state.grounded["reservation_ids"] = ["NO6JO3"]
    summary = build_grounded_facts_summary(state)
    assert "mia_li_3668" in summary
    assert "credit_card_4421486" in summary
    assert "NO6JO3" in summary


def test_run_loop_integration_grounding_called_after_tool_step():
    """After a tool step, apply_grounding is invoked and task_state gets grounded facts."""
    from tau_bench.orchestration.run_loop import run_orchestrated_loop
    from tau_bench.types import SolveResult

    captured_states = []

    def capture_apply_grounding(env, domain, action, observation, task_state):
        from tau_bench.orchestration.grounding import apply_grounding as real_apply
        real_apply(env, domain, action, observation, task_state)
        captured_states.append((action.name, observation[:80], dict(task_state.grounded)))

    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="Book flight", outputs=[])
    mock_env.tools_map = {"get_user_details": MagicMock()}
    # Validator requires tools_info schema for get_user_details; else validation fails and we never reach apply_grounding.
    mock_env.tools_info = [
        {
            "function": {
                "name": "get_user_details",
                "parameters": {
                    "type": "object",
                    "properties": {"user_id": {"type": "string"}},
                    "required": ["user_id"],
                },
            }
        }
    ]
    mock_env.reset.return_value = MagicMock(
        observation="I want to book a flight",
        info=MagicMock(model_dump=lambda: {}),
    )
    call_count = [0]

    def step_side_effect(action):
        call_count[0] += 1
        if action.name == "get_user_details":
            return MagicMock(
                observation=AIRLINE_USER_PROFILE_JSON,
                reward=0.0,
                done=False,
                info=MagicMock(model_dump=lambda: {}),
            )
        return MagicMock(
            observation="###STOP###",
            reward=1.0,
            done=True,
            info=MagicMock(model_dump=lambda: {}),
        )

    mock_env.step.side_effect = step_side_effect

    class TwoStepProposer:
        def __init__(self):
            self.step = 0

        def generate_next_step(self, messages):
            self.step += 1
            if self.step == 1:
                return (
                    {"role": "assistant", "tool_calls": [{"id": "tc1", "function": {"name": "get_user_details", "arguments": '{"user_id": "mia_li_3668"}'}}]},
                    Action(name="get_user_details", kwargs={"user_id": "mia_li_3668"}),
                    0.0,
                )
            return (
                {"role": "assistant", "content": "Done. ###STOP###"},
                Action(name=RESPOND_ACTION_NAME, kwargs={"content": "Done. ###STOP###"}),
                0.0,
            )

    mock_logger = MagicMock()

    with patch("tau_bench.orchestration.run_loop.apply_grounding", side_effect=capture_apply_grounding):
        result = run_orchestrated_loop(
            env=mock_env,
            proposer=TwoStepProposer(),
            run_logger=mock_logger,
            task_index=0,
            max_num_steps=5,
            domain="airline",
        )

    assert isinstance(result, SolveResult)
    assert result.reward == 1.0
    assert len(captured_states) >= 1
    action_name, obs_snippet, grounded = captured_states[0]
    assert action_name == "get_user_details"
    assert "mia_li_3668" in grounded.get("user_id", "")
    assert "credit_card_4421486" in grounded.get("known_payment_method_ids", [])
