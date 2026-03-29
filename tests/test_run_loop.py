# Copyright Sierra
# Unit tests for run_loop: domain contract, grounded facts injection, recovery invocation.

import pytest
from unittest.mock import MagicMock, patch

from tau_bench.types import Task, Action, SolveResult, RESPOND_ACTION_NAME
from tau_bench.orchestration.run_loop import run_orchestrated_loop, MESSAGE_SOURCE_ORCHESTRATOR
from tau_bench.orchestration.task_state import create_initial_task_state


def test_run_loop_domain_required_raises():
    """run_orchestrated_loop raises ValueError when domain is None."""
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


def test_run_loop_injects_single_grounded_facts_message_per_step():
    """After each step, messages contain exactly one user message with content starting with 'Grounded facts:' (no accumulation)."""
    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="Book flight", outputs=[])
    mock_env.tools_map = {"get_user_details": MagicMock()}
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
    mock_env.step.return_value = MagicMock(
        observation='{"user_id": "u1", "payment_methods": {}, "reservations": []}',
        reward=0.0,
        done=False,
        info=MagicMock(model_dump=lambda: {}),
    )

    call_count = [0]

    class Proposer:
        def generate_next_step(self, messages):
            call_count[0] += 1
            if call_count[0] == 1:
                return (
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {"id": "tc1", "function": {"name": "get_user_details", "arguments": '{"user_id": "u1"}'}}
                        ],
                    },
                    Action(name="get_user_details", kwargs={"user_id": "u1"}),
                    0.0,
                )
            return (
                {"role": "assistant", "content": "Done."},
                Action(name=RESPOND_ACTION_NAME, kwargs={"content": "Done. ###STOP###"}),
                0.0,
            )

    mock_env.step.side_effect = lambda a: MagicMock(
        observation="###STOP###" if a.name == RESPOND_ACTION_NAME else mock_env.step.return_value.observation,
        reward=1.0 if a.name == RESPOND_ACTION_NAME else 0.0,
        done=a.name == RESPOND_ACTION_NAME,
        info=MagicMock(model_dump=lambda: {}),
    )

    mock_logger = MagicMock()
    result = run_orchestrated_loop(
        env=mock_env,
        proposer=Proposer(),
        run_logger=mock_logger,
        task_index=0,
        max_num_steps=5,
        domain="airline",
    )

    assert isinstance(result, SolveResult)
    grounded_user_messages = [
        m for m in result.messages
        if m.get("role") == "user"
        and isinstance(m.get("content"), str)
        and m["content"].strip().startswith("Grounded facts:")
        and m.get("source") == MESSAGE_SOURCE_ORCHESTRATOR
    ]
    assert len(grounded_user_messages) == 1, "Exactly one grounded facts message should exist (no accumulation)"


def test_run_loop_recovery_trace_written_on_validation_failure():
    """When validator rejects an action, recovery is invoked and write_trace_event called with module=recovery."""
    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    mock_env.tools_map = {"get_user_details": MagicMock()}
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
    mock_env.reset.return_value = MagicMock(observation="Hi", info=MagicMock(model_dump=lambda: {}))

    class ProposerInvalidTool:
        def generate_next_step(self, messages):
            return (
                {
                    "role": "assistant",
                    "tool_calls": [
                        {"id": "tc1", "function": {"name": "unknown_tool", "arguments": "{}"}},
                    ],
                },
                Action(name="unknown_tool", kwargs={}),
                0.0,
            )

    mock_logger = MagicMock()
    run_orchestrated_loop(
        env=mock_env,
        proposer=ProposerInvalidTool(),
        run_logger=mock_logger,
        task_index=0,
        max_num_steps=2,
        domain="airline",
    )

    trace_calls = [c for c in mock_logger.write_trace_event.call_args_list if c[0][0].get("module") == "recovery"]
    assert len(trace_calls) >= 1
    assert trace_calls[0][0][0].get("event_type") == "recovery_decision"


