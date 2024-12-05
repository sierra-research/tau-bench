from cashier.graph.node_schema import NodeSchema
from cashier.graph.mixin.state_mixin import BaseStateModel
from cashier.graph.edge_schema import EdgeSchema
from cashier.graph.mixin.base_edge_schema import StateTransitionConfig
from cashier.graph.graph_schema import GraphSchema
from typing import Optional, List
from tau_bench.agents.custom_tool_call_data.types import (
    CabinType,
    FlightInfo,
    FlightReservationInfo,
    FlightType,
    PassengerInfo,
    PaymentDetails,
    PaymentMethod,
    InsuranceValue,
    ReservationDetails,
    UserDetails,
)
from tau_bench.agents.custom_tool_call_data.prompts import AirlineNodeSystemPrompt
from pydantic import Field, BaseModel
from tau_bench.agents.custom_tool_call_data.tool_registry import AIRLINE_TOOL_REGISTRY

## book flight graph

PREAMBLE = "You are helping the customer to change the baggage information for a reservation. "


class UserState(BaseStateModel):
    user_details: UserDetails = None


get_user_id_node_schema = NodeSchema(
    node_prompt=PREAMBLE + "Right now, you need to get their user details.",
    node_system_prompt=AirlineNodeSystemPrompt,
    input_pydantic_model=None,
    state_pydantic_model=UserState,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=["get_user_details", "calculate"],
)

# ---------------------------------------------------------


class UserInput(BaseModel):
    user_details: UserDetails


class ReservationDetailsState(BaseStateModel):
    reservation_details: Optional[ReservationDetails] = None


get_reservation_details_node_schema = NodeSchema(
    node_prompt=PREAMBLE
    + "Right now, you need to get the reservation details by asking for the reservation id. If they don't know the id, lookup each reservation in their user details and find the one that best matches their description .",
    node_system_prompt=AirlineNodeSystemPrompt,
    input_pydantic_model=UserInput,
    state_pydantic_model=ReservationDetailsState,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=[
        "get_reservation_details",
        "calculate",
        "list_all_airports",
    ],
)

# ------------------------------------------


class OrderInput3(BaseModel):
    user_details: UserDetails
    reservation_details: ReservationDetails


class LuggageState(BaseStateModel):
    total_baggages: Optional[int] = None
    nonfree_baggages: Optional[int] = None


luggage_node_schema = NodeSchema(
    node_prompt=PREAMBLE
    + (
        "Right now, you need to ask how many luggages to check. "
        "If the booking user is a regular member, 0 free checked bag for each basic economy passenger, 1 free checked bag for each economy passenger, and 2 free checked bags for each business passenger. If the booking user is a silver member, 1 free checked bag for each basic economy passenger, 2 free checked bag for each economy passenger, and 3 free checked bags for each business passenger. If the booking user is a gold member, 2 free checked bag for each basic economy passenger, 3 free checked bag for each economy passenger, and 3 free checked bags for each business passenger. Each extra baggage is 50 dollars."
    ),
    node_system_prompt=AirlineNodeSystemPrompt,
    input_pydantic_model=OrderInput3,
    state_pydantic_model=LuggageState,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=["calculate"],
)

# ---------------------------------------------------------


class OrderInput4(BaseModel):
    user_details: UserDetails
    reservation_details: ReservationDetails
    total_baggages: int
    nonfree_baggages: int


class PaymentState(BaseStateModel):
    payments: List[PaymentMethod] = Field(default_factory=list)
    has_explained_payment_policy_to_customer: bool = Field(default=False, description='There are very important payment policies, and these must be clearly communicated to the customer. Most importantly, the customer must understand that any left-over balance on a travel certificate will be forfeited.')
    is_payment_finalized: bool = Field(default=False, description='This can only be true after payment policy has been communicated and payment method collected')

