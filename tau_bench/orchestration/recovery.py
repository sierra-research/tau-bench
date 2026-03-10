# Copyright Sierra
# Recovery module: failure categories, recovery decisions, and state.
# Run_loop calls decide_recovery on validator/policy failure (and later tool error);
# applies state_updates and loop behavior per RecoveryDecision.

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from tau_bench.types import Action
from tau_bench.orchestration.validator import ValidatorResult
from tau_bench.orchestration.policy_guard import (
    PolicyGuardResult,
    CODE_MISSING_CONFIRMATION,
    get_tools_requiring_confirmation,
)

# Failure categories (observable outcomes)
FAILURE_VALIDATION_ERROR = "validation_error"
FAILURE_POLICY_BLOCK = "policy_block"
FAILURE_MISSING_REQUIRED_USER_CONFIRMATION = "missing_required_user_confirmation"
FAILURE_TOOL_EXECUTION_ERROR = "tool_execution_error"
FAILURE_NO_PROGRESS = "no_progress"
FAILURE_REPEATED_SAME_ACTION = "repeated_same_action"
FAILURE_REPEATED_FAILURE_AFTER_REPAIR = "repeated_failure_after_repair"
FAILURE_BUDGET_RISK = "budget_risk_or_turn_limit_risk"

# Recovery strategies
STRATEGY_RETRY_SAME_ACTION = "RETRY_SAME_ACTION"
STRATEGY_RETRY_REPAIRED_ACTION = "RETRY_REPAIRED_ACTION"
STRATEGY_ASK_USER_CONFIRMATION = "ASK_USER_CONFIRMATION"
STRATEGY_ASK_CLARIFYING_QUESTION = "ASK_CLARIFYING_QUESTION"
STRATEGY_REPLAN_FROM_STATE = "REPLAN_FROM_STATE"
STRATEGY_SAFE_TERMINATE = "SAFE_TERMINATE"


# Affirmative and negative phrases for confirmation heuristic (replaceable by LLM later)
_AFFIRMATIVE_SUBSTRINGS = ("yes", "confirm", "go ahead", "please do", "ok", "sure", "proceed", "do it")
_NEGATIVE_SUBSTRINGS = ("no", "don't", "dont", "cancel", "wait", "stop", "never mind")


def check_confirmation_heuristic(user_content: str, pending_confirmation_key: str) -> bool:
    """
    Return True if user_content appears to affirm the pending confirmation.
    Simple substring check: any affirmative and no strong negative. Replaceable by LLM behind same interface.
    """
    if not user_content or not isinstance(user_content, str):
        return False
    lower = user_content.strip().lower()
    if not lower:
        return False
    has_negative = any(n in lower for n in _NEGATIVE_SUBSTRINGS)
    if has_negative:
        return False
    return any(a in lower for a in _AFFIRMATIVE_SUBSTRINGS)


def action_retry_key(action: Action) -> str:
    """Deterministic fingerprint for retry counting (same action + kwargs -> same key)."""
    parts = [action.name]
    if isinstance(action.kwargs, dict) and action.kwargs:
        parts.append(json.dumps(sorted(action.kwargs.items()), sort_keys=True))
    return "|".join(parts)


@dataclass
class RecoveryState:
    """Per-run recovery state: pending action, retry counts, recovery budget."""
    pending_side_effect_action: Optional[Action] = None
    pending_confirmation_key: Optional[str] = None
    pending_since_step: int = 0
    retry_counts: Dict[str, int] = field(default_factory=dict)
    failure_type_counts: Dict[str, int] = field(default_factory=dict)
    recovery_count_this_run: int = 0
    # After confirmation satisfied, allow one execution of this retry_key then clear confirmation
    retry_key_just_confirmed: Optional[str] = None
    confirmation_key_just_used: Optional[str] = None


@dataclass
class RecoveryInput:
    """Input to decide_recovery: failure type, source result, action, step, state refs."""
    failure_type: str
    action: Action
    step_index: int
    validator_result: Optional[ValidatorResult] = None
    policy_result: Optional[PolicyGuardResult] = None
    observation: Optional[str] = None
    task_state: Any = None  # TaskState ref for reading; run_loop applies updates
    recovery_state: Optional[RecoveryState] = None
    recent_action_names: Optional[List[str]] = None  # last N action names for no_progress / repeated_same_action


@dataclass(frozen=True)
class RecoveryDecision:
    """Output of decide_recovery; run_loop applies state_updates and controls loop."""
    failure_type: str
    diagnosis: str
    confidence: float
    recoverable: bool
    proposed_strategy: str
    message_to_user: Optional[str] = None
    repaired_action: Optional[Action] = None
    replanning_hint: Optional[str] = None
    state_updates: Dict[str, Any] = field(default_factory=dict)
    retry_allowed: bool = False
    retry_key: Optional[str] = None
    retry_budget_cost: int = 1
    terminal_reason: Optional[str] = None
    trace_metadata: Dict[str, Any] = field(default_factory=dict)




