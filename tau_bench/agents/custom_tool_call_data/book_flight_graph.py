from cashier.graph import NodeSchema, BaseStateModel, EdgeSchema, GraphSchema
from typing import Optional, List, Dict
from tau_bench.agents.custom_tool_call_data.types import (
    FlightInfo,
    PassengerInfo,
    PaymentMethod,
    InsuranceValue,
)
import tau_bench.envs.airline.tools as TOOLS
from tau_bench.agents.custom_tool_call_data.prompts import AirlineNodeSystemPrompt
from pydantic import Field, BaseModel

## book flight graph

PREAMBLE = "You are helping the customer to book a flight. "


class UserState(BaseStateModel):
    user_details: Dict = None


get_user_id_node_schema = NodeSchema(
    node_prompt=PREAMBLE + "Right now, you need to get their user details.",
    node_system_prompt=AirlineNodeSystemPrompt,
    input_pydantic_model=None,
    state_pydantic_model=UserState,
    tool_registry_or_tool_defs_map=[
        TOOLS.Think.get_info(),
        TOOLS.GetUserDetails.get_info(),
        TOOLS.Calculate.get_info(),
    ],
)

# ---------------------------------------------------------


class UserInput(BaseModel):
    user_details: Dict


class FlightOrder(BaseStateModel):
    flight_infos: List[FlightInfo] = Field(default_factory=list)


find_flight_node_schema = NodeSchema(
    node_prompt=PREAMBLE + "Right now, you need to help find flights for them.",
    node_system_prompt=AirlineNodeSystemPrompt,
    input_pydantic_model=UserInput,
    state_pydantic_model=FlightOrder,
    tool_registry_or_tool_defs_map=[
        TOOLS.Think.get_info(),
        TOOLS.SearchDirectFlight.get_info(),
        TOOLS.SearchOnestopFlight.get_info(),
        TOOLS.ListAllAirports.get_info(),
        TOOLS.Calculate.get_info(),
    ],
)


# ---------------------------------------------------------
class OrderInput(BaseModel):
    user_details: Dict
    flight_infos: List[FlightInfo]


class PassengerState(BaseStateModel):
    passengers: List[PassengerInfo] = Field(default_factory=list)


get_passanger_info_schema = NodeSchema(
    node_prompt=(
        PREAMBLE
        + (
            "Right now, you need to get the passenger info of all the passengers."
            "Each reservation can have at most five passengers. All passengers must fly the same flights in the same cabin."
        )
    ),
    node_system_prompt=AirlineNodeSystemPrompt,
    input_pydantic_model=OrderInput,
    state_pydantic_model=PassengerState,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info(), TOOLS.Calculate.get_info()],
)


# ---------------------------------------------------------
class OrderInput2(BaseModel):
    user_details: Dict
    flight_infos: List[FlightInfo]
    passengers: List[PassengerInfo]


class InsuranceState(BaseStateModel):
    add_insurance: Optional[InsuranceValue] = Field(
        default=None, description="whether to add insurance for all passengers"
    )


ask_for_insurance_node_schema = NodeSchema(
    node_prompt=PREAMBLE
    + "Right now, you need to ask if they want to add insurance, which is 30 dollars per passenger and enables full refund if the user needs to cancel the flight given health or weather reasons.",
    node_system_prompt=AirlineNodeSystemPrompt,
    input_pydantic_model=OrderInput2,
    state_pydantic_model=InsuranceState,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info(), TOOLS.Calculate.get_info()],
)

# ------------------------------------------


class OrderInput3(BaseModel):
    user_details: Dict
    flight_infos: List[FlightInfo]
    passengers: List[PassengerInfo]
    add_insurance: InsuranceValue


class LuggageState(BaseStateModel):
    total_baggages: Optional[int]
    nonfree_baggages: Optional[int]


luggage_node_schema = NodeSchema(
    node_prompt=PREAMBLE
    + (
        "Right now, you need to ask how many luggages to check. "
        "If the booking user is a regular member, 0 free checked bag for each basic economy passenger, 1 free checked bag for each economy passenger, and 2 free checked bags for each business passenger. If the booking user is a silver member, 1 free checked bag for each basic economy passenger, 2 free checked bag for each economy passenger, and 3 free checked bags for each business passenger. If the booking user is a gold member, 2 free checked bag for each basic economy passenger, 3 free checked bag for each economy passenger, and 3 free checked bags for each business passenger. Each extra baggage is 50 dollars."
    ),
    node_system_prompt=AirlineNodeSystemPrompt,
    input_pydantic_model=OrderInput3,
    state_pydantic_model=LuggageState,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info(), TOOLS.Calculate.get_info()],
)

# ---------------------------------------------------------


