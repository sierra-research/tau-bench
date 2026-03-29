# Copyright Sierra
# Policy Guard v1: blocks policy-invalid or premature mutating actions using TaskState.
# Placed between validator and executor: validator = action validity; policy guard = timing/precondition legality.
# Guard logic is metadata-driven: (domain, tool_name) -> requires_user_id, requires_authenticated, etc.

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

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
# Additional prereq block codes for detailed grounded state
CODE_MISSING_RESERVATION_DETAILS = "missing_reservation_details"
CODE_MISSING_ORDER_DETAILS = "missing_order_details"

# Generic business-rule code used when a more specific one is not needed.
CODE_BUSINESS_RULE_VIOLATION = "business_rule_violation"

# Metadata keys for tool policy (extend per-tool in env/tools_info or keep registry here)
REQUIRES_USER_ID = "requires_user_id"
REQUIRES_PROFILE_GROUNDED = "requires_profile_grounded"
REQUIRES_CONFIRMATION_KEY = "requires_confirmation_key"
REQUIRES_RESERVATION_CONTEXT = "requires_reservation_context"
REQUIRES_ORDER_CONTEXT = "requires_order_context"
REQUIRES_AUTHENTICATED = "requires_authenticated"
# Additional prereqs for detailed grounded state
REQUIRES_RESERVATION_DETAILS = "requires_reservation_details"
REQUIRES_ORDER_DETAILS = "requires_order_details"

# Metadata key for per-tool business rules
BUSINESS_RULES = "business_rules"