def test_run_loop_finish_run_includes_recovery_counters():
    """finish_run is called with num_recovery_invocations in counters when recovery was invoked."""
    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    mock_env.tools_map = {}
    mock_env.tools_info = []
    mock_env.reset.return_value = MagicMock(observation="Hi", info=MagicMock(model_dump=lambda: {}))

    class ProposerRespondOnly:
        def generate_next_step(self, messages):
            return (
                {"role": "assistant", "content": "Done. ###STOP###"},
                Action(name=RESPOND_ACTION_NAME, kwargs={"content": "Done. ###STOP###"}),
                0.0,
            )

    mock_env.step.return_value = MagicMock(
        observation="###STOP###",
        reward=1.0,
        done=True,
        info=MagicMock(model_dump=lambda: {}),
    )
    mock_logger = MagicMock()
    run_orchestrated_loop(
        env=mock_env,
        proposer=ProposerRespondOnly(),
        run_logger=mock_logger,
        task_index=0,
        max_num_steps=2,
        domain="retail",
    )

    mock_logger.finish_run.assert_called_once()
    call_kw = mock_logger.finish_run.call_args
    assert "counters" in call_kw[1]
    assert "num_recovery_invocations" in call_kw[1]["counters"]


# --- Integration: full confirmation retry path ---


def test_run_loop_full_confirmation_retry_path():
    """Policy blocks for missing confirmation → recovery sets pending → user affirms → retry executes → confirmation cleared."""
    tools_info = [
        {"function": {"name": "get_user_details", "parameters": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}}},
        {"function": {"name": "book_reservation", "parameters": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}}},
    ]
    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="Book", outputs=[])
    mock_env.tools_map = {"get_user_details": None, "book_reservation": None}
    mock_env.tools_info = tools_info
    mock_env.reset.return_value = MagicMock(observation="yes", info=MagicMock(model_dump=lambda: {}))
    created_states = []

    def capture_state(domain, task, initial_observation=None):
        s = create_initial_task_state(domain=domain, task=task, initial_observation=initial_observation)
        created_states.append(s)
        return s

    step_calls = []

    def step_side_effect(action):
        step_calls.append(action.name)
        if action.name == "get_user_details":
            return MagicMock(
                observation='{"user_id": "u1", "payment_methods": {}, "reservations": []}',
                reward=0.0,
                done=False,
                info=MagicMock(model_dump=lambda: {}),
            )
        if action.name == "book_reservation":
            return MagicMock(
                observation="Booked.",
                reward=1.0,
                done=True,
                info=MagicMock(model_dump=lambda: {}),
            )
        return MagicMock(observation="###STOP###", reward=1.0, done=True, info=MagicMock(model_dump=lambda: {}))

    mock_env.step.side_effect = step_side_effect
    call_count = [0]

    class Proposer:
        def generate_next_step(self, messages):
            call_count[0] += 1
            if call_count[0] == 1:
                return (
                    {"role": "assistant", "tool_calls": [{"id": "t1", "function": {"name": "get_user_details", "arguments": '{"user_id": "u1"}'}}]},
                    Action(name="get_user_details", kwargs={"user_id": "u1"}),
                    0.0,
                )
            if call_count[0] == 2:
                return (
                    {"role": "assistant", "tool_calls": [{"id": "t2", "function": {"name": "book_reservation", "arguments": '{"user_id": "u1"}'}}]},
                    Action(name="book_reservation", kwargs={"user_id": "u1"}),
                    0.0,
                )
            return (
                {"role": "assistant", "tool_calls": [{"id": "t3", "function": {"name": "book_reservation", "arguments": '{"user_id": "u1"}'}}]},
                Action(name="book_reservation", kwargs={"user_id": "u1"}),
                0.0,
            )

    mock_logger = MagicMock()
    with patch("tau_bench.orchestration.run_loop.create_initial_task_state", side_effect=capture_state):
        result = run_orchestrated_loop(
            env=mock_env,
            proposer=Proposer(),
            run_logger=mock_logger,
            task_index=0,
            max_num_steps=6,
            domain="airline",
        )

    assert result.reward == 1.0
    assert "book_reservation" in step_calls
    assert step_calls.count("book_reservation") == 1
    assert len(created_states) == 1
    assert "booking_confirmed" not in created_states[0].confirmations
    mock_logger.finish_run.assert_called_once()
    assert mock_logger.finish_run.call_args[1]["exit_reason"] == "success"


# --- Integration: negative confirmation path ---


