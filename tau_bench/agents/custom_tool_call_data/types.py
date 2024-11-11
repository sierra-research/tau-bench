from enum import StrEnum

from pydantic import BaseModel, Field


class FlightType(StrEnum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


class CabinType(StrEnum):
    BASIC_ECONOMY="basic_economy"
    ECONOMY = "economy"
    BUSINESS="business"


class FlightInfo(BaseModel):
    type: FlightType
    flight_number: str = Field(description = "Flight number, such as 'HAT001'.")
    date: str = Field(description="The date for the flight in the format 'YYYY-MM-DD', such as '2024-05-01'.")
    cabin: CabinType


class PassengerInfo(BaseModel):
    first_name: str
    last_name: str
    dob: str = Field(description="The date of birth of the passenger in the format 'YYYY-MM-DD', such as '1990-01-01'.")


class PaymentMethod(BaseModel):
     payment_id: str = Field(description="The payment id stored in user profile, such as 'credit_card_7815826', 'gift_card_7815826', 'certificate_7815826'.")
     amount: float = Field(description="The amount to be paid.")


class InsuranceValue(StrEnum):
    YES = "yes"
    NO = "no"