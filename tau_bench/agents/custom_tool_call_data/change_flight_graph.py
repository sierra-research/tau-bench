from cashier.graph.conversation_node import ConversationNodeSchema
from cashier.graph.base.base_state import BaseStateModel
from cashier.graph.edge_schema import EdgeSchema
from cashier.graph.base.base_edge_schema import (
    StateTransitionConfig,
)
from cashier.graph.graph_schema import GraphSchema
from typing import Optional, List, Dict
from tau_bench.agents.custom_tool_call_data.types import (
    CabinType,
    FlightInfo,
    FlightReservationInfo,
    FlightType,
    PassengerInfo,
    PaymentDetails,
    PaymentMethod,
    InsuranceValue,
    UserDetails,
)
from tau_bench.agents.custom_tool_call_data.prompts import AirlineNodeSystemPrompt
from pydantic import Field, BaseModel
from tau_bench.agents.custom_tool_call_data.tool_registry import AIRLINE_TOOL_REGISTRY
from tau_bench.agents.custom_tool_call_data.types import ReservationDetails

## book flight graph

PREAMBLE = "You are helping the customer to change flight/s. "


class UserState(BaseStateModel):
    user_details: Optional[UserDetails] = None


get_user_id_node_schema = ConversationNodeSchema(
    node_prompt=PREAMBLE + "Right now, you need to get their user details.",
    node_system_prompt=AirlineNodeSystemPrompt,
    input_schema=None,
    state_schema=UserState,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=["get_user_details", "calculate"],
)

# ---------------------------------------------------------


class UserInput(BaseModel):
    user_details: UserDetails


class ReservationDetailsState(BaseStateModel):
    reservation_details: Optional[ReservationDetails] = None


get_reservation_details_node_schema = ConversationNodeSchema(
    node_prompt=PREAMBLE
    + "Right now, you need to get the reservation details by asking for the reservation id. If they don't know the id, lookup each reservation in their user details and find the one that best matches their description .",
    node_system_prompt=AirlineNodeSystemPrompt,
    input_schema=UserInput,
    state_schema=ReservationDetailsState,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=[
        "get_reservation_details",
        "calculate",
        "list_all_airports",
    ],
)


# ---------------------------------------------------------


class OrderInput1(BaseModel):
    user_details: UserDetails
    reservation_details: ReservationDetails


class FlightOrder(BaseStateModel):
    flight_infos: List[FlightInfo] = Field(
        default_factory=list,
        descripion="An array of objects containing details about each piece of flight in the ENTIRE new reservation. Even if the a flight segment is not changed, it should still be included in the array.",
    )


find_flight_node_schema = ConversationNodeSchema(
    node_prompt=PREAMBLE
    + (
        "Right now, you need to help find new flights for them. The customer can change anything from a single flight segment to all the flights. "
        "Remember, basic economy flights cannot be modified. Other reservations can be modified without changing the origin, destination, and trip type."
    ),
    node_system_prompt=AirlineNodeSystemPrompt,
    input_schema=OrderInput1,
    state_schema=FlightOrder,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=[
        "search_direct_flight",
        "search_onestop_flight",
        "list_all_airports",
        "calculate",
    ],
)


# ------------------------------------------------------------------
class OrderInput2(BaseModel):
    user_details: UserDetails
    reservation_details: ReservationDetails
    flight_infos: List[FlightInfo]


class PaymentOrder(BaseStateModel):
    payment_id: Optional[str] = None


get_payment_node_schema = ConversationNodeSchema(
    node_prompt=PREAMBLE
    + (
        "Right now, you need to get the payment information. They can only use gift card or credit card "
        "IMPORTANT: All payment methods must already be in user profile for safety reasons."
    ),
    node_system_prompt=AirlineNodeSystemPrompt,
    input_schema=OrderInput2,
    state_schema=PaymentOrder,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=["calculate"],
)


# ------------------------------------------------------------------


class OrderInput3(BaseModel):
    user_details: UserDetails
    reservation_details: ReservationDetails
    flight_infos: List[FlightInfo]
    payment_id: str


update_flight_node_schema = ConversationNodeSchema(
    node_prompt=PREAMBLE
    + "Right now, you have all the data necessary to place the booking.",
    node_system_prompt=AirlineNodeSystemPrompt,
    input_schema=OrderInput3,
    state_schema=None,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=["update_reservation_flights", "calculate"],
    run_assistant_turn_before_transition=True,
)
# ----------------------------------------------

edge_schema_1 = EdgeSchema(
    from_node_schema=get_user_id_node_schema,
    to_node_schema=get_reservation_details_node_schema,
    transition_config=StateTransitionConfig(
        need_user_msg=True,
        state_check_fn_map={"user_details": lambda val: val is not None},
    ),
    new_input_fn=lambda state: UserInput(user_details=state.user_details),
)


edge_schema_2 = EdgeSchema(
    from_node_schema=get_reservation_details_node_schema,
    to_node_schema=find_flight_node_schema,
    transition_config=StateTransitionConfig(
        need_user_msg=True,
        state_check_fn_map={"reservation_details": lambda val: val is not None},
    ),
    new_input_fn=lambda state: OrderInput1(
        user_details=state.user_details, reservation_details=state.reservation_details
    ),
)


edge_schema_3 = EdgeSchema(
    from_node_schema=find_flight_node_schema,
    to_node_schema=get_payment_node_schema,
    transition_config=StateTransitionConfig(
        need_user_msg=True,
        state_check_fn_map={"flight_infos": lambda val: val and len(val) > 0},
    ),
    new_input_fn=lambda state: OrderInput2(
        user_details=state.user_details,
        reservation_details=state.reservation_details,
        flight_infos=state.flight_infos,
    ),
)


edge_schema_4 = EdgeSchema(
    from_node_schema=get_payment_node_schema,
    to_node_schema=update_flight_node_schema,
    transition_config=StateTransitionConfig(
        need_user_msg=True,
        state_check_fn_map={"payment_id": lambda val: val is not None},
    ),
    new_input_fn=lambda state: OrderInput3(
        user_details=state.user_details,
        reservation_details=state.reservation_details,
        flight_infos=state.flight_infos,
        payment_id=state.payment_id,
    ),
)

# ------------------------


class GraphOutputSchema(BaseModel):
    reservation_id: str
    user_id: str
    origin: str
    destination: str
    flight_type: FlightType
    cabin: CabinType
    flights: List[FlightReservationInfo]
    passengers: List[PassengerInfo]
    payment_history: List[PaymentDetails]
    created_at: str
    total_baggages: int
    nonfree_baggages: int
    insurance: InsuranceValue


class StateSchema(BaseStateModel):
    user_details: Optional[UserDetails] = None
    reservation_details: Optional[ReservationDetails] = None
    flight_infos: List[FlightInfo] = Field(default_factory=list)
    payment_id: Optional[str] = None


CHANGE_FLIGHT_GRAPH = GraphSchema(
    description="Help customers change flights",
    start_node_schema=get_user_id_node_schema,
    last_node_schema=update_flight_node_schema,
    output_schema=GraphOutputSchema,
    node_schemas=[
        get_user_id_node_schema,
        get_reservation_details_node_schema,
        find_flight_node_schema,
        get_payment_node_schema,
        update_flight_node_schema,
    ],
    edge_schemas=[edge_schema_1, edge_schema_2, edge_schema_3, edge_schema_4],
    state_schema=StateSchema,
    run_assistant_turn_before_transition=True,
)