def decide_recovery(
    inp: RecoveryInput,
    domain: str,
    max_recovery_per_run: int = 10,
    max_retries_per_action: int = 2,
) -> RecoveryDecision:
    """
    Decide recovery strategy for a failure. Applies retry budgets, repeated_same_action, and strategy selection.
    Run_loop logs the decision and applies state_updates.
    """
    recovery_state = inp.recovery_state or RecoveryState()
    retry_key = action_retry_key(inp.action)
    trace_meta: Dict[str, Any] = {
        "failure_code": None,
        "missing_prerequisites": [],
        "recovery_count": recovery_state.recovery_count_this_run,
    }

    # Budget exhausted
    if recovery_state.recovery_count_this_run >= max_recovery_per_run:
        return RecoveryDecision(
            failure_type=FAILURE_BUDGET_RISK,
            diagnosis="Recovery budget exhausted",
            confidence=1.0,
            recoverable=False,
            proposed_strategy=STRATEGY_SAFE_TERMINATE,
            terminal_reason="max_recovery_per_run",
            retry_key=retry_key,
            trace_metadata={**trace_meta, "recovery_count": recovery_state.recovery_count_this_run},
        )

    # Repeated same action while pending confirmation (do not burn retry count)
    if (
        recovery_state.pending_side_effect_action is not None
        and action_retry_key(recovery_state.pending_side_effect_action) == retry_key
    ):
        return RecoveryDecision(
            failure_type=FAILURE_REPEATED_SAME_ACTION,
            diagnosis="Same action blocked again; waiting for user confirmation",
            confidence=1.0,
            recoverable=True,
            proposed_strategy=STRATEGY_REPLAN_FROM_STATE,
            replanning_hint="Ask the user to confirm before proceeding.",
            retry_key=retry_key,
            trace_metadata=trace_meta,
        )

    # Retry count for this action
    recovery_state.retry_counts[retry_key] = recovery_state.retry_counts.get(retry_key, 0) + 1
    if recovery_state.retry_counts[retry_key] > max_retries_per_action:
        return RecoveryDecision(
            failure_type=FAILURE_REPEATED_SAME_ACTION,
            diagnosis=f"Max retries ({max_retries_per_action}) exceeded for this action",
            confidence=1.0,
            recoverable=False,
            proposed_strategy=STRATEGY_SAFE_TERMINATE,
            terminal_reason="max_retries_per_action",
            retry_key=retry_key,
            trace_metadata=trace_meta,
        )

    # No progress: last N steps same action
    recent = inp.recent_action_names or []
    if len(recent) >= 3 and all(n == inp.action.name for n in recent[-3:]):
        return RecoveryDecision(
            failure_type=FAILURE_NO_PROGRESS,
            diagnosis="Same action repeated without progress",
            confidence=1.0,
            recoverable=True,
            proposed_strategy=STRATEGY_REPLAN_FROM_STATE,
            replanning_hint="Try a different approach or gather more information.",
            retry_key=retry_key,
            trace_metadata=trace_meta,
        )

    if inp.failure_type == FAILURE_VALIDATION_ERROR and inp.validator_result:
        trace_meta["failure_code"] = inp.validator_result.code
        return RecoveryDecision(
            failure_type=FAILURE_VALIDATION_ERROR,
            diagnosis=f"Validation failed: {inp.validator_result.message}",
            confidence=1.0,
            recoverable=True,
            proposed_strategy=STRATEGY_REPLAN_FROM_STATE,
            replanning_hint=inp.validator_result.message,
            retry_key=retry_key,
            trace_metadata=trace_meta,
        )

    if inp.failure_type == FAILURE_POLICY_BLOCK and inp.policy_result:
        trace_meta["failure_code"] = inp.policy_result.code
        trace_meta["missing_prerequisites"] = list(inp.policy_result.missing_prerequisites)
        tools_requiring_confirmation = get_tools_requiring_confirmation(domain)
        if (
            inp.policy_result.code == CODE_MISSING_CONFIRMATION
            and inp.action.name in tools_requiring_confirmation
        ):
            # Require user confirmation before side-effecting action; run_loop will set pending and wait.
            pending_key = (
                inp.policy_result.missing_prerequisites[0]
                if inp.policy_result.missing_prerequisites
                else "booking_confirmed"
            )
            return RecoveryDecision(
                failure_type=FAILURE_MISSING_REQUIRED_USER_CONFIRMATION,
                diagnosis=f"Policy blocked: {inp.policy_result.message}",
                confidence=1.0,
                recoverable=True,
                proposed_strategy=STRATEGY_ASK_USER_CONFIRMATION,
                message_to_user="Please confirm you want to proceed.",
                state_updates={
                    "set_pending_side_effect_action": inp.action,
                    "pending_confirmation_key": pending_key,
                },
                retry_key=retry_key,
                trace_metadata=trace_meta,
            )
        return RecoveryDecision(
            failure_type=FAILURE_POLICY_BLOCK,
            diagnosis=f"Policy blocked: {inp.policy_result.message}",
            confidence=1.0,
            recoverable=True,
            proposed_strategy=STRATEGY_REPLAN_FROM_STATE,
            replanning_hint=inp.policy_result.message,
            retry_key=retry_key,
            trace_metadata=trace_meta,
        )

    # Tool execution error (observation starts with "Error:")
    if inp.failure_type == FAILURE_TOOL_EXECUTION_ERROR:
        obs_preview = (inp.observation or "")[:200].strip()
        return RecoveryDecision(
            failure_type=FAILURE_TOOL_EXECUTION_ERROR,
            diagnosis=f"Tool execution failed: {obs_preview}",
            confidence=1.0,
            recoverable=True,
            proposed_strategy=STRATEGY_REPLAN_FROM_STATE,
            message_to_user=None,
            replanning_hint="Check the error message and try a different approach or correct the inputs.",
            retry_key=retry_key,
            trace_metadata={**trace_meta, "observation_preview": obs_preview},
        )

    # Fallback
    return RecoveryDecision(
        failure_type=inp.failure_type,
        diagnosis="Unhandled failure",
        confidence=0.0,
        recoverable=False,
        proposed_strategy=STRATEGY_SAFE_TERMINATE,
        terminal_reason="recovery_stub_unhandled",
        retry_key=retry_key,
        trace_metadata=trace_meta,
    )
