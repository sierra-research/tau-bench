# Copyright Sierra
# Minimal orchestrator run loop: init/reset → proposer → validator → executor → state update → finish_run.
# Only the orchestrator calls the logger.
#
# Conventions:
# - Single effective action per step: only the first tool call from the proposer is used; multi-tool-call is not supported.
# - Tool errors: tools return observations starting with "Error: " on failure; task_state and grounding use this convention.

from typing import Any, Dict, List, Optional

from tau_bench.envs.base import Env
from tau_bench.orchestration.grounding import apply_grounding, build_grounded_facts_summary
from tau_bench.orchestration.logging import observation_summary
from tau_bench.orchestration.message_utils import sanitize_user_observation, strip_think_tags
from tau_bench.orchestration.task_state import TaskState, create_initial_task_state
from tau_bench.orchestration.validator import ValidatorResult, validate_action
from tau_bench.orchestration.policy_guard import PolicyGuardResult, check_policy
from tau_bench.orchestration.recovery import (
    RecoveryState,
    RecoveryInput,
    RecoveryDecision,
    decide_recovery,
    check_confirmation_heuristic,
    action_retry_key,
    FAILURE_VALIDATION_ERROR,
    FAILURE_POLICY_BLOCK,
    FAILURE_TOOL_EXECUTION_ERROR,
    STRATEGY_ASK_USER_CONFIRMATION,
    STRATEGY_SAFE_TERMINATE,
)
from tau_bench.types import Action, SolveResult, RESPOND_ACTION_NAME