def test_run_loop_negative_confirmation_does_not_unlock():
    """Pending confirmation exists; user reply is not affirmative; mutating action stays blocked."""
    tools_info = [
        {"function": {"name": "get_user_details", "parameters": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}}},
        {"function": {"name": "book_reservation", "parameters": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}}},
    ]
    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    mock_env.tools_map = {"get_user_details": None, "book_reservation": None}
    mock_env.tools_info = tools_info
    mock_env.reset.return_value = MagicMock(observation="no", info=MagicMock(model_dump=lambda: {}))

    def step_side_effect(action):
        if action.name == "get_user_details":
            return MagicMock(
                observation='{"user_id": "u1", "payment_methods": {}, "reservations": []}',
                reward=0.0,
                done=False,
                info=MagicMock(model_dump=lambda: {}),
            )
        return MagicMock(observation="###STOP###", reward=0.0, done=False, info=MagicMock(model_dump=lambda: {}))
    mock_env.step.side_effect = step_side_effect

    call_count = [0]

    class Proposer:
        def generate_next_step(self, messages):
            call_count[0] += 1
            if call_count[0] == 1:
                return (
                    {"role": "assistant", "tool_calls": [{"id": "t1", "function": {"name": "get_user_details", "arguments": '{"user_id": "u1"}'}}]},
                    Action(name="get_user_details", kwargs={"user_id": "u1"}),
                    0.0,
                )
            return (
                {"role": "assistant", "tool_calls": [{"id": "t2", "function": {"name": "book_reservation", "arguments": '{"user_id": "u1"}'}}]},
                Action(name="book_reservation", kwargs={"user_id": "u1"}),
                0.0,
            )

    mock_logger = MagicMock()
    run_orchestrated_loop(
        env=mock_env,
        proposer=Proposer(),
        run_logger=mock_logger,
        task_index=0,
        max_num_steps=5,
        domain="airline",
    )

    step_action_names = [c[0][0].name for c in mock_env.step.call_args_list]
    assert "book_reservation" not in step_action_names


# --- Integration: tool execution error recovery ---


def test_run_loop_tool_execution_error_invokes_recovery_and_trace():
    """Executor returns observation starting with 'Error:' → recovery invoked and trace event written."""
    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    mock_env.tools_map = {"get_user_details": None}
    mock_env.tools_info = [
        {"function": {"name": "get_user_details", "parameters": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}}},
    ]
    mock_env.reset.return_value = MagicMock(observation="Hi", info=MagicMock(model_dump=lambda: {}))
    mock_env.step.return_value = MagicMock(
        observation="Error: user not found",
        reward=0.0,
        done=False,
        info=MagicMock(model_dump=lambda: {}),
    )

    class Proposer:
        def generate_next_step(self, messages):
            return (
                {"role": "assistant", "tool_calls": [{"id": "t1", "function": {"name": "get_user_details", "arguments": '{"user_id": "x"}'}}]},
                Action(name="get_user_details", kwargs={"user_id": "x"}),
                0.0,
            )

    mock_logger = MagicMock()
    result = run_orchestrated_loop(
        env=mock_env,
        proposer=Proposer(),
        run_logger=mock_logger,
        task_index=0,
        max_num_steps=3,
        domain="airline",
    )

    trace_calls = [c for c in mock_logger.write_trace_event.call_args_list if c[0][0].get("module") == "recovery"]
    assert len(trace_calls) >= 1
    assert any(c[0][0].get("failure_trigger") == "tool_execution_error" for c in trace_calls)
    assert any("Error:" in (m.get("content") or "") for m in result.messages if m.get("role") == "tool")


# --- Integration: grounded facts replacement over multiple steps ---


