# Copyright Sierra
# Policy Guard v1: blocks policy-invalid or premature mutating actions using TaskState.
# Placed between validator and executor: validator = action validity; policy guard = timing/precondition legality.
# Guard logic is metadata-driven: (domain, tool_name) -> requires_user_id, requires_authenticated, etc.

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from tau_bench.envs.base import Env
from tau_bench.orchestration.task_state import TaskState
from tau_bench.types import Action, RESPOND_ACTION_NAME


# Block codes (machine-usable for recovery)
CODE_ALLOWED = "allowed"
CODE_MISSING_USER_ID = "missing_user_id"
CODE_NOT_AUTHENTICATED = "not_authenticated"
CODE_MISSING_PROFILE_GROUNDING = "missing_profile_grounding"
CODE_MISSING_CONFIRMATION = "missing_confirmation"
CODE_MISSING_RESERVATION_CONTEXT = "missing_reservation_context"
CODE_MISSING_ORDER_CONTEXT = "missing_order_context"

# Metadata keys for tool policy (extend per-tool in env/tools_info or keep registry here)
REQUIRES_USER_ID = "requires_user_id"
REQUIRES_PROFILE_GROUNDED = "requires_profile_grounded"
REQUIRES_CONFIRMATION_KEY = "requires_confirmation_key"
REQUIRES_RESERVATION_CONTEXT = "requires_reservation_context"
REQUIRES_ORDER_CONTEXT = "requires_order_context"
REQUIRES_AUTHENTICATED = "requires_authenticated"

# Registry: (domain, tool_name) -> policy metadata. Single source of truth; new tools/domains add here.
POLICY_METADATA: Dict[Tuple[str, str], Dict[str, Any]] = {
    # Airline
    ("airline", "book_reservation"): {
        REQUIRES_USER_ID: True,
        REQUIRES_PROFILE_GROUNDED: True,
        REQUIRES_CONFIRMATION_KEY: "booking_confirmed",
    },
    ("airline", "cancel_reservation"): {
        REQUIRES_USER_ID: True,
        REQUIRES_RESERVATION_CONTEXT: True,
    },
    ("airline", "update_reservation_flights"): {
        REQUIRES_USER_ID: True,
        REQUIRES_RESERVATION_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "flights_update_confirmed",
    },
    ("airline", "update_reservation_baggages"): {
        REQUIRES_USER_ID: True,
        REQUIRES_RESERVATION_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "baggage_update_confirmed",
    },
    ("airline", "update_reservation_passengers"): {
        REQUIRES_USER_ID: True,
        REQUIRES_RESERVATION_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "passengers_update_confirmed",
    },
    # Retail: auth + order context (where applicable) + explicit confirmation per policy
    ("retail", "cancel_pending_order"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_ORDER_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "cancel_order_confirmed",
    },
    ("retail", "modify_pending_order_address"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_ORDER_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "address_modify_confirmed",
    },
    ("retail", "modify_pending_order_items"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_ORDER_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "items_modify_confirmed",
    },
    ("retail", "modify_pending_order_payment"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_ORDER_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "payment_modify_confirmed",
    },
    ("retail", "modify_user_address"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_CONFIRMATION_KEY: "user_address_modify_confirmed",
    },
    ("retail", "return_delivered_order_items"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_ORDER_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "return_order_confirmed",
    },
    ("retail", "exchange_delivered_order_items"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_ORDER_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "exchange_order_confirmed",
    },
}

# Legacy sets (kept for recovery module and tests); derived from POLICY_METADATA for consistency
AIRLINE_GUARDED_ACTIONS = frozenset(
    name for (d, name) in POLICY_METADATA if d == "airline"
)
RETAIL_GUARDED_ACTIONS = frozenset(
    name for (d, name) in POLICY_METADATA if d == "retail"
)
BOOKING_CONFIRMATION_KEY = "booking_confirmed"


def get_tool_policy_metadata(domain: str, tool_name: str) -> Dict[str, Any]:
    """Return policy metadata for (domain, tool_name). Empty dict = no guard requirements."""
    return POLICY_METADATA.get((domain, tool_name), {}).copy()


def get_tools_requiring_confirmation(domain: str) -> Set[str]:
    """Tool names that require a confirmation key (for recovery ASK_USER_CONFIRMATION)."""
    return {
        name for (d, name), meta in POLICY_METADATA.items()
        if d == domain and meta.get(REQUIRES_CONFIRMATION_KEY)
    }


@dataclass(frozen=True)
class PolicyGuardResult:
    """Structured policy guard output for logging and recovery."""
    allowed: bool
    code: str
    message: str
    missing_prerequisites: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "code": self.code,
            "message": self.message,
            "missing_prerequisites": list(self.missing_prerequisites),
        }


def _allow(msg: str = "ok") -> PolicyGuardResult:
    return PolicyGuardResult(allowed=True, code=CODE_ALLOWED, message=msg, missing_prerequisites=[])


def _block(code: str, message: str, missing: List[str]) -> PolicyGuardResult:
    return PolicyGuardResult(allowed=False, code=code, message=message, missing_prerequisites=missing)


def check_policy(env: Env, action: Action, task_state: TaskState) -> PolicyGuardResult:
    """
    Check whether the action is allowed given current policy-relevant state.
    Uses POLICY_METADATA; if metadata absent, allow. Validator handles unknown tools.
    """
    if action.name == RESPOND_ACTION_NAME:
        return _allow("respond allowed")

    domain = task_state.domain
    meta = get_tool_policy_metadata(domain, action.name)
    if not meta:
        return _allow()

    if meta.get(REQUIRES_USER_ID):
        if not task_state.identity.user_id or not task_state.identity.user_id.strip():
            return _block(
                CODE_MISSING_USER_ID,
                "user_id must be established (e.g. via get_user_details) before this action",
                ["user_id"],
            )
    if meta.get(REQUIRES_PROFILE_GROUNDED):
        if not task_state.identity.profile_grounded:
            return _block(
                CODE_MISSING_PROFILE_GROUNDING,
                "profile must be grounded (get_user_details) before this action",
                ["profile_grounded"],
            )
    if meta.get(REQUIRES_CONFIRMATION_KEY):
        key = meta[REQUIRES_CONFIRMATION_KEY]
        if key not in task_state.confirmations:
            return _block(
                CODE_MISSING_CONFIRMATION,
                "explicit user confirmation required before this action",
                [key],
            )
    if meta.get(REQUIRES_RESERVATION_CONTEXT):
        rids = task_state.grounded.get("reservation_ids") or []
        focused_rid = task_state.domain_state.get("reservation_id")
        if not (rids or focused_rid):
            return _block(
                CODE_MISSING_RESERVATION_CONTEXT,
                "reservation_id must be established (e.g. via get_user_details or get_reservation_details) before this action",
                ["reservation_context"],
            )
    if meta.get(REQUIRES_ORDER_CONTEXT):
        oids = task_state.grounded.get("order_ids") or []
        focused_oid = task_state.domain_state.get("order_id")
        if not (oids or focused_oid):
            return _block(
                CODE_MISSING_ORDER_CONTEXT,
                "order_id must be established (e.g. via get_user_details or get_order_details) before this action",
                ["order_context"],
            )
    if meta.get(REQUIRES_AUTHENTICATED):
        if not task_state.identity.authenticated:
            return _block(
                CODE_NOT_AUTHENTICATED,
                "user must be authenticated (e.g. find_user_id_by_email or find_user_id_by_name_zip) before this action",
                ["authenticated"],
            )
    return _allow()