# Message dict key: when present and "orchestrator", the message is synthetic (grounded facts / rejection), not real user.
MESSAGE_SOURCE_ORCHESTRATOR = "orchestrator"

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
    TaskState is created at entry and updated each step for policy guard, planner, recovery, etc.
    domain must be passed by the caller (e.g. config.env); no default is applied."""
    if domain is None:
        raise ValueError("domain is required for run_orchestrated_loop (e.g. pass config.env)")
    total_cost = 0.0
    steps = 0
    reward = 0.0
    num_validation_failures = 0
    info: Dict[str, Any] = {}
    messages: List[Dict[str, Any]] = []
    recovery_state: Optional[RecoveryState] = None
    try:
        env_reset_res = env.reset(task_index=task_index)
        obs = env_reset_res.observation
        info = env_reset_res.info.model_dump()
        messages = [
            {"role": "system", "content": env.wiki},
            {"role": "user", "content": obs},
        ]
        task_state: TaskState = create_initial_task_state(
            domain=domain,
            task=env.task,
            initial_observation=obs,
        )
        recovery_state = RecoveryState()
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
        recent_action_names: List[str] = []

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
            # Confirmation: if pending side-effect and last message is from user, check heuristic and maybe add_confirmation
            if (
                recovery_state.pending_side_effect_action is not None
                and recovery_state.pending_confirmation_key
            ):
                last_user_content = None
                for i in range(len(messages) - 1, -1, -1):
                    if messages[i].get("role") == "user" and isinstance(messages[i].get("content"), str):
                        if messages[i].get("source") == MESSAGE_SOURCE_ORCHESTRATOR:
                            continue
                        last_user_content = messages[i]["content"]
                        break
                if last_user_content is not None and check_confirmation_heuristic(
                    last_user_content, recovery_state.pending_confirmation_key
                ):
                    task_state.add_confirmation(recovery_state.pending_confirmation_key)
                    recovery_state.retry_key_just_confirmed = action_retry_key(
                        recovery_state.pending_side_effect_action
                    )
                    recovery_state.confirmation_key_just_used = recovery_state.pending_confirmation_key
                    recovery_state.pending_side_effect_action = None
                    recovery_state.pending_confirmation_key = None
            # Inject grounded facts summary as a single dedicated message (no accumulation)
            summary = build_grounded_facts_summary(task_state)
            # Remove any previous grounded-summary message so only one exists
            messages = [m for m in messages if not (
                isinstance(m.get("content"), str) and m["content"].strip().startswith("Grounded facts:")
            )]
            messages.append({"role": "user", "content": summary, "source": MESSAGE_SOURCE_ORCHESTRATOR})
            next_message, action, cost = proposer.generate_next_step(messages)
            # Proposer output must be treated as assistant; normalize in case provider omits or mis-sets role.
            if next_message.get("role") != "assistant":
                next_message = {**next_message, "role": "assistant"}
            # Remove <think> blocks from assistant content so they are not persisted in trajectory.
            if isinstance(next_message.get("content"), str):
                next_message = {**next_message, "content": strip_think_tags(next_message["content"]).strip()}
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
                recovery_input = RecoveryInput(
                    failure_type=FAILURE_VALIDATION_ERROR,
                    action=action,
                    step_index=step_index,
                    validator_result=v_result,
                    task_state=task_state,
                    recovery_state=recovery_state,
                    recent_action_names=recent_action_names[-3:] if recent_action_names else None,
                )
                recovery_decision: RecoveryDecision = decide_recovery(recovery_input, domain=domain)
                recovery_state.recovery_count_this_run += 1
                if recovery_decision.proposed_strategy == STRATEGY_SAFE_TERMINATE and recovery_decision.terminal_reason:
                    run_logger.finish_run(
                        exit_reason="recovery_terminated",
                        steps=step_index,
                        total_cost=total_cost,
                        reward=reward,
                        done=False,
                        counters={
                            "num_validation_failures": num_validation_failures,
                            "num_recovery_invocations": recovery_state.recovery_count_this_run,
                        },
                    )
                    return SolveResult(
                        reward=reward,
                        info=info,
                        messages=messages,
                        total_cost=total_cost,
                    )
                run_logger.write_trace_event({
                    "step_index": step_index,
                    "module": "recovery",
                    "event_type": "recovery_decision",
                    "failure_trigger": recovery_decision.failure_type,
                    "failure_code": recovery_decision.trace_metadata.get("failure_code"),
                    "chosen_strategy": recovery_decision.proposed_strategy,
                    "retry_key": recovery_decision.retry_key,
                    "recovery_count_this_run": recovery_state.recovery_count_this_run,
                    "terminal_reason": recovery_decision.terminal_reason,
                })
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
                    messages.extend([next_message, {"role": "user", "content": rejection, "source": MESSAGE_SOURCE_ORCHESTRATOR}])
                last_action = action.name
                last_observation_summary = observation_summary(rejection)
                steps = step_index
                recent_action_names = (recent_action_names + [action.name])[-3:]
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
                recovery_input = RecoveryInput(
                    failure_type=FAILURE_POLICY_BLOCK,
                    action=action,
                    step_index=step_index,
                    policy_result=p_result,
                    task_state=task_state,
                    recovery_state=recovery_state,
                    recent_action_names=recent_action_names[-3:] if recent_action_names else None,
                )
                recovery_decision = decide_recovery(recovery_input, domain=domain)
                recovery_state.recovery_count_this_run += 1
                if recovery_decision.proposed_strategy == STRATEGY_SAFE_TERMINATE and recovery_decision.terminal_reason:
                    run_logger.finish_run(
                        exit_reason="recovery_terminated",
                        steps=step_index,
                        total_cost=total_cost,
                        reward=reward,
                        done=False,
                        counters={
                            "num_validation_failures": num_validation_failures,
                            "num_recovery_invocations": recovery_state.recovery_count_this_run,
                        },
                    )
                    return SolveResult(
                        reward=reward,
                        info=info,
                        messages=messages,
                        total_cost=total_cost,
                    )
                run_logger.write_trace_event({
                    "step_index": step_index,
                    "module": "recovery",
                    "event_type": "recovery_decision",
                    "failure_trigger": recovery_decision.failure_type,
                    "failure_code": recovery_decision.trace_metadata.get("failure_code"),
                    "chosen_strategy": recovery_decision.proposed_strategy,
                    "retry_key": recovery_decision.retry_key,
                    "recovery_count_this_run": recovery_state.recovery_count_this_run,
                    "terminal_reason": recovery_decision.terminal_reason,
                })
                if recovery_decision.proposed_strategy == STRATEGY_ASK_USER_CONFIRMATION:
                    su = recovery_decision.state_updates
                    recovery_state.pending_side_effect_action = su.get("set_pending_side_effect_action")
                    recovery_state.pending_confirmation_key = su.get("pending_confirmation_key") or "booking_confirmed"
                    recovery_state.pending_since_step = step_index
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
                    messages.extend([next_message, {"role": "user", "content": rejection, "source": MESSAGE_SOURCE_ORCHESTRATOR}])
                last_action = action.name
                last_observation_summary = observation_summary(rejection)
                steps = step_index
                recent_action_names = (recent_action_names + [action.name])[-3:]
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
                # Single use of confirmation: after successful execution of the just-confirmed action, clear it
                if (
                    recovery_state.retry_key_just_confirmed is not None
                    and action_retry_key(action) == recovery_state.retry_key_just_confirmed
                    and not (env_response.observation.strip().startswith("Error:"))
                ):
                    if recovery_state.confirmation_key_just_used:
                        task_state.confirmations.discard(recovery_state.confirmation_key_just_used)
                    recovery_state.retry_key_just_confirmed = None
                    recovery_state.confirmation_key_just_used = None

                # Tool execution error: invoke recovery for trace and possible hint
                if env_response.observation.strip().startswith("Error:"):
                    tool_error_input = RecoveryInput(
                        failure_type=FAILURE_TOOL_EXECUTION_ERROR,
                        action=action,
                        step_index=step_index,
                        observation=env_response.observation,
                        task_state=task_state,
                        recovery_state=recovery_state,
                        recent_action_names=recent_action_names[-3:] if recent_action_names else None,
                    )
                    tool_error_decision = decide_recovery(tool_error_input, domain=domain)
                    recovery_state.recovery_count_this_run += 1
                    run_logger.write_trace_event({
                        "step_index": step_index,
                        "module": "recovery",
                        "event_type": "recovery_decision",
                        "failure_trigger": tool_error_decision.failure_type,
                        "chosen_strategy": tool_error_decision.proposed_strategy,
                        "retry_key": tool_error_decision.retry_key,
                        "recovery_count_this_run": recovery_state.recovery_count_this_run,
                    })
                    if tool_error_decision.proposed_strategy == STRATEGY_SAFE_TERMINATE and tool_error_decision.terminal_reason:
                        run_logger.finish_run(
                            exit_reason="recovery_terminated",
                            steps=step_index,
                            total_cost=total_cost,
                            reward=reward,
                            done=False,
                            counters={
                                "num_validation_failures": num_validation_failures,
                                "num_recovery_invocations": recovery_state.recovery_count_this_run,
                            },
                        )
                        return SolveResult(
                            reward=reward,
                            info=info,
                            messages=messages,
                            total_cost=total_cost,
                        )

            last_action = action.name
            last_observation_summary = obs_summary
            done = env_response.done
            recent_action_names = (recent_action_names + [action.name])[-3:]

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
                        {"role": "user", "content": sanitize_user_observation(env_response.observation)},
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
                    counters={
                        "num_validation_failures": num_validation_failures,
                        "num_recovery_invocations": recovery_state.recovery_count_this_run,
                    },
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
            counters={
                "num_validation_failures": num_validation_failures,
                "num_recovery_invocations": recovery_state.recovery_count_this_run,
            },
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
            counters={
                "error": 1,
                "num_validation_failures": num_validation_failures,
                "num_recovery_invocations": recovery_state.recovery_count_this_run if recovery_state is not None else 0,
            },
        )
        raise