def test_run_loop_grounded_facts_single_message_after_multiple_tool_steps():
    """Multiple tool steps; only one current grounded facts message remains; no accumulation."""
    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    mock_env.tools_map = {"get_user_details": None, "get_reservation_details": None}
    mock_env.tools_info = [
        {"function": {"name": "get_user_details", "parameters": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}}},
        {"function": {"name": "get_reservation_details", "parameters": {"type": "object", "properties": {"reservation_id": {"type": "string"}}, "required": ["reservation_id"]}}},
    ]
    mock_env.reset.return_value = MagicMock(observation="Hi", info=MagicMock(model_dump=lambda: {}))
    call_count = [0]

    def step_side_effect(action):
        if action.name == "get_user_details":
            return MagicMock(observation='{"user_id":"u1","reservations":[]}', reward=0.0, done=False, info=MagicMock(model_dump=lambda: {}))
        if action.name == "get_reservation_details":
            return MagicMock(observation='{}', reward=0.0, done=False, info=MagicMock(model_dump=lambda: {}))
        return MagicMock(observation="###STOP###", reward=1.0, done=True, info=MagicMock(model_dump=lambda: {}))
    mock_env.step.side_effect = step_side_effect

    class Proposer:
        def generate_next_step(self, messages):
            call_count[0] += 1
            if call_count[0] == 1:
                return (
                    {"role": "assistant", "tool_calls": [{"id": "t1", "function": {"name": "get_user_details", "arguments": '{"user_id": "u1"}'}}]},
                    Action(name="get_user_details", kwargs={"user_id": "u1"}),
                    0.0,
                )
            if call_count[0] == 2:
                return (
                    {"role": "assistant", "tool_calls": [{"id": "t2", "function": {"name": "get_reservation_details", "arguments": '{"reservation_id": "R1"}'}}]},
                    Action(name="get_reservation_details", kwargs={"reservation_id": "R1"}),
                    0.0,
                )
            return (
                {"role": "assistant", "content": "Done."},
                Action(name=RESPOND_ACTION_NAME, kwargs={"content": "Done. ###STOP###"}),
                0.0,
            )

    mock_logger = MagicMock()
    result = run_orchestrated_loop(
        env=mock_env,
        proposer=Proposer(),
        run_logger=mock_logger,
        task_index=0,
        max_num_steps=6,
        domain="airline",
    )

    grounded = [
        m
        for m in result.messages
        if m.get("role") == "user"
        and isinstance(m.get("content"), str)
        and m["content"].strip().startswith("Grounded facts:")
        and m.get("source") == MESSAGE_SOURCE_ORCHESTRATOR
    ]
    assert len(grounded) == 1


# --- Integration: recovery bookkeeping ---


def test_run_loop_repeated_validation_failure_triggers_safe_terminate():
    """Repeated same invalid action through run_loop increments recovery state; eventually SAFE_TERMINATE and finish_run."""
    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    mock_env.tools_map = {}
    mock_env.tools_info = []
    mock_env.reset.return_value = MagicMock(observation="Hi", info=MagicMock(model_dump=lambda: {}))

    class ProposerSameInvalid:
        def generate_next_step(self, messages):
            return (
                {"role": "assistant", "tool_calls": [{"id": "t1", "function": {"name": "bad_tool", "arguments": "{}"}}]},
                Action(name="bad_tool", kwargs={}),
                0.0,
            )

    mock_logger = MagicMock()
    result = run_orchestrated_loop(
        env=mock_env,
        proposer=ProposerSameInvalid(),
        run_logger=mock_logger,
        task_index=0,
        max_num_steps=5,
        domain="airline",
    )

    mock_logger.finish_run.assert_called_once()
    assert mock_logger.finish_run.call_args[1]["exit_reason"] == "recovery_terminated"
    assert mock_logger.finish_run.call_args[1]["counters"]["num_recovery_invocations"] >= 1


def test_no_synthetic_orchestrator_message_as_plain_user():
    """Messages with Grounded facts / Validation failed / Policy blocked must have source=orchestrator."""
    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    mock_env.tools_map = {"get_user_details": MagicMock()}
    mock_env.tools_info = [
        {"function": {"name": "get_user_details", "parameters": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}}}
    ]
    mock_env.reset.return_value = MagicMock(observation="Hi", info=MagicMock(model_dump=lambda: {}))
    mock_env.step.return_value = MagicMock(observation="ok", reward=0.0, done=False, info=MagicMock(model_dump=lambda: {}))

    class Proposer:
        def generate_next_step(self, messages):
            return (
                {"role": "assistant", "tool_calls": [{"id": "t1", "function": {"name": "get_user_details", "arguments": '{"user_id": "u1"}'}}]},
                Action(name="get_user_details", kwargs={"user_id": "u1"}),
                0.0,
            )

    result = run_orchestrated_loop(
        env=mock_env,
        proposer=Proposer(),
        run_logger=MagicMock(),
        task_index=0,
        max_num_steps=2,
        domain="airline",
    )
    for m in result.messages:
        c = m.get("content") if isinstance(m.get("content"), str) else ""
        if c.strip().startswith("Grounded facts:") or c.strip().startswith("Validation failed:") or c.strip().startswith("Policy blocked:"):
            assert m.get("source") == MESSAGE_SOURCE_ORCHESTRATOR, f"Expected source=orchestrator for synthetic message: {c[:80]}"


