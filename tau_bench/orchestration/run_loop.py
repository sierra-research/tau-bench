# Copyright Sierra
# Minimal orchestrator run loop: init/reset → proposer → validator → executor → state update → finish_run.
# Only the orchestrator calls the logger.

from typing import Any, Dict, List, Optional

from tau_bench.envs.base import Env
from tau_bench.orchestration.grounding import apply_grounding, build_grounded_facts_summary
from tau_bench.orchestration.logging import observation_summary
from tau_bench.orchestration.task_state import TaskState, create_initial_task_state
from tau_bench.orchestration.validator import ValidatorResult, validate_action
from tau_bench.orchestration.policy_guard import PolicyGuardResult, check_policy
from tau_bench.types import Action, SolveResult, RESPOND_ACTION_NAME

# Logger protocol: has log_run_start, log_step_stage, write_trace_event, finish_run
RunLogger = Any


def run_orchestrated_loop(
    env: Env,
    proposer: Any,  # has generate_next_step(messages) -> (next_message, action, cost)
    run_logger: RunLogger,
    task_index: Optional[int],
    max_num_steps: int,
    domain: Optional[str] = None,
) -> SolveResult:
    """Run one task: reset → start log → loop (propose → validate → execute → state update) → finish_run.
    TaskState is created at entry and updated each step for policy guard, planner, recovery, etc."""
    total_cost = 0.0
    steps = 0
    reward = 0.0
    num_validation_failures = 0
    info: Dict[str, Any] = {}
    messages: List[Dict[str, Any]] = []
    try:
        env_reset_res = env.reset(task_index=task_index)
        obs = env_reset_res.observation
        info = env_reset_res.info.model_dump()
        messages = [
            {"role": "system", "content": env.wiki},
            {"role": "user", "content": obs},
        ]
        task_state: TaskState = create_initial_task_state(
            domain=domain or "airline",
            task=env.task,
            initial_observation=obs,
        )
        run_logger.log_run_start()
        first_event = {
            "step_index": 0,
            "module": "orchestrator",
            "event_type": "run_start",
        }
        run_logger.write_trace_event(first_event)

        last_action: Optional[str] = None
        last_observation_summary: str = observation_summary(obs)
        done = False

        for step_index in range(1, max_num_steps + 1):
            # Lightweight state snapshot at beginning of step (no full message history)
            run_logger.write_trace_event({
                "step_index": step_index,
                "module": "orchestrator",
                "event_type": "state_snapshot",
                "last_action": last_action,
                "last_observation_summary": last_observation_summary,
                "messages_len": len(messages),
                "total_cost": total_cost,
                "done": done,
            })
            # Inject grounded facts summary so LLM can reason with "what we know" (no tool names in prompt)
            summary = build_grounded_facts_summary(task_state)
            for i in range(len(messages) - 1, -1, -1):
                if "content" in messages[i] and isinstance(messages[i].get("content"), str):
                    messages[i]["content"] = f"[{summary}]\n\n{messages[i]['content']}"
                    break
            next_message, action, cost = proposer.generate_next_step(messages)
            total_cost += cost
            # Proposer stage (log + trace)
            run_logger.log_step_stage(
                step_index,
                "proposer",
                {"action_name": action.name, "cost": cost},
            )
            run_logger.write_trace_event({
                "step_index": step_index,
                "module": "proposer",
                "event_type": "proposed",
                "action_name": action.name,
                "cost": cost,
            })
            # Validator stage (structured result; log + trace)
            v_result: ValidatorResult = validate_action(env, action, step_index)
            run_logger.log_step_stage(
                step_index,
                "validator",
                {"allowed": v_result.allowed, "code": v_result.code, "message": v_result.message, "action_name": action.name},
            )
            run_logger.write_trace_event({
                "step_index": step_index,
                "module": "validator",
                "event_type": "validated",
                "allowed": v_result.allowed,
                "code": v_result.code,
                "message": v_result.message,
                "action_name": action.name,
            })
            if not v_result.allowed:
                num_validation_failures += 1
                rejection = f"Validation failed: {v_result.message}"
                if action.name != RESPOND_ACTION_NAME and "tool_calls" in next_message and next_message.get("tool_calls"):
                    next_message["tool_calls"] = next_message["tool_calls"][:1]
                    messages.extend([
                        next_message,
                        {
                            "role": "tool",
                            "tool_call_id": next_message["tool_calls"][0]["id"],
                            "name": next_message["tool_calls"][0]["function"]["name"],
                            "content": rejection,
                        },
                    ])
                else:
                    messages.extend([next_message, {"role": "user", "content": rejection}])
                last_action = action.name
                last_observation_summary = observation_summary(rejection)
                steps = step_index
                continue
            # Policy guard stage (after validator, before executor)
            p_result: PolicyGuardResult = check_policy(env, action, task_state)
            run_logger.log_step_stage(
                step_index,
                "policy_guard",
                {"allowed": p_result.allowed, "code": p_result.code, "message": p_result.message, "action_name": action.name},
            )
            run_logger.write_trace_event({
                "step_index": step_index,
                "module": "policy_guard",
                "event_type": "blocked" if not p_result.allowed else "checked",
                "allowed": p_result.allowed,
                "code": p_result.code,
                "message": p_result.message,
                "action_name": action.name,
            })
            if not p_result.allowed:
                rejection = f"Policy blocked: {p_result.message}"
                task_state.set_last_error(f"Policy blocked ({p_result.code}): {p_result.message}")
                if action.name != RESPOND_ACTION_NAME and "tool_calls" in next_message and next_message.get("tool_calls"):
                    next_message["tool_calls"] = next_message["tool_calls"][:1]
                    messages.extend([
                        next_message,
                        {
                            "role": "tool",
                            "tool_call_id": next_message["tool_calls"][0]["id"],
                            "name": next_message["tool_calls"][0]["function"]["name"],
                            "content": rejection,
                        },
                    ])
                else:
                    messages.extend([next_message, {"role": "user", "content": rejection}])
                last_action = action.name
                last_observation_summary = observation_summary(rejection)
                steps = step_index
                continue
            env_response = env.step(action)
            reward = env_response.reward
            info = {**info, **env_response.info.model_dump()}
            obs_summary = observation_summary(env_response.observation)
            run_logger.log_step_stage(
                step_index,
                "executor",
                {"reward": reward, "done": env_response.done, "observation_summary": obs_summary},
            )
            trace_evt = {
                "step_index": step_index,
                "module": "executor",
                "event_type": "step",
                "action_name": action.name,
                "reward": reward,
                "done": env_response.done,
                "total_cost": total_cost,
                "observation_summary": obs_summary,
            }
            run_logger.write_trace_event(trace_evt)

            task_state.update_after_step(action.name, env_response.observation)
            # Grounding only for env tool steps, not for terminal respond actions.
            if action.name != RESPOND_ACTION_NAME:
                apply_grounding(
                    env,
                    task_state.domain,
                    action,
                    env_response.observation,
                    task_state,
                )

            last_action = action.name
            last_observation_summary = obs_summary
            done = env_response.done

            if action.name != RESPOND_ACTION_NAME:
                next_message["tool_calls"] = next_message["tool_calls"][:1]
                messages.extend(
                    [
                        next_message,
                        {
                            "role": "tool",
                            "tool_call_id": next_message["tool_calls"][0]["id"],
                            "name": next_message["tool_calls"][0]["function"]["name"],
                            "content": env_response.observation,
                        },
                    ]
                )
            else:
                messages.extend(
                    [
                        next_message,
                        {"role": "user", "content": env_response.observation},
                    ]
                )
            steps = step_index
            if env_response.done:
                run_logger.finish_run(
                    exit_reason="success",
                    steps=steps,
                    total_cost=total_cost,
                    reward=reward,
                    done=True,
                    counters={"num_validation_failures": num_validation_failures},
                )
                return SolveResult(
                    reward=reward,
                    info=info,
                    messages=messages,
                    total_cost=total_cost,
                )

        run_logger.finish_run(
            exit_reason="budget_exhausted",
            steps=steps,
            total_cost=total_cost,
            reward=reward,
            done=False,
            counters={"num_validation_failures": num_validation_failures},
        )
        return SolveResult(
            reward=reward,
            info=info,
            messages=messages,
            total_cost=total_cost,
        )
    except Exception as e:
        run_logger.finish_run(
            exit_reason="error",
            steps=steps,
            total_cost=total_cost,
            reward=reward,
            done=False,
            counters={"error": 1, "num_validation_failures": num_validation_failures},
        )
        raise
