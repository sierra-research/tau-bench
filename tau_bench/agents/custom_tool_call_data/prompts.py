from cashier.prompts.base_prompt import BasePrompt
from cashier.prompts.general_guideline import GeneralGuidelinePrompt
from cashier.prompts.node_system import NodeSystemPrompt
from cashier.prompts.response_guideline import ResponseGuidelinePrompt
from cashier.prompts.state_guideline import StateGuidelinePrompt
from pydantic import BaseModel
from tau_bench.agents.custom_tool_call_data.types import CabinType


class BackgroundPrompt(BasePrompt):

    f_string_prompt = """The current time is 2024-05-15 15:00:00 EST. You are an airline agent, and you can help customers book, modify, or cancel flight reservations.

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


class TextOnlyResponseGuideline(ResponseGuidelinePrompt):
    IS_VOICE_ONLY = False


class AirlineNodeSystemPrompt(NodeSystemPrompt):
    BACKGROUND_PROMPT = BackgroundPrompt
    GUIDELINE_PROMPTS = [
        TextOnlyResponseGuideline,
        StateGuidelinePrompt,
        CustomToolGuideline,
        GeneralGuidelinePrompt,
    ]

class NoAvailableSeatsPrompt(BasePrompt):

    def dynamic_prompt(
        self,
        state: BaseModel,
        input: BaseModel,
    ) -> str:
        flight_infos = state.new_flight_infos
        offending_flights = []
        for flight_info in flight_infos:
            if flight_info.cabin_type == CabinType.ECONOMY:
                target_seat_numb = flight_info.available_seats_in_economy
            elif flight_info.cabin_type == CabinType.BUSINESS:
                target_seat_numb = flight_info.available_seats_in_business
            elif flight_info.cabin_type == CabinType.BASIC_ECONOMY:
                target_seat_numb = flight_info.available_seats_in_basic_economy
            else:
                raise ValueError(f"Unknown cabin type: {flight_info.cabin_type}")
            
            if target_seat_numb == 0:
                offending_flights.append(flight_info)

        assert len(offending_flights) > 0, "No offending flights found"
        return "I can only add new flights that have available seats in the chosen cabin. However, the following flights do not have available seats in the chosen cabin: " + ", ".join([f"{flight_info.flight_number} ({flight_info.cabin_type})" for flight_info in offending_flights]) + ". I need to choose different flights."