def test_proposer_role_normalized_to_assistant():
    """Proposer that returns wrong role gets normalized to assistant in result messages."""
    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    mock_env.tools_map = {}
    mock_env.tools_info = []
    mock_env.reset.return_value = MagicMock(observation="Hi", info=MagicMock(model_dump=lambda: {}))
    mock_env.step.return_value = MagicMock(observation="###STOP###", reward=1.0, done=True, info=MagicMock(model_dump=lambda: {}))

    class ProposerWrongRole:
        def generate_next_step(self, messages):
            return (
                {"role": "other", "content": "Done."},
                Action(name=RESPOND_ACTION_NAME, kwargs={"content": "Done. ###STOP###"}),
                0.0,
            )

    result = run_orchestrated_loop(
        env=mock_env,
        proposer=ProposerWrongRole(),
        run_logger=MagicMock(),
        task_index=0,
        max_num_steps=2,
        domain="airline",
    )
    assistant_msgs = [m for m in result.messages if m.get("role") == "assistant"]
    assert len(assistant_msgs) >= 1
    assert all(m.get("role") == "assistant" for m in result.messages if m.get("role") not in ("system", "user", "tool"))


def test_user_observation_think_tags_sanitized_in_trajectory():
    """Env observation containing <think> is sanitized before being stored as user message."""
    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    mock_env.tools_map = {}
    mock_env.tools_info = []
    mock_env.reset.return_value = MagicMock(observation="Hi", info=MagicMock(model_dump=lambda: {}))
    mock_env.step.return_value = MagicMock(
        observation="<think> I will say yes </think>\nYes please.",
        reward=1.0,
        done=True,
        info=MagicMock(model_dump=lambda: {}),
    )

    class Proposer:
        def generate_next_step(self, messages):
            return (
                {"role": "assistant", "content": "Done."},
                Action(name=RESPOND_ACTION_NAME, kwargs={"content": "Done."}),
                0.0,
            )

    result = run_orchestrated_loop(
        env=mock_env,
        proposer=Proposer(),
        run_logger=MagicMock(),
        task_index=0,
        max_num_steps=2,
        domain="airline",
    )
    user_contents = [m.get("content") for m in result.messages if m.get("role") == "user" and isinstance(m.get("content"), str)]
    for content in user_contents:
        if content.strip().startswith("Grounded facts:"):
            continue
        assert "<think>" not in content, f"User message should not contain <think>: {content!r}"
        assert "</think>" not in content, f"User message should not contain </think>: {content!r}"


def test_saved_trajectory_roles_match_in_memory():
    """Serializing EnvRunResult and parsing back preserves roles (traj matches in-memory messages)."""
    import json
    mock_env = MagicMock()
    mock_env.wiki = "# Policy"
    mock_env.task = Task(user_id="u1", actions=[], instruction="", outputs=[])
    mock_env.tools_map = {}
    mock_env.tools_info = []
    mock_env.reset.return_value = MagicMock(observation="Hi", info=MagicMock(model_dump=lambda: {}))
    mock_env.step.return_value = MagicMock(observation="###STOP###", reward=1.0, done=True, info=MagicMock(model_dump=lambda: {}))

    class Proposer:
        def generate_next_step(self, messages):
            return (
                {"role": "assistant", "content": "Done."},
                Action(name=RESPOND_ACTION_NAME, kwargs={"content": "Done. ###STOP###"}),
                0.0,
            )

    result = run_orchestrated_loop(
        env=mock_env,
        proposer=Proposer(),
        run_logger=MagicMock(),
        task_index=0,
        max_num_steps=2,
        domain="airline",
    )
    from tau_bench.types import EnvRunResult
    er = EnvRunResult(task_id=0, reward=result.reward, info=result.info, traj=result.messages, trial=0)
    dumped = er.model_dump()
    loaded = json.loads(json.dumps(dumped))
    traj = loaded["traj"]
    assert len(traj) == len(result.messages)
    for i, (orig, saved) in enumerate(zip(result.messages, traj)):
        assert saved.get("role") == orig.get("role"), f"Role mismatch at index {i}: {orig.get('role')} vs {saved.get('role')}"
