from cashier.prompts.base_prompt import BasePrompt
from cashier.prompts.node_system import NodeSystemPrompt
from cashier.prompts.general_guideline import GeneralGuidelinePrompt
from cashier.prompts.response_guideline import ResponseGuidelinePrompt
from cashier.prompts.state_guideline import StateGuidelinePrompt
from cashier.graph import NodeSchema, BaseStateModel
from typing import Optional, List, Dict
from tau_bench.agents.custom_tool_call_data.types import FlightInfo, PassengerInfo, PaymentMethod
import tau_bench.envs.airline.tools as TOOLS
from pydantic import Field, BaseModel

class BackgroundPrompt(BasePrompt):

    f_string_prompt ="""The current time is 2024-05-15 15:00:00 EST. You are an airline agent, and you can help customers book, modify, or cancel flight reservations.

This is domain knowledge you are expected to know:
- Each customer has a profile containing user id, email, addresses, date of birth, payment methods, reservation numbers, and membership tier.
- Each reservation has an reservation id, user id, trip type (one way, round trip), flights, passengers, payment methods, created time, baggages, and travel insurance information.
- Each flight has a flight number, an origin, destination, scheduled departure and arrival time (local time), and for each date:
  - If the status is "available", the flight has not taken off, available seats and prices are listed.
  - If the status is "delayed" or "on time", the flight has not taken off, cannot be booked.
  - If the status is "flying", the flight has taken off but not landed, cannot be booked."""

class CustomToolGuideline(BasePrompt):
    f_string_prompt = (
        "<tools_guidelines>\n"
        "- You should not provide any information, knowledge, or procedures not provided by the customer or available tools, or give subjective recommendations or comments.\n"
        "- AVOID stating/mentioning that you can/will perform an action if there are no tools (including state updates) associated with that action.\n"
        "- Before taking any actions that update the booking database (booking, modifying flights, editing baggage, upgrading cabin class, or updating passenger information), you must list the action details and obtain explicit customer confirmation (yes) to proceed."
        "- if you need to perform an action, you can only state to the customer that you performed it after the associated tool (including state update) calls have been successfull.\n"
        "</tools_guidelines>\n"
    )

class AirlineNodeSystemPrompt(NodeSystemPrompt):
    BACKGROUND_PROMPT = BackgroundPrompt
    GUIDELINE_PROMPTS = [
        ResponseGuidelinePrompt,
        StateGuidelinePrompt,
        CustomToolGuideline,
        GeneralGuidelinePrompt,
    ]

## book flight graph

class UserState(BaseStateModel):
    user_info: Dict = None

get_user_id_node_schema = NodeSchema(
    node_prompt="You are helping the users book a flight and you need to get the user ID",
    input_pydantic_model=None,
    state_pydantic_model=UserState,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info(), TOOLS.GetUserDetails.get_info()],
    )

class FlightOrder(BaseStateModel):
    flight_infos: List[FlightInfo] = Field(default_factory=list)

find_flight_node_schema = NodeSchema(
    node_prompt="You are helping the users book a flight and you need to get the trip info",
    input_pydantic_model=UserState,
    state_pydantic_model=FlightOrder,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info(), TOOLS.SearchDirectFlight.get_info(), TOOLS.SearchOnestopFlight.get_info()],
    )

class PassengerState(BaseStateModel):
    passengers: List[PassengerInfo] = Field(default_factory=list)

get_passanger_info_schema = NodeSchema(
    node_prompt="You are helping the users book a flight and you need to get the trip info",
    input_pydantic_model=None,
    state_pydantic_model=PassengerState,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info()],
    )
#---------------------------------------------------------
class InsuranceState(BaseStateModel):
    add_insurance: Optional[bool] = Field(default=None, description="whether to add insurance for all passengers")

ask_for_insurance_node_schema = NodeSchema(
    node_prompt="You are helping the users book a flight and you need to get the trip info",
    input_pydantic_model=FlightOrder,
    state_pydantic_model=InsuranceState,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info(), TOOLS.Calculate.get_info()],
    )

#------------------------------------------

class Input(BaseModel):
    user_info: Dict

class LuggageState(BaseStateModel):
    total_baggages: Optional[int]
    nonfree_baggages: Optional[int]

luggage_node_schema = NodeSchema(
    node_prompt="You are helping the users book a flight and you need to get the trip info",
    input_pydantic_model=Input,
    state_pydantic_model=LuggageState,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info(), TOOLS.Calculate.get_info()],
    )

#---------------------------------------------------------

class Input(BaseModel):
    user_info: Dict


class PaymentState(BaseStateModel):
    payments: List[PaymentMethod] = Field(default_factory=list)

payment_node_schema = NodeSchema(
    node_prompt="You are helping the users book a flight and you need to get the trip info",
    input_pydantic_model=Input,
    state_pydantic_model=PaymentState,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info(), TOOLS.Calculate.get_info()],
    )

#---------------------------------------------------------
class BookingInput(BaseModel):
    user_info: Dict
    passengers: List[PassengerInfo]
    flight_infos: List[FlightInfo]
    payments: List[PaymentMethod]
    total_baggages: int
    nonfree_baggages: int

book_flight_node_schema = NodeSchema(
    node_prompt="You are helping the users book a flight and you need to get the trip info",
    input_pydantic_model=BookingInput,
    state_pydantic_model=InsuranceState,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info(), TOOLS.BookReservation.get_info()],
    )