payment_node_schema = NodeSchema(
    node_prompt=PREAMBLE
    + (
        "Right now, you need to get the payment information. "
        "IMPORTANT: Each reservation can use AT MOST one travel certificate, AT MOST one credit card, and AT MOST three gift cards. The remaining unused amount of a travel certificate is not refundable (i.e. forfeited). All payment methods must already be in user profile for safety reasons."
    ),
    node_system_prompt=AirlineNodeSystemPrompt,
    input_pydantic_model=OrderInput4,
    state_pydantic_model=PaymentState,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=["calculate"],
)


# ---------------------------------------------------------
class OrderInput5(BaseModel):
    user_details: UserDetails
    reservation_details: ReservationDetails
    total_baggages: int
    nonfree_baggages: int
    payments: List[PaymentMethod]


class BookingState(BaseStateModel):
    is_baggage_change_successfull: bool = False


book_flight_node_schema = NodeSchema(
    node_prompt=PREAMBLE
    + "Right now, you have all the data necessary to change the baggage for the reservation.",
    node_system_prompt=AirlineNodeSystemPrompt,
    input_pydantic_model=OrderInput5,
    state_pydantic_model=BookingState,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=[
        "update_reservation_baggages",
        "calculate",
    ],
)

# ---------------------------------------------------------

edge_1 = EdgeSchema(
    from_node_schema=get_user_id_node_schema,
    to_node_schema=get_reservation_details_node_schema,
    transition_config=StateTransitionConfig(need_user_msg=True, state_check_fn_map={"user_details": lambda val: val is not None}),
    new_input_fn=lambda state: UserInput(user_details=state.user_details),
)

edge_2 = EdgeSchema(
    from_node_schema=get_reservation_details_node_schema,
    to_node_schema=luggage_node_schema,
    transition_config=StateTransitionConfig(need_user_msg=True, state_check_fn_map={"reservation_details": lambda val: bool(val)}),
    new_input_fn=lambda state: OrderInput3(
        user_details=state.user_details, reservation_details=state.reservation_details
    ),
)

edge_3 = EdgeSchema(
    from_node_schema=luggage_node_schema,
    to_node_schema=payment_node_schema,
    transition_config=StateTransitionConfig(need_user_msg=True, state_check_fn_map={"total_baggages": lambda val: val is not None, "nonfree_baggages": lambda val: val is not None}),
    new_input_fn=lambda state: OrderInput4(
        user_details=state.user_details,
        reservation_details=state.reservation_details,
        total_baggages=state.total_baggages,
        nonfree_baggages=state.nonfree_baggages,
    ),
)

edge_4 = EdgeSchema(
    from_node_schema=payment_node_schema,
    to_node_schema=book_flight_node_schema,
    transition_config=StateTransitionConfig(need_user_msg=True, state_check_fn_map={"payments": lambda val: val and len(val) > 0, "is_payment_finalized": lambda val: bool(val)}),
    new_input_fn=lambda state: OrderInput5(
        user_details=state.user_details,
        reservation_details=state.reservation_details,
        total_baggages=state.total_baggages,
        nonfree_baggages=state.nonfree_baggages,
        payments=state.payments
    ),
)
# --------------------

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


class StateSchema(BaseModel):
    user_details: Optional[UserDetails] = None
    reservation_details: Optional[ReservationDetails] = None
    total_baggages: Optional[int] = None
    nonfree_baggages: Optional[int] = None
    payments: List[PaymentMethod] = Field(default_factory=list)


CHANGE_BAGGAGE_GRAPH = GraphSchema(
    description="Help customers update baggage information for a reservation",
    start_node_schema=get_user_id_node_schema,
    output_schema= GraphOutputSchema,
    last_node_schema=book_flight_node_schema,
    edge_schemas=[edge_1, edge_2, edge_3, edge_4],
    node_schemas=[
        get_user_id_node_schema,
        get_reservation_details_node_schema,
        luggage_node_schema,
        payment_node_schema,
        book_flight_node_schema,
    ],
    state_pydantic_model=StateSchema,
)
