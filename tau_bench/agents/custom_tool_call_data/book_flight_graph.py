from cashier.graph import NodeSchema, BaseStateModel
from typing import Optional, List, Dict
from tau_bench.agents.custom_tool_call_data.types import FlightInfo, PassengerInfo, PaymentMethod
import tau_bench.envs.airline.tools as TOOLS
from pydantic import Field, BaseModel

## book flight graph

class UserState(BaseStateModel):
    user_details: Dict = None

get_user_id_node_schema = NodeSchema(
    node_prompt="You are helping the users book a flight and you need to get the user ID",
    input_pydantic_model=None,
    state_pydantic_model=UserState,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info(), TOOLS.GetUserDetails.get_info()],
    )

#---------------------------------------------------------

class FlightOrder(BaseStateModel):
    flight_infos: List[FlightInfo] = Field(default_factory=list)

find_flight_node_schema = NodeSchema(
    node_prompt="You are helping the users book a flight and you need to get the trip info",
    input_pydantic_model=UserState,
    state_pydantic_model=FlightOrder,
    tool_registry_or_tool_defs_map=[TOOLS.Think.get_info(), TOOLS.SearchDirectFlight.get_info(), TOOLS.SearchOnestopFlight.get_info()],
    )

#---------------------------------------------------------

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

