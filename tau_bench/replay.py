# Copyright Sierra

"""Replay-graft timing driver for tau-bench.

Goal: measure timing on an *already recorded* trajectory without changing a
single message. The recorded trajectory is the ground truth (it carries the
paper's annotations); replay-graft "grafts" timing onto it by re-executing
the same logical operations and recording how long each takes:

  * agent_llm : a SHADOW completion() call on the recorded prefix. The model
    response is discarded; the recorded assistant message is what stays in the
    trajectory. We only keep the measured latency.
  * tool_exec : a REAL tool .invoke() against the env data (deterministic).
    The env data is mutated exactly as in the original run, so later tool
    calls see consistent state. A fidelity check compares the produced
    observation against the recorded one.
  * user_llm  : a SHADOW user-simulator turn (real completion via the user
    object), output discarded, recorded user message kept.

It uses the SAME tau_bench.timing.TimingRecorder as the live loop, with
source="replay", so the emitted TimingReport is schema-identical to live: a
report cannot be distinguished from a live one except by its `source` field.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from tau_bench.agents.tool_calling_agent import message_to_action
from tau_bench.envs import get_env
from tau_bench.timing import SpanKind, TimingRecorder
from tau_bench.types import RESPOND_ACTION_NAME, TimingReport


_ALLOWED_KEYS = {"role", "content", "tool_calls", "tool_call_id", "name"}


def _clean(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep only the keys litellm.completion accepts, dropping None content
    only when tool_calls are present (assistant tool-call messages)."""
    out: List[Dict[str, Any]] = []
    for m in messages:
        cm = {k: v for k, v in m.items() if k in _ALLOWED_KEYS and v is not None}
        if "role" not in cm:
            continue
        out.append(cm)
    return out


class ReplayGraftResult:
    def __init__(
        self,
        timing: TimingReport,
        fidelity_ok: bool,
        mismatches: List[Dict[str, Any]],
    ) -> None:
        self.timing = timing
        self.fidelity_ok = fidelity_ok
        self.mismatches = mismatches


def replay_graft(
    record: Dict[str, Any],
    *,
    env_name: str,
    task_split: str,
    model: str,
    model_provider: str,
    user_model: str,
    user_model_provider: str,
    user_strategy: str = "llm",
    temperature: float = 0.0,
    shadow: bool = True,
    fidelity_check: bool = True,
) -> ReplayGraftResult:
    """Replay one recorded EnvRunResult-shaped record and graft timing onto it.

    `record` must have at least `task_id` and `traj` (the recorded messages).
    `shadow=False` skips the LLM network calls (times only real tool execution
    and the recording overhead) for fast structural/CI runs.
    """
    from litellm import completion

    task_id = record["task_id"]
    traj: List[Dict[str, Any]] = record["traj"]

    env = get_env(
        env_name,
        user_strategy=user_strategy,
        user_model=user_model,
        task_split=task_split,
        user_provider=user_model_provider,
        task_index=task_id,
    )
    # Fresh, deterministic data for the graft; do not trigger env.reset's own
    # user call (we drive the user simulator ourselves below).
    env.task_index = task_id
    env.task = env.tasks[task_id]
    env.data = env.data_load_func()
    env.actions = []

    rec = TimingRecorder(source="replay")
    mismatches: List[Dict[str, Any]] = []

    def shadow_agent(prefix: List[Dict[str, Any]]) -> None:
        if not shadow:
            return
        completion(
            messages=_clean(prefix),
            model=model,
            custom_llm_provider=model_provider,
            tools=env.tools_info,
            temperature=temperature,
        )

    # --- step -1: initial user message (mirrors Env.reset in the live loop) ---
    rec.begin_step(-1)
    with rec.span(SpanKind.USER_LLM, "user"):
        if shadow:
            env.user.reset(instruction=env.task.instruction)

    # --- walk the recorded trajectory: [system, user, (assistant, tool|user)*] ---
    i = 2  # 0=system, 1=initial user
    step = 0
    n = len(traj)
    while i < n:
        msg = traj[i]
        if msg.get("role") != "assistant":
            i += 1
            continue
        rec.begin_step(step)
        with rec.span(SpanKind.AGENT_LLM, "agent"):
            shadow_agent(traj[:i])

        action = message_to_action(msg)
        nxt = traj[i + 1] if i + 1 < n else None

        if action.name != RESPOND_ACTION_NAME and action.name in env.tools_map:
            with rec.span(SpanKind.TOOL_EXEC, action.name):
                try:
                    obs = env.tools_map[action.name].invoke(
                        data=env.data, **action.kwargs
                    )
                except Exception as e:  # noqa: BLE001 - mirror Env.step
                    obs = f"Error: {e}"
            if fidelity_check and nxt is not None and nxt.get("role") == "tool":
                if str(obs) != str(nxt.get("content")):
                    mismatches.append(
                        {
                            "step": step,
                            "tool": action.name,
                            "recorded": nxt.get("content"),
                            "replayed": obs,
                        }
                    )
            i += 2 if (nxt is not None and nxt.get("role") == "tool") else 1
        else:
            # respond -> shadow a user-simulator turn, keep recorded user text
            with rec.span(SpanKind.USER_LLM, "user"):
                if shadow:
                    env.user.step(action.kwargs.get("content", ""))
            i += 2 if (nxt is not None and nxt.get("role") == "user") else 1
        step += 1

    report = rec.report()
    return ReplayGraftResult(
        timing=report,
        fidelity_ok=len(mismatches) == 0,
        mismatches=mismatches,
    )
