# Copyright Sierra
# Shared TaskState for Phase 3 orchestration. Created at run entry, updated each step.
# Supports policy guard, planner, validator grounding, recovery, memory compression.
# Domain-agnostic core + domain-specific substate for airline and retail.
#
# Grounded state schema (populated only from tool results via orchestration/grounding.py):
#   grounded["user_id"]: str | None - established by get_user_details success or find_user_id_by_* (retail)
#   grounded["user_profile"]: dict | None - normalized profile (dob, payment_method_ids, membership, reservations/orders)
#   grounded["known_payment_method_ids"]: List[str] - real system IDs from profile (e.g. credit_card_4421486)
#   grounded["reservation_ids"]: List[str] - airline; from user_profile or get_reservation_details
#   grounded["order_ids"]: List[str] - retail; from user_profile or get_order_details
#   grounded["reservation_details"]: dict - keyed by reservation_id when get_reservation_details used
#   grounded["order_details"]: dict - keyed by order_id when get_order_details used

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

# Avoid circular import: accept Task as Any (tau_bench.types.Task)
TaskLike = Any


@dataclass
class IntentState:
    """Current intent: task kind, objective, constraints, unresolved slots, status."""
    task_kind: Optional[str] = None
    current_objective: Optional[str] = None
    unresolved_slots: List[str] = field(default_factory=list)
    status: str = "in_progress"
    initial_instruction: Optional[str] = None


@dataclass
class IdentityState:
    """Identity/authentication state. Safe defaults: not authenticated until established."""
    user_id: Optional[str] = None
    authenticated: bool = False
    auth_method: Optional[str] = None  # e.g. "email", "name_zip"
    profile_grounded: bool = False


@dataclass
class ChecklistState:
    """Policy-relevant prerequisites and milestones. Planner can fill/evolve."""
    required_prerequisites: List[str] = field(default_factory=list)
    completed_milestones: List[str] = field(default_factory=list)
    pending: List[str] = field(default_factory=list)
    next_step_candidates: List[str] = field(default_factory=list)
    version: int = 0


@dataclass
class TaskState:
    """
    Shared orchestration state per run/session. One instance per run_orchestrated_loop.
    Read/updated by proposer, planner, policy guard, validator, executor, recovery, memory.
    """
    domain: str
    intent: IntentState = field(default_factory=IntentState)
    identity: IdentityState = field(default_factory=IdentityState)
    grounded: Dict[str, Any] = field(default_factory=dict)  # tool-derived facts; see module doc for schema
    candidates: Optional[Dict[str, Any]] = None  # current working candidates
    selected: Optional[Dict[str, Any]] = None  # current selected choice
    confirmations: Set[str] = field(default_factory=set)  # e.g. "booking_confirmed"
    progress: Optional[Dict[str, Any]] = None  # checkpoints / last milestone
    checklist: ChecklistState = field(default_factory=ChecklistState)
    last_tool_result: Optional[str] = None
    last_error: Optional[str] = None
    scratchpad_summary: Optional[str] = None
    domain_state: Dict[str, Any] = field(default_factory=dict)

    def set_user_id(self, user_id: str) -> None:
        self.identity.user_id = user_id

    def set_authenticated(self, method: Optional[str] = None) -> None:
        self.identity.authenticated = True
        if method is not None:
            self.identity.auth_method = method

    def set_profile_grounded(self, grounded: bool = True) -> None:
        self.identity.profile_grounded = grounded

    def add_grounded(self, key: str, value: Any) -> None:
        self.grounded[key] = value

    def mark_prerequisite_done(self, name: str) -> None:
        if name in self.checklist.required_prerequisites:
            self.checklist.completed_milestones.append(name)
            self.checklist.required_prerequisites = [
                p for p in self.checklist.required_prerequisites if p != name
            ]
        self.checklist.version += 1

    def add_confirmation(self, name: str) -> None:
        self.confirmations.add(name)

    def set_last_error(self, message: str) -> None:
        self.last_error = message

    def set_last_tool_result(self, result: str) -> None:
        self.last_tool_result = result
        self.last_error = None  # clear error when we have a new result

    def update_after_step(self, action_name: str, observation: str) -> None:
        """Update last_tool_result / last_error from executor observation."""
        if observation.strip().startswith("Error:"):
            self.last_error = observation
            self.last_tool_result = None
        else:
            self.last_tool_result = observation
            self.last_error = None


def _default_domain_state(domain: str) -> Dict[str, Any]:
    """Default domain_state shape for airline and retail. Populated by grounding layer from tool results."""
    if domain == "airline":
        return {
            "reservation_id": None,
            "booking_flow_stage": None,  # search | select | confirm | none
            "payment_methods_from_profile": [],  # real IDs from get_user_details
            "selected_itinerary": None,
            "policy_counters": {
                # Generic counters used by policy guard business rules. Keys are
                # domain-agnostic (e.g. "tool_success_count").
                "tool_success_count": {},
            },
        }
    if domain == "retail":
        return {
            "order_id": None,
            "auth_method_used": None,  # email | name_zip | none
            "user_id_from_lookup": None,  # from find_user_id_by_email / find_user_id_by_name_zip
            "policy_counters": {
                "tool_success_count": {},
            },
        }
    return {
        "policy_counters": {
            "tool_success_count": {},
        },
    }


def create_initial_task_state(
    domain: str,
    task: TaskLike,
    initial_observation: Optional[str] = None,
) -> TaskState:
    """
    Create TaskState at run entry (after env.reset). Safe defaults; no assumption of auth or grounding.
    """
    intent = IntentState(initial_instruction=getattr(task, "instruction", None))
    state = TaskState(
        domain=domain,
        intent=intent,
        identity=IdentityState(),
        checklist=ChecklistState(),
        domain_state=_default_domain_state(domain),
    )
    # Do not set identity.user_id or authenticated/profile_grounded from task; those are established by tools/conversation.
    return state
