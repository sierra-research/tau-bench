# Copyright Sierra
# Grounding layer: extract reusable facts from tool results into TaskState.
# Handler selection is driven by env.tools_info / explicit registry; no hard-coded prompts.
# Supports airline and retail; only authoritative tool results are grounded.

import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from tau_bench.envs.base import Env
from tau_bench.orchestration.task_state import TaskState
from tau_bench.types import Action


# Result types for grounding dispatch
RESULT_TYPE_USER_PROFILE = "user_profile"
RESULT_TYPE_USER_ID_LOOKUP = "user_id_lookup"
RESULT_TYPE_RESERVATION_DETAILS = "reservation_details"
RESULT_TYPE_ORDER_DETAILS = "order_details"

# Map: tool_name -> auth_method for user_id_lookup extractors (avoids substring in action.name).
USER_ID_LOOKUP_AUTH_METHOD: Dict[str, str] = {
    "find_user_id_by_email": "email",
    "find_user_id_by_name_zip": "name_zip",
}

# Registry: (domain, tool_name) -> result_type. Extend when new envs/tools are added.
# Keeps handler selection in code, not prompts; tools can vary by env.
_TOOL_RESULT_TYPE_REGISTRY: List[Tuple[str, str, str]] = [
    ("airline", "get_user_details", RESULT_TYPE_USER_PROFILE),
    ("retail", "get_user_details", RESULT_TYPE_USER_PROFILE),
    ("retail", "find_user_id_by_email", RESULT_TYPE_USER_ID_LOOKUP),
    ("retail", "find_user_id_by_name_zip", RESULT_TYPE_USER_ID_LOOKUP),
    ("airline", "get_reservation_details", RESULT_TYPE_RESERVATION_DETAILS),
    ("retail", "get_order_details", RESULT_TYPE_ORDER_DETAILS),
]


def _get_result_type(domain: str, action_name: str) -> Optional[str]:
    """Return result type for (domain, action_name), or None if no handler."""
    for d, name, rtype in _TOOL_RESULT_TYPE_REGISTRY:
        if d == domain and name == action_name:
            return rtype
    return None


def _extract_user_profile(
    observation: str, action: Action, task_state: TaskState
) -> None:
    """Parse get_user_details JSON; update grounded, identity, domain_state. Preserve real IDs."""
    try:
        data = json.loads(observation)
    except (json.JSONDecodeError, TypeError):
        return
    if not isinstance(data, dict):
        return

    user_id = (action.kwargs or {}).get("user_id")
    if not user_id or not isinstance(user_id, str):
        return

    # Payment method IDs: real system IDs from the profile
    payment_methods = data.get("payment_methods") or {}
    if isinstance(payment_methods, dict):
        payment_ids = list(payment_methods.keys())
    else:
        payment_ids = []

    # Normalized user_profile for reuse
    profile: Dict[str, Any] = {
        "dob": data.get("dob"),
        "payment_method_ids": payment_ids,
        "membership": data.get("membership"),  # airline
        "reservations": data.get("reservations") if isinstance(data.get("reservations"), list) else [],
        "orders": data.get("orders") if isinstance(data.get("orders"), list) else [],
    }

    task_state.grounded["user_id"] = user_id
    task_state.grounded["user_profile"] = profile
    task_state.grounded["known_payment_method_ids"] = payment_ids
    task_state.identity.user_id = user_id
    task_state.identity.profile_grounded = True

    if task_state.domain == "airline":
        task_state.domain_state["payment_methods_from_profile"] = payment_ids
        task_state.grounded["reservation_ids"] = profile.get("reservations") or []
    elif task_state.domain == "retail":
        task_state.grounded["order_ids"] = profile.get("orders") or []
        task_state.domain_state["payment_methods_from_profile"] = payment_ids


def _extract_user_id_lookup(
    observation: str, action: Action, task_state: TaskState
) -> None:
    """Parse find_user_id_by_* result; set identity and grounded user_id. Only on success."""
    obs = observation.strip()
    if obs.startswith("Error:"):
        return
    # Success: plain user_id string
    user_id = obs
    if not user_id:
        return

    task_state.grounded["user_id"] = user_id
    task_state.identity.user_id = user_id
    task_state.identity.authenticated = True
    task_state.identity.auth_method = USER_ID_LOOKUP_AUTH_METHOD.get(action.name)
    if task_state.domain == "retail":
        task_state.domain_state["user_id_from_lookup"] = user_id
        task_state.domain_state["auth_method_used"] = task_state.identity.auth_method


