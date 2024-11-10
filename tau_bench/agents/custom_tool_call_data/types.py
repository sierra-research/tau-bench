from enum import StrEnum

from pydantic import BaseModel, Field


class TripType(StrEnum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


class CabinType(StrEnum):
    BASIC_ECONOMY="basic_economy"
    ECONOMY = "economy"
    BUSINESS="business"


class FlightInfo(BaseModel):
    type: TripType
    flight_number: str = Field(description = "Flight number, such as 'HAT001'.")
    date: str = Field(description="The date for the flight in the format 'YYYY-MM-DD', such as '2024-05-01'.")
    cabin: CabinType


class PassengerInfo(BaseModel):
    first_name: str
    last_name: str
    dob: str = Field(description="The date of birth of the passenger in the format 'YYYY-MM-DD', such as '1990-01-01'.")


class PaymentMethod(BaseModel):
     payment_id: str
     amount: float