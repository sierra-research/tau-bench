# Copyright Sierra
"""End-to-end smoke test for live `--enable-timing` wiring.

Unlike test_timing.py (which exercises the timing core in isolation), this test
drives the *real* run loop: a real retail Env + ToolCallingAgent, with only the
network LLM calls stubbed out. It verifies that attaching a TimingRecorder makes
agent.solve() produce a populated TimingReport whose spans cover all three span
kinds, are grouped by step, and roll up consistently.
"""
import json
from unittest.mock import patch

from tau_bench.envs import get_env
from tau_bench.agents.tool_calling_agent import ToolCallingAgent
from tau_bench.timing import SpanKind, TimingRecorder


class _FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self._tool_calls = tool_calls

    def model_dump(self):
        return {
            "role": "assistant",
            "content": self.content,
            "tool_calls": self._tool_calls,
        }


class _FakeResponse:
    def __init__(self, message, cost=0.0):
        self.choices = [type("Choice", (), {"message": message})()]
        self._hidden_params = {"response_cost": cost}


def _tool_call_message(name, arguments):
    return _FakeMessage(
        content=None,
        tool_calls=[
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments)},
            }
        ],
    )


def test_live_timing_end_to_end_smoke():
    # Scripted agent: step 0 calls a pure tool, step 1 responds (ends dialog).
    agent_script = iter(
        [
            _tool_call_message("calculate", {"expression": "2 + 2"}),
            _FakeMessage(content="The answer is 4. Anything else?"),
        ]
    )

    def fake_agent_completion(*args, **kwargs):
        return _FakeResponse(next(agent_script))

    # User sim always ends the conversation; ###STOP### marks the run done.
    def fake_user_completion(*args, **kwargs):
        return _FakeResponse(_FakeMessage(content="Thanks, that's all. ###STOP###"))

    with patch(
        "tau_bench.envs.user.completion", side_effect=fake_user_completion
    ), patch(
        "tau_bench.agents.tool_calling_agent.completion",
        side_effect=fake_agent_completion,
    ):
        env = get_env(
            "retail",
            user_strategy="llm",
            user_model="gpt-4o",
            task_split="test",
            user_provider="openai",
            task_index=0,
        )
        env.attach_timing(TimingRecorder(source="live"))
        agent = ToolCallingAgent(
            tools_info=env.tools_info,
            wiki=env.wiki,
            model="gpt-4o",
            provider="openai",
            temperature=0.0,
        )
        result = agent.solve(env=env, task_index=0, max_num_steps=5)

    timing = result.timing
    assert timing is not None, "live run with recorder must populate SolveResult.timing"
    assert timing.source == "live"

    # Steps: -1 (initial user message from env.reset), 0 (tool), 1 (respond).
    assert timing.n_steps == 3
    assert {s.step_index for s in timing.spans} == {-1, 0, 1}
    kinds = {s.kind for s in timing.spans}
    assert kinds == {SpanKind.AGENT_LLM, SpanKind.TOOL_EXEC, SpanKind.USER_LLM}

    # One agent call per real step (2); one tool exec; two user-sim calls
    # (the initial reset greeting at step -1, and the reply to the agent's
    # respond at step 1).
    by_kind = {}
    for s in timing.spans:
        by_kind.setdefault(s.kind, []).append(s)
    assert len(by_kind[SpanKind.AGENT_LLM]) == 2
    assert len(by_kind[SpanKind.TOOL_EXEC]) == 1
    assert len(by_kind[SpanKind.USER_LLM]) == 2
    assert by_kind[SpanKind.TOOL_EXEC][0].name == "calculate"

    # Grand totals equal the span-level aggregation per kind.
    assert abs(
        timing.agent_llm_ms
        - sum(s.duration_ms for s in by_kind[SpanKind.AGENT_LLM])
    ) < 1e-6
    assert abs(
        timing.tool_ms - sum(s.duration_ms for s in by_kind[SpanKind.TOOL_EXEC])
    ) < 1e-6
    assert abs(
        timing.user_llm_ms
        - sum(s.duration_ms for s in by_kind[SpanKind.USER_LLM])
    ) < 1e-6

    # Per-step rollups are non-negative and bounded by the wall-clock total.
    for step in timing.steps:
        assert step.step_ms >= 0
        assert step.agent_llm_ms >= 0
        assert step.tool_ms >= 0
        assert step.user_llm_ms >= 0
        assert step.step_ms <= timing.total_ms + 1e-6
    assert timing.total_ms >= 0