def _extract_reservation_details(
    observation: str, action: Action, task_state: TaskState
) -> None:
    """Parse get_reservation_details JSON; store in grounded and domain_state."""
    try:
        data = json.loads(observation)
    except (json.JSONDecodeError, TypeError):
        return
    if not isinstance(data, dict):
        return

    reservation_id = (action.kwargs or {}).get("reservation_id")
    if not reservation_id or not isinstance(reservation_id, str):
        return

    if "reservation_details" not in task_state.grounded:
        task_state.grounded["reservation_details"] = {}
    task_state.grounded["reservation_details"][reservation_id] = data
    task_state.domain_state["reservation_id"] = reservation_id
    if "reservation_ids" not in task_state.grounded:
        task_state.grounded["reservation_ids"] = []
    if reservation_id not in task_state.grounded["reservation_ids"]:
        task_state.grounded["reservation_ids"].append(reservation_id)


def _extract_order_details(
    observation: str, action: Action, task_state: TaskState
) -> None:
    """Parse get_order_details JSON; store in grounded and domain_state."""
    try:
        data = json.loads(observation)
    except (json.JSONDecodeError, TypeError):
        return
    if not isinstance(data, dict):
        return

    order_id = (action.kwargs or {}).get("order_id")
    if not order_id or not isinstance(order_id, str):
        return

    if "order_details" not in task_state.grounded:
        task_state.grounded["order_details"] = {}
    task_state.grounded["order_details"][order_id] = data
    task_state.domain_state["order_id"] = order_id
    if "order_ids" not in task_state.grounded:
        task_state.grounded["order_ids"] = []
    if order_id not in task_state.grounded["order_ids"]:
        task_state.grounded["order_ids"].append(order_id)


_EXTRACTORS: Dict[str, Callable[[str, Action, TaskState], None]] = {
    RESULT_TYPE_USER_PROFILE: _extract_user_profile,
    RESULT_TYPE_USER_ID_LOOKUP: _extract_user_id_lookup,
    RESULT_TYPE_RESERVATION_DETAILS: _extract_reservation_details,
    RESULT_TYPE_ORDER_DETAILS: _extract_order_details,
}


def apply_grounding(
    env: Env,
    domain: str,
    action: Action,
    observation: str,
    task_state: TaskState,
) -> None:
    """
    If the executed action has a grounding handler, parse the observation and update
    task_state.grounded, identity, and domain_state. Only tool results are grounded;
    error observations are skipped. Uses action.name and action.kwargs for context.
    """
    if not observation or not observation.strip():
        return
    if observation.strip().startswith("Error:"):
        return
    # Only ground tools that exist in this env
    if action.name not in getattr(env, "tools_map", {}):
        return

    result_type = _get_result_type(domain, action.name)
    if result_type is None:
        return
    extractor = _EXTRACTORS.get(result_type)
    if extractor is None:
        return
    extractor(observation, action, task_state)


def build_grounded_facts_summary(task_state: TaskState) -> str:
    """
    Build a short, tool-name-free summary of grounded state for LLM context.
    Use when injecting state into messages so the model can reason with "what we know".
    """
    parts: List[str] = []
    uid = task_state.grounded.get("user_id")
    parts.append(f"user_id={uid if uid else 'not yet established'}")
    parts.append(f"profile_grounded={task_state.identity.profile_grounded}")
    payment_ids = task_state.grounded.get("known_payment_method_ids") or []
    if payment_ids:
        parts.append(f"known_payment_ids={payment_ids}")
    else:
        parts.append("known_payment_ids=none")
    if task_state.domain == "airline":
        rids = task_state.grounded.get("reservation_ids") or []
        parts.append(f"reservation_ids={rids}")
    elif task_state.domain == "retail":
        oids = task_state.grounded.get("order_ids") or []
        parts.append(f"order_ids={oids}")
    return "Grounded facts: " + "; ".join(parts)
