from cashier.graph.conversation_node import ConversationNodeSchema
from cashier.graph.base.base_state import BaseStateModel
from cashier.graph.base.base_edge_schema import FunctionTransitionConfig, FunctionState
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
    NewFlightInfo,
)
from tau_bench.agents.custom_tool_call_data.prompts import AirlineNodeSystemPrompt
from pydantic import Field, BaseModel, computed_field
from tau_bench.agents.custom_tool_call_data.tool_registry import AIRLINE_TOOL_REGISTRY
from tau_bench.agents.custom_tool_call_data.types import ReservationDetails
from cashier.graph.conversation_node import AlertConfig
from tau_bench.agents.custom_tool_call_data.prompts import NoAvailableSeatsPrompt
## book flight graph

PREAMBLE = "You are helping the customer to change flight/s. "


class UserState(BaseStateModel):
    user_details: Optional[UserDetails] = None


get_user_id_node_schema = ConversationNodeSchema(
    node_prompt=PREAMBLE + "Right now, you need to get their user details.",
    node_system_prompt=AirlineNodeSystemPrompt,
    state_schema=UserState,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=["get_user_details", "calculate"],
)

# ---------------------------------------------------------



class ReservationDetailsState(BaseStateModel):
    reservation_details: Optional[ReservationDetails] = None


get_reservation_details_node_schema = ConversationNodeSchema(
    node_prompt=PREAMBLE
    + "Right now, you need to get the reservation details by asking for the reservation id. If they don't know the id, lookup each reservation in their user details and find the one that best matches their description .",
    node_system_prompt=AirlineNodeSystemPrompt,
    state_schema=ReservationDetailsState,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=[
        "get_reservation_details",
        "calculate",
        "list_all_airports",
    ],
)


# ---------------------------------------------------------



class FlightOrder(BaseStateModel):
    resettable_fields = ["has_confirmed_new_flights", "new_flight_infos","has_communicated_new_flights_total_travel_time", "new_flights_total_travel_time"]
    has_communicated_new_flights_total_travel_time: bool = Field( # this doesnt work that well
        default=False,
        descripion="True only if you have communicated the total travel time for the new flights to the customer",
    )
    new_flights_total_travel_time: Optional[int] = Field(None, description="The total travel time of the new flights in hours, including layover time")
    flight_infos: List[FlightInfo] = Field(
        default_factory=list,
        descripion="An array of objects containing details about each piece of flight in the ENTIRE new reservation. Even if a flight segment is not changed, it should still be included in the array.",
    )
    new_flight_infos: List[NewFlightInfo] = Field(
        default_factory=list,
        descripion="An array of objects containing details about new flights only",
    )
    has_confirmed_new_flights: bool = Field(
        default=False,
        descripion="this can only be set to true if the customer has explicitly confirmed the new flights",
    )


    @computed_field(
        description="the total difference in cost between the old and new flights. If the value is negative, it represents the refund amount."
    )
    @property
    def net_new_cost(self) -> Optional[int]:
        if self._input is not None and len(self.flight_infos) > 0:
            old_cost = sum(
                [flight.price for flight in self._input.reservation_details.flights]
            )
            new_cost = sum([flight.price for flight in self.flight_infos])
            return new_cost - old_cost
        else:
            return None
        

def alert_check(state, input):
    flight_infos = state.new_flight_infos
    offending_flights = []
    for flight_info in flight_infos:
        if flight_info.cabin == CabinType.ECONOMY:
            target_seat_numb = flight_info.available_seats_in_economy
        elif flight_info.cabin == CabinType.BUSINESS:
            target_seat_numb = flight_info.available_seats_in_business
        elif flight_info.cabin == CabinType.BASIC_ECONOMY:
            target_seat_numb = flight_info.available_seats_in_basic_economy
        else:
            raise ValueError(f"Unknown cabin type: {flight_info.cabin}")
        
        if target_seat_numb == 0:
            offending_flights.append(flight_info)

    return len(offending_flights) > 0

alert_config = AlertConfig(
    state_field = "new_flight_infos",
    alert_condition = alert_check,
    alert_msg = NoAvailableSeatsPrompt
)

find_flight_node_schema = ConversationNodeSchema(
    node_prompt=PREAMBLE
    + (
        "Right now, you need to help find new flights for them. The customer can change anything from a single flight segment to all the flights. "
        "Remember, basic economy flights cannot be modified. Other reservations can be modified without changing the origin, destination, and cabin type. "
        "Also, make sure to check that all new flights have available seats in the selected cabin."
    ),
    node_system_prompt=AirlineNodeSystemPrompt,
    state_schema=FlightOrder,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=[
        "search_direct_flight",
        "search_onestop_flight",
        "list_all_airports",
        "calculate",
    ],
    completion_config=StateTransitionConfig(need_user_msg=False,state_check_fn_map={"has_confirmed_new_flights": lambda val: val is True,
                                                                                    "has_communicated_new_flights_total_travel_time": lambda val: val is True}),
    alert_configs = [alert_config],
    pre_alert_fn_names=["search_direct_flight", "search_onestop_flight"]
)


# ------------------------------------------------------------------
class PaymentOrder(BaseStateModel):
    resettable_fields = ["can_payment_cover_net_new_cost"]
    payment_id: Optional[str] = None
    can_payment_cover_net_new_cost: bool = Field(
        default=False,
        descripion="True only if the payment method can cover the net new cost. If net new cost is negative, it represents the refund amount, which gets refunded to the selected payment method."
    )


get_payment_node_schema = ConversationNodeSchema(
    node_prompt=PREAMBLE
    + (
        "Right now, you need to get the payment information. They can only use gift card or credit card. Only one payment method can be used. "
        "IMPORTANT: All payment methods must already be in user profile for safety reasons."
    ),
    node_system_prompt=AirlineNodeSystemPrompt,
    state_schema=PaymentOrder,
    tool_registry_or_tool_defs=AIRLINE_TOOL_REGISTRY,
    tool_names=["calculate"],
)


# ------------------------------------------------------------------


update_flight_node_schema = ConversationNodeSchema(
    node_prompt=PREAMBLE
    + "Right now, you have all the data necessary to place the booking.",
    node_system_prompt=AirlineNodeSystemPrompt,
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
)


edge_schema_2 = EdgeSchema(
    from_node_schema=get_reservation_details_node_schema,
    to_node_schema=find_flight_node_schema,
    transition_config=StateTransitionConfig(
        need_user_msg=True,
        state_check_fn_map={"reservation_details": lambda val: val is not None},
    ),
)


edge_schema_3 = EdgeSchema(
    from_node_schema=find_flight_node_schema,
    to_node_schema=get_payment_node_schema,
    transition_config=StateTransitionConfig(
        need_user_msg=True,
        state_check_fn_map={"flight_infos": lambda val: val and len(val) > 0, "net_new_cost": lambda val: val is not None},
    ),
)


edge_schema_4 = EdgeSchema(
    from_node_schema=get_payment_node_schema,
    to_node_schema=update_flight_node_schema,
    transition_config=StateTransitionConfig(
        need_user_msg=True,
        state_check_fn_map={"payment_id": lambda val: val is not None},
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
    net_new_cost: Optional[int] = None
    payment_id: Optional[str] = None


CHANGE_FLIGHT_GRAPH = GraphSchema(
    description="Help customers change flights",
    start_node_schema=get_user_id_node_schema,
    end_node_schema=update_flight_node_schema,
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
    completion_config=FunctionTransitionConfig(need_user_msg=False,fn_name="update_reservation_flights", state=FunctionState.CALLED_AND_SUCCEEDED),
    run_assistant_turn_before_transition=True,
)
