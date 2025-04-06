from pydantic import BaseModel, Field
from enum import StrEnum
from typing import List, Union, Any, Dict
from tau_bench.envs.tool import Tool
import json

class SortAttribute(StrEnum):
    PRICE = "price_any_class"
    PRICE_BASIC_ECONOMY = "price_basic_economy"
    PRICE_ECONOMY = "price_economy"
    PRICE_BUSINESS = "price_business"
    DEPARTURE_TIME = "departure_time"
    ARRIVAL_TIME = "arrival_time"
    TOTAL_FLIGHT_DURATION_EXCL_LAYOVER = "total_flight_duration_excl_layover"
    TOTAL_FLIGHT_DURATION_INCL_LAYOVER = "total_flight_duration_incl_layover"


SORT_ATTRIBUTE_STRING_VALUES = [attr.value for attr in SortAttribute]

SORT_ATTRIBUTE_TO_KEY_PATH = {
    SortAttribute.PRICE_BASIC_ECONOMY: "prices.basic_economy",
    SortAttribute.PRICE_ECONOMY: "prices.economy",
    SortAttribute.PRICE_BUSINESS: "prices.business",
    SortAttribute.DEPARTURE_TIME: "scheduled_departure_time_est",
    SortAttribute.ARRIVAL_TIME: "scheduled_arrival_time_est",
}


class SeatInfo(BaseModel):
    basic_economy: int
    economy: int
    business: int


class PriceInfo(BaseModel):
    basic_economy: int
    economy: int
    business: int


class FlightSegment(BaseModel):
    flight_number: str
    origin: str
    destination: str
    scheduled_departure_time_est: str
    scheduled_arrival_time_est: str
    status: str
    available_seats: SeatInfo
    prices: PriceInfo
    date: str


# This class is intentionally mispelled FlightSgment to differ from FlightSegment
# Currently, if an Union type references the same subtype twice,
# pydantic struggles to create a json schema via model_json_schema.
# Therefore, this is a workaround to fool pydantic into thinking that
# there are two separete types in FlighTrip.
class FlightSgment(FlightSegment):
    pass


FlightTrip = Union[FlightSgment, List[FlightSegment]]


def get_value_by_dict_key_path(obj, sort_by):
    key_path = SORT_ATTRIBUTE_TO_KEY_PATH[sort_by]
    for key in key_path.split("."):
        obj = obj[key]
    return obj


def time_difference_seconds(time1, time2):
    # Convert to seconds first
    def to_seconds(time_str):
        baseline = 0
        if "+1" in time_str:
            baseline += 86400
            time_str = time_str.replace("+1", "")
        hours, minutes, seconds = map(int, time_str.split(":"))
        baseline += hours * 3600 + minutes * 60 + seconds
        return baseline

    seconds1 = to_seconds(time1)
    seconds2 = to_seconds(time2)
    return seconds1 - seconds2


def get_sort_attribute(
    flight_trip: FlightTrip, sort_by: SortAttribute
):
    if type(flight_trip) is not list:
        if sort_by in [
            SortAttribute.TOTAL_FLIGHT_DURATION_EXCL_LAYOVER,
            SortAttribute.TOTAL_FLIGHT_DURATION_INCL_LAYOVER,
        ]:
            return time_difference_seconds(
                get_value_by_dict_key_path(
                    flight_trip, SortAttribute.ARRIVAL_TIME
                ),
                get_value_by_dict_key_path(
                    flight_trip,
                    SortAttribute.DEPARTURE_TIME,
                ),
            )
        elif sort_by == SortAttribute.PRICE:
            price_basic_economy = get_value_by_dict_key_path(
                flight_trip,
                SortAttribute.PRICE_BASIC_ECONOMY,
            )
            price_economy = get_value_by_dict_key_path(
                flight_trip, SortAttribute.PRICE_ECONOMY
            )
            price_business = get_value_by_dict_key_path(
                flight_trip, SortAttribute.PRICE_BUSINESS
            )
            return min(price_basic_economy, price_economy, price_business)
        else:
            return get_value_by_dict_key_path(
                flight_trip, sort_by
            )
    else:
        if sort_by in [
            SortAttribute.PRICE_BASIC_ECONOMY,
            SortAttribute.PRICE_ECONOMY,
            SortAttribute.PRICE_BUSINESS,
            SortAttribute.PRICE,
        ]:
            return sum(
                get_sort_attribute(segment, sort_by)
                for segment in flight_trip
            )
        else:
            sorted_flight_trip = sorted(
                flight_trip,
                key=lambda x: get_sort_attribute(
                    x, SortAttribute.DEPARTURE_TIME
                ),
            )
            if sort_by == SortAttribute.DEPARTURE_TIME:
                return get_value_by_dict_key_path(
                    sorted_flight_trip[0], sort_by
                )
            elif sort_by == SortAttribute.ARRIVAL_TIME:
                return get_value_by_dict_key_path(
                    sorted_flight_trip[-1], sort_by
                )
            elif sort_by == SortAttribute.TOTAL_FLIGHT_DURATION_EXCL_LAYOVER:
                duration = 0
                for segment in sorted_flight_trip:
                    duration += time_difference_seconds(
                        get_value_by_dict_key_path(
                            segment,
                            SortAttribute.ARRIVAL_TIME,
                        ),
                        get_value_by_dict_key_path(
                            segment,
                            SortAttribute.DEPARTURE_TIME,
                        ),
                    )
                return duration
            elif sort_by == SortAttribute.TOTAL_FLIGHT_DURATION_INCL_LAYOVER:
                return time_difference_seconds(
                    get_value_by_dict_key_path(
                        sorted_flight_trip[-1],
                        SortAttribute.ARRIVAL_TIME,
                    ),
                    get_value_by_dict_key_path(
                        sorted_flight_trip[0],
                        SortAttribute.DEPARTURE_TIME,
                    ),
                )
            else:
                raise ValueError(f"Invalid sort attribute: {sort_by}")
            

def sort_flights(flight_trips, sort_by: SortAttribute):
    return sorted(
        flight_trips,
        key=lambda x: get_sort_attribute(x, sort_by),
    )


class SortFlightToolSchema(BaseModel):
    flight_trips: List[FlightTrip] = Field(description="flights to sort. A single \"flight\" can be either a single FlightSegment or a list of FlightSegments.")
    sort_by: SortAttribute = Field(description="attribute to sort by")


sort_flight_tool_json_schema = SortFlightToolSchema.model_json_schema()
sort_flight_tool_json_schema.pop('title')

class SortFlights(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        flight_trips: List[Dict[str, Any]],
        sort_by: SortAttribute,
    ) -> str:
        sorted_flights = sort_flights(flight_trips, sort_by)
        return json.dumps(sorted_flights)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "sort_flights",
                "description": "Sorts flights by the sort attribute in ascending order",
                "parameters": sort_flight_tool_json_schema
            },
        }