# Registry: (domain, tool_name) -> policy metadata. Single source of truth; new tools/domains add here.
POLICY_METADATA: Dict[Tuple[str, str], Dict[str, Any]] = {
    # Airline
    ("airline", "book_reservation"): {
        REQUIRES_USER_ID: True,
        REQUIRES_PROFILE_GROUNDED: True,
        REQUIRES_CONFIRMATION_KEY: "booking_confirmed",
        BUSINESS_RULES: [
            {
                "id": "max_passengers",
                "severity": "block",
                "params": {"max": 5},
            },
            {
                "id": "payment_limits",
                "severity": "block",
                "params": {"max_certificates": 1, "max_credit_cards": 1, "max_gift_cards": 3},
            },
            {
                "id": "payment_methods_in_profile",
                "severity": "block",
            },
            {
                "id": "flight_must_be_available",
                "severity": "block",
            },
        ],
    },
    ("airline", "cancel_reservation"): {
        REQUIRES_USER_ID: True,
        REQUIRES_RESERVATION_CONTEXT: True,
        REQUIRES_RESERVATION_DETAILS: True,
        BUSINESS_RULES: [
            {
                "id": "cancel_eligibility",
                "severity": "block",
            },
            {
                "id": "cancel_only_unflown_whole_trip",
                "severity": "block",
            },
        ],
    },
    ("airline", "update_reservation_flights"): {
        REQUIRES_USER_ID: True,
        REQUIRES_RESERVATION_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "flights_update_confirmed",
        REQUIRES_RESERVATION_DETAILS: True,
        BUSINESS_RULES: [
            {
                "id": "basic_economy_no_flight_change",
                "severity": "block",
            },
            {
                "id": "cabin_consistency",
                "severity": "block",
            },
            {
                "id": "insurance_no_add_after_booking",
                "severity": "block",
            },
            {
                "id": "payment_method_required_for_flight_change",
                "severity": "block",
            },
        ],
    },
    ("airline", "update_reservation_baggages"): {
        REQUIRES_USER_ID: True,
        REQUIRES_RESERVATION_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "baggage_update_confirmed",
        REQUIRES_RESERVATION_DETAILS: True,
        BUSINESS_RULES: [
            {
                "id": "baggage_only_add",
                "severity": "block",
            },
        ],
    },
    ("airline", "update_reservation_passengers"): {
        REQUIRES_USER_ID: True,
        REQUIRES_RESERVATION_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "passengers_update_confirmed",
        REQUIRES_RESERVATION_DETAILS: True,
        BUSINESS_RULES: [
            {
                "id": "passenger_count_immutable",
                "severity": "block",
            },
        ],
    },
    # Retail: auth + order context (where applicable) + explicit confirmation per policy
    ("retail", "cancel_pending_order"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_ORDER_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "cancel_order_confirmed",
        REQUIRES_ORDER_DETAILS: True,
        BUSINESS_RULES: [
            {
                "id": "order_status_required",
                "severity": "block",
                "params": {"required_status": "pending"},
            },
        ],
    },
    ("retail", "modify_pending_order_address"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_ORDER_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "address_modify_confirmed",
        REQUIRES_ORDER_DETAILS: True,
        BUSINESS_RULES: [
            {
                "id": "order_status_required",
                "severity": "block",
                "params": {"required_status": "pending"},
            },
        ],
    },
    ("retail", "modify_pending_order_items"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_ORDER_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "items_modify_confirmed",
        REQUIRES_ORDER_DETAILS: True,
        BUSINESS_RULES: [
            {
                "id": "order_status_required",
                "severity": "block",
                "params": {"required_status": "pending"},
            },
            {
                "id": "max_successful_executions_per_tool",
                "severity": "block",
                "params": {"max_successful_executions": 1},
            },
            {
                "id": "payment_method_allowed",
                "severity": "block",
            },
        ],
    },
    ("retail", "modify_pending_order_payment"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_ORDER_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "payment_modify_confirmed",
        REQUIRES_ORDER_DETAILS: True,
        BUSINESS_RULES: [
            {
                "id": "order_status_required",
                "severity": "block",
                "params": {"required_status": "pending"},
            },
            {
                "id": "payment_method_allowed",
                "severity": "block",
            },
        ],
    },
    ("retail", "modify_user_address"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_CONFIRMATION_KEY: "user_address_modify_confirmed",
    },
    ("retail", "return_delivered_order_items"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_ORDER_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "return_order_confirmed",
        REQUIRES_ORDER_DETAILS: True,
        BUSINESS_RULES: [
            {
                "id": "order_status_required",
                "severity": "block",
                "params": {"required_status": "delivered"},
            },
            {
                "id": "refund_method_allowed",
                "severity": "block",
            },
        ],
    },
    ("retail", "exchange_delivered_order_items"): {
        REQUIRES_AUTHENTICATED: True,
        REQUIRES_ORDER_CONTEXT: True,
        REQUIRES_CONFIRMATION_KEY: "exchange_order_confirmed",
        REQUIRES_ORDER_DETAILS: True,
        BUSINESS_RULES: [
            {
                "id": "order_status_required",
                "severity": "block",
                "params": {"required_status": "delivered"},
            },
            {
                "id": "max_successful_executions_per_tool",
                "severity": "block",
                "params": {"max_successful_executions": 1},
            },
            {
                "id": "payment_method_allowed",
                "severity": "block",
            },
        ],
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
    # Optional free-form warnings from non-blocking business rules.
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "code": self.code,
            "message": self.message,
            "missing_prerequisites": list(self.missing_prerequisites),
            "warnings": list(self.warnings),
        }


def _allow(msg: str = "ok", warnings: Optional[List[str]] = None) -> PolicyGuardResult:
    return PolicyGuardResult(
        allowed=True,
        code=CODE_ALLOWED,
        message=msg,
        missing_prerequisites=[],
        warnings=list(warnings or []),
    )


def _block(code: str, message: str, missing: List[str]) -> PolicyGuardResult:
    return PolicyGuardResult(
        allowed=False,
        code=code,
        message=message,
        missing_prerequisites=missing,
        warnings=[],
    )


@dataclass
class PolicyViolation:
    """
    Internal representation of a single business-rule violation.

    This is intentionally lightweight and not part of the public API; callers
    receive aggregated information via PolicyGuardResult instead.
    """

    code: str
    message: str
    missing_prerequisites: List[str]


RuleFunc = Callable[[Env, Action, TaskState, Dict[str, Any]], Optional[PolicyViolation]]


# Registry of business-rule implementations, keyed by rule id.
RULES: Dict[str, RuleFunc] = {}


def _register_rule(rule_id: str):
    """Decorator to register a business-rule implementation."""

    def decorator(func: RuleFunc) -> RuleFunc:
        RULES[rule_id] = func
        return func

    return decorator


@_register_rule("max_passengers")
def _rule_max_passengers(
    env: Env, action: Action, task_state: TaskState, params: Dict[str, Any]
) -> Optional[PolicyViolation]:
    """Enforce an upper bound on number of passengers for a booking tool."""

    max_allowed = params.get("max")
    if max_allowed is None:
        return None
    passengers = (action.kwargs or {}).get("passengers") or []
    try:
        count = len(passengers)
    except TypeError:
        return None
    if count <= max_allowed:
        return None
    return PolicyViolation(
        code="max_passengers_exceeded",
        message=f"Too many passengers: {count} > allowed maximum of {max_allowed}.",
        missing_prerequisites=[],
    )


@_register_rule("payment_limits")
def _rule_payment_limits(
    env: Env, action: Action, task_state: TaskState, params: Dict[str, Any]
) -> Optional[PolicyViolation]:
    """
    Enforce limits on number of payment methods by type for a booking tool.

    This uses simple heuristics based on payment_id prefixes, matching the
    underlying env conventions (e.g. 'certificate_', 'credit_card_', 'gift_card_').
    """

    payments = (action.kwargs or {}).get("payment_methods") or []
    if not isinstance(payments, list):
        return None

    max_cert = params.get("max_certificates")
    max_cc = params.get("max_credit_cards")
    max_gc = params.get("max_gift_cards")

    cert_count = 0
    cc_count = 0
    gc_count = 0

    for p in payments:
        pid = (p or {}).get("payment_id") or ""
        if "certificate" in pid:
            cert_count += 1
        elif "credit_card" in pid:
            cc_count += 1
        elif "gift_card" in pid:
            gc_count += 1

    violations: List[str] = []
    if max_cert is not None and cert_count > max_cert:
        violations.append(f"certificates={cert_count} > {max_cert}")
    if max_cc is not None and cc_count > max_cc:
        violations.append(f"credit_cards={cc_count} > {max_cc}")
    if max_gc is not None and gc_count > max_gc:
        violations.append(f"gift_cards={gc_count} > {max_gc}")

    if not violations:
        return None

    return PolicyViolation(
        code="payment_limits_exceeded",
        message="Payment limits exceeded: " + ", ".join(violations),
        missing_prerequisites=[],
    )


@_register_rule("payment_methods_in_profile")
def _rule_payment_methods_in_profile(
    env: Env, action: Action, task_state: TaskState, params: Dict[str, Any]
) -> Optional[PolicyViolation]:
    """
    Ensure all payment methods used are present in grounded known_payment_method_ids.
    """

    known_ids = task_state.grounded.get("known_payment_method_ids") or []
    if not known_ids:
        # If we do not know any real IDs yet, treat as non-violating; the
        # profile-grounding prereq should already be guarding this where needed.
        return None

    payments = (action.kwargs or {}).get("payment_methods") or []
    if not isinstance(payments, list):
        return None

    unknown: List[str] = []
    for p in payments:
        pid = (p or {}).get("payment_id")
        if not pid:
            continue
        if pid not in known_ids:
            unknown.append(pid)

    if not unknown:
        return None

    return PolicyViolation(
        code="unknown_payment_methods",
        message=f"Payment methods not found in grounded profile: {sorted(set(unknown))}",
        missing_prerequisites=[],
    )


@_register_rule("order_status_required")
def _rule_order_status_required(
    env: Env, action: Action, task_state: TaskState, params: Dict[str, Any]
) -> Optional[PolicyViolation]:
    """
    Enforce that an order has a required status (e.g. pending vs delivered).

    Relies on grounded order_details populated by get_order_details.
    """

    required_status = params.get("required_status")
    if not required_status:
        return None

    order_id = (action.kwargs or {}).get("order_id")
    if not order_id:
        return None

    details_by_id = task_state.grounded.get("order_details") or {}
    details = details_by_id.get(order_id)
    if not isinstance(details, dict):
        # Grounding has not happened yet; from a policy perspective we cannot
        # assert a stronger guarantee than "unknown", so treat as non-violating.
        return None

    status = details.get("status")
    if status == required_status:
        return None

    return PolicyViolation(
        code="order_status_mismatch",
        message=f"Order {order_id} has status '{status}', but '{required_status}' is required for this action.",
        missing_prerequisites=[],
    )


@_register_rule("max_successful_executions_per_tool")
def _rule_max_successful_executions_per_tool(
    env: Env, action: Action, task_state: TaskState, params: Dict[str, Any]
) -> Optional[PolicyViolation]:
    """
    Enforce an upper bound on how many times a tool may successfully execute.

    This uses generic counters stored in task_state.domain_state['policy_counters'],
    if present. If counters are absent, the rule is treated as non-violating so
    that the system degrades gracefully until counters are wired in.
    """

    max_exec = params.get("max_successful_executions")
    if max_exec is None:
        return None

    policy_counters = task_state.domain_state.get("policy_counters") or {}
    tool_counts = policy_counters.get("tool_success_count") or {}
    count = int(tool_counts.get(action.name, 0))

    if count < max_exec:
        return None

    return PolicyViolation(
        code="max_successful_executions_exceeded",
        message=(
            f"Tool '{action.name}' has already executed successfully {count} times; "
            f"maximum allowed is {max_exec}."
        ),
        missing_prerequisites=[],
    )


@_register_rule("payment_method_allowed")
def _rule_payment_method_allowed(
    env: Env, action: Action, task_state: TaskState, params: Dict[str, Any]
) -> Optional[PolicyViolation]:
    """
    Enforce basic payment-method constraints for retail order modifications/exchanges.

    This rule focuses on what can be checked with currently grounded data:
      - A new payment method must be provided.
      - For payment-modifying tools, the new payment method must differ from the
        original payment method used for the order.
    """

    order_id = (action.kwargs or {}).get("order_id")
    if not order_id:
        return None

    details_by_id = task_state.grounded.get("order_details") or {}
    details = details_by_id.get(order_id)
    if not isinstance(details, dict):
        # Defer to prereq REQUIRES_ORDER_DETAILS; if details are unavailable we do not
        # attempt to enforce business rules here.
        return None

    payment_history = details.get("payment_history") or []
    original_payment_id: Optional[str] = None
    if isinstance(payment_history, list) and payment_history:
        first = payment_history[0] or {}
        original_payment_id = first.get("payment_method_id")

    # The tools expose a single payment/refund method id in kwargs; require it.
    new_payment_id = (action.kwargs or {}).get("payment_method_id")
    if not new_payment_id or not isinstance(new_payment_id, str):
        return PolicyViolation(
            code="payment_method_missing",
            message="A payment_method_id must be provided for this action.",
            missing_prerequisites=[],
        )

    # For tools that modify payment for an order, the new method must differ from
    # the original one; exchanging like-for-like is not allowed per policy.
    if action.name in {
        "modify_pending_order_payment",
        "modify_pending_order_items",
        "exchange_delivered_order_items",
    } and original_payment_id and new_payment_id == original_payment_id:
        return PolicyViolation(
            code="payment_method_same_as_original",
            message=(
                f"New payment method {new_payment_id!r} must be different from the "
                f"original payment method {original_payment_id!r}."
            ),
            missing_prerequisites=[],
        )

    return None


@_register_rule("refund_method_allowed")
def _rule_refund_method_allowed(
    env: Env, action: Action, task_state: TaskState, params: Dict[str, Any]
) -> Optional[PolicyViolation]:
    """
    Enforce refund-method constraints for retail returns.

    For return tools, the refund must go either to the original payment method
    or to a gift card (represented by ids starting with 'gift_card_').
    """

    order_id = (action.kwargs or {}).get("order_id")
    if not order_id:
        return None

    details_by_id = task_state.grounded.get("order_details") or {}
    details = details_by_id.get(order_id)
    if not isinstance(details, dict):
        return None

    payment_history = details.get("payment_history") or []
    original_payment_id: Optional[str] = None
    if isinstance(payment_history, list) and payment_history:
        first = payment_history[0] or {}
        original_payment_id = first.get("payment_method_id")

    refund_method_id = (action.kwargs or {}).get("refund_method_id")
    if not refund_method_id or not isinstance(refund_method_id, str):
        return PolicyViolation(
            code="refund_method_missing",
            message="A refund_method_id must be provided for this action.",
            missing_prerequisites=[],
        )

    if refund_method_id == original_payment_id:
        return None
    if refund_method_id.startswith("gift_card_"):
        return None

    return PolicyViolation(
        code="refund_method_not_allowed",
        message=(
            f"Refund method {refund_method_id!r} is not allowed; it must be the "
            "original payment method or an existing gift card."
        ),
        missing_prerequisites=[],
    )


@_register_rule("flight_must_be_available")
def _rule_flight_must_be_available(
    env: Env, action: Action, task_state: TaskState, params: Dict[str, Any]
) -> Optional[PolicyViolation]:
    """
    Ensure all flights in a booking are available in the underlying env data.

    This rule is airline-specific and assumes the Env exposes a ``data`` mapping
    with a ``\"flights\"`` entry, following the standard airline env schema.
    If that structure is not present (e.g. in tests using a minimal mock env),
    the rule degrades gracefully and does not block.
    """

    # Only enforce when env exposes the canonical flights dictionary.
    flights_data = getattr(env, "data", None)
    if not isinstance(flights_data, dict):
        return None
    all_flights = flights_data.get("flights")
    if not isinstance(all_flights, dict):
        return None

    requested_flights = (action.kwargs or {}).get("flights") or []
    if not isinstance(requested_flights, list):
        return None

    unavailable: List[str] = []

    for f in requested_flights:
        if not isinstance(f, dict):
            continue
        fnum = f.get("flight_number")
        fdate = f.get("date")
        if not fnum or not isinstance(fnum, str) or not fdate or not isinstance(fdate, str):
            continue
        flight_record = all_flights.get(fnum)
        if not isinstance(flight_record, dict):
            unavailable.append(f"{fnum} on {fdate} (not found)")
            continue
        dates = flight_record.get("dates") or {}
        date_info = dates.get(fdate)
        if not isinstance(date_info, dict):
            unavailable.append(f"{fnum} on {fdate} (no data)")
            continue
        status = date_info.get("status")
        if status != "available":
            unavailable.append(f"{fnum} on {fdate} (status={status!r})")

    if not unavailable:
        return None

    return PolicyViolation(
        code="flight_unavailable",
        message=(
            "One or more requested flights are not available in the system: "
            + ", ".join(unavailable)
        ),
        missing_prerequisites=[],
    )


def evaluate_business_rules(
    env: Env,
    action: Action,
    task_state: TaskState,
    rule_specs: List[Dict[str, Any]],
) -> Tuple[Optional[PolicyGuardResult], List[str]]:
    """
    Evaluate metadata-driven business rules for a tool.

    Returns (blocking_result, warnings):
      - blocking_result: a PolicyGuardResult if any rule with severity 'block'
        fails, else None.
      - warnings: list of warning strings from rules with severity 'warn'.
    """

    warnings: List[str] = []
    for spec in rule_specs:
        rule_id = spec.get("id")
        if not rule_id:
            continue
        severity = spec.get("severity", "block")
        params = spec.get("params") or {}

        rule_fn = RULES.get(rule_id)
        if rule_fn is None:
            # Unknown rule id; ignore silently to keep metadata extensible.
            continue

        violation = rule_fn(env, action, task_state, params)
        if violation is None:
            continue

        if severity == "warn":
            warnings.append(violation.message)
            continue

        # severity == "block" (or anything else treated as blocking)
        return (
            PolicyGuardResult(
                allowed=False,
                code=violation.code or CODE_BUSINESS_RULE_VIOLATION,
                message=violation.message,
                missing_prerequisites=list(violation.missing_prerequisites),
                warnings=list(warnings),
            ),
            warnings,
        )

    return None, warnings


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
    if meta.get(REQUIRES_AUTHENTICATED):
        if not task_state.identity.authenticated:
            return _block(
                CODE_NOT_AUTHENTICATED,
                "user must be authenticated (e.g. find_user_id_by_email or find_user_id_by_name_zip) before this action",
                ["authenticated"],
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
    if meta.get(REQUIRES_RESERVATION_DETAILS):
        # Require that detailed reservation data be grounded for the focused reservation.
        # Prefer the explicit reservation_id in the action kwargs, otherwise fall back to
        # the focused reservation_id tracked in domain_state.
        reservation_details = task_state.grounded.get("reservation_details") or {}
        reservation_id = (action.kwargs or {}).get("reservation_id") or task_state.domain_state.get("reservation_id")
        if not reservation_id or reservation_id not in reservation_details:
            return _block(
                CODE_MISSING_RESERVATION_DETAILS,
                "reservation_details must be grounded (get_reservation_details) before this action",
                ["reservation_details"],
            )
    if meta.get(REQUIRES_ORDER_DETAILS):
        # Require that detailed order data be grounded for the focused order.
        order_details = task_state.grounded.get("order_details") or {}
        order_id = (action.kwargs or {}).get("order_id") or task_state.domain_state.get("order_id")
        if not order_id or order_id not in order_details:
            return _block(
                CODE_MISSING_ORDER_DETAILS,
                "order_details must be grounded (get_order_details) before this action",
                ["order_details"],
            )
    if meta.get(REQUIRES_CONFIRMATION_KEY):
        key = meta[REQUIRES_CONFIRMATION_KEY]
        if key not in task_state.confirmations:
            return _block(
                CODE_MISSING_CONFIRMATION,
                "explicit user confirmation required before this action",
                [key],
            )

    # After prerequisite checks pass, apply any metadata-driven business rules.
    rule_specs = meta.get(BUSINESS_RULES) or []
    if rule_specs:
        blocking_result, warnings = evaluate_business_rules(
            env=env,
            action=action,
            task_state=task_state,
            rule_specs=rule_specs,
        )
        if blocking_result is not None:
            return blocking_result
        if warnings:
            # Allowed, but include warnings in the result for logging/tracing.
            return _allow(warnings=warnings)

    return _allow()
