# Copyright Sierra
# Minimal orchestrator run loop: init/reset → proposer → validator → executor → state update → finish_run.
# Only the orchestrator calls the logger.

from typing import Any, Dict, List, Optional

from tau_bench.envs.base import Env
from tau_bench.orchestration.logging import observation_summary
from tau_bench.orchestration.validator import ValidatorResult, validate_action
from tau_bench.types import Action, SolveResult, RESPOND_ACTION_NAME

# Logger protocol: has log_run_start, log_step_stage, write_trace_event, finish_run
RunLogger = Any


def run_orchestrated_loop(
    env: Env,
    proposer: Any,  # has generate_next_step(messages) -> (next_message, action, cost)
    run_logger: RunLogger,
    task_index: Optional[int],
    max_num_steps: int,
) -> SolveResult:
    """Run one task: reset → start log → loop (propose → validate → execute → state update) → finish_run."""
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