class OrderInput4(BaseModel):
    user_details: Dict
    flight_infos: List[FlightInfo]
    passengers: List[PassengerInfo]
    add_insurance: InsuranceValue
    total_baggages: int
    nonfree_baggages: int


class PaymentState(BaseStateModel):
    payments: List[PaymentMethod] = Field(default_factory=list)


payment_node_schema = NodeSchema(
    node_prompt=PREAMBLE
    + (
        "Right now, you need to get the payment information"
        "Each reservation can use at most one travel certificate, at most one credit card, and at most three gift cards. The remaining amount of a travel certificate is not refundable. All payment methods must already be in user profile for safety reasons."
    ),
    node_system_prompt=AirlineNodeSystemPrompt,
    input_pydantic_model=OrderInput4,
    state_pydantic_model=PaymentState,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info(), TOOLS.Calculate.get_info()],
)


# ---------------------------------------------------------
class OrderInput5(BaseModel):
    user_details: Dict
    flight_infos: List[FlightInfo]
    passengers: List[PassengerInfo]
    add_insurance: InsuranceValue
    total_baggages: int
    nonfree_baggages: int
    payments: List[PaymentMethod]


class BookingState(BaseStateModel):
    is_booking_successfull: bool = False


book_flight_node_schema = NodeSchema(
    node_prompt=PREAMBLE
    + "Right now, you have all the data necessary to place the booking.",
    node_system_prompt=AirlineNodeSystemPrompt,
    input_pydantic_model=OrderInput5,
    state_pydantic_model=BookingState,
    tool_registry_or_tool_defs_map=[
        TOOLS.Think.get_info(),
        TOOLS.BookReservation.get_info(),
        TOOLS.Calculate.get_info(),
    ],
)

# ---------------------------------------------------------

edge_1 = EdgeSchema(
    from_node_schema=get_user_id_node_schema,
    to_node_schema=find_flight_node_schema,
    state_condition_fn=lambda state: state.user_details is not None,
    new_input_fn=lambda state, input: UserInput(user_details=state.user_details),
)

edge_2 = EdgeSchema(
    from_node_schema=find_flight_node_schema,
    to_node_schema=get_passanger_info_schema,
    state_condition_fn=lambda state: state.flight_infos and len(state.flight_infos) > 0,
    new_input_fn=lambda state, input: OrderInput(
        user_details=input.user_details, flight_infos=state.flight_infos
    ),
)

edge_3 = EdgeSchema(
    from_node_schema=get_passanger_info_schema,
    to_node_schema=ask_for_insurance_node_schema,
    state_condition_fn=lambda state: state.passengers and len(state.passengers) > 0,
    new_input_fn=lambda state, input: OrderInput2(
        user_details=input.user_details,
        flight_infos=input.flight_infos,
        passengers=state.passengers,
    ),
)

edge_4 = EdgeSchema(
    from_node_schema=ask_for_insurance_node_schema,
    to_node_schema=luggage_node_schema,
    state_condition_fn=lambda state: state.add_insurance is not None,
    new_input_fn=lambda state, input: OrderInput3(
        user_details=input.user_details,
        flight_infos=input.flight_infos,
        passengers=input.passengers,
        add_insurance=state.add_insurance,
    ),
)


edge_5 = EdgeSchema(
    from_node_schema=luggage_node_schema,
    to_node_schema=payment_node_schema,
    state_condition_fn=lambda state: state.total_baggages is not None
    and state.nonfree_baggages is not None,
    new_input_fn=lambda state, input: OrderInput4(
        user_details=input.user_details,
        flight_infos=input.flight_infos,
        passengers=input.passengers,
        add_insurance=state.add_insurance,
        total_baggages=state.total_baggages,
        nonfree_baggages=state.nonfree_baggages,
    ),
)

edge_6 = EdgeSchema(
    from_node_schema=payment_node_schema,
    to_node_schema=book_flight_node_schema,
    state_condition_fn=lambda state: state.payments and len(state.payments) > 0,
    new_input_fn=lambda state, input: OrderInput5(
        user_details=input.user_details,
        flight_infos=input.flight_infos,
        passengers=input.passengers,
        add_insurance=state.add_insurance,
        total_baggages=state.total_baggages,
        nonfree_baggages=state.nonfree_baggages,
        payments=state.payments,
    ),
)
# --------------------

BOOK_FLIGHT_GRAPH = GraphSchema(
    start_node_schema=get_user_id_node_schema,
    edge_schemas=[edge_1, edge_2, edge_3, edge_4, edge_5, edge_6],
    node_schemas=[
        get_user_id_node_schema,
        find_flight_node_schema,
        get_passanger_info_schema,
        ask_for_insurance_node_schema,
        luggage_node_schema,
        payment_node_schema,
        book_flight_node_schema,
    ],
)
