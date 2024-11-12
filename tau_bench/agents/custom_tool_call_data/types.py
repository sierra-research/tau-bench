from enum import StrEnum

from pydantic import BaseModel, Field
from typing import Literal, List, Union

class FlightType(StrEnum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


class CabinType(StrEnum):
    BASIC_ECONOMY = "basic_economy"
    ECONOMY = "economy"
    BUSINESS = "business"


class FlightInfo(BaseModel):
    type: FlightType
    flight_number: str = Field(description="Flight number, such as 'HAT001'.")
    date: str = Field(
        description="The date for the flight in the format 'YYYY-MM-DD', such as '2024-05-01'."
    )
    cabin: CabinType
    price: int # keeping this int because hasing is type sensitive (4 vs 4.0 create different hashes), and all prices are integers


class PassengerInfo(BaseModel):
    first_name: str
    last_name: str
    dob: str = Field(
        description="The date of birth of the passenger in the format 'YYYY-MM-DD', such as '1990-01-01'."
    )


class PaymentMethod(BaseModel):
    payment_id: str = Field(
        description="The payment id stored in user profile, such as 'credit_card_7815826', 'gift_card_7815826', 'certificate_7815826'."
    )
    amount: int = Field(description="The amount to be paid.") # keeping this int because hasing is type sensitive (4 vs 4.0 create different hashes), and all prices are integers


class InsuranceValue(StrEnum):
    YES = "yes"
    NO = "no"


class Name(BaseModel):
    first_name: str
    last_name: str

class Address(BaseModel):
    address1: str
    address2: str
    city: str
    country: str
    province: str
    zip: str

class PaymentSource(StrEnum):
    CREDIT_CARD = 'credit_card'
    CERTIFICATE = 'certificate'
    GIFT_CARD = 'gift_card'

class BaseSavedPaymentMethod(BaseModel):
    source: PaymentSource
    id: str

class CreditCard(BaseSavedPaymentMethod):
    source: Literal[PaymentSource.CREDIT_CARD] = PaymentSource.CREDIT_CARD
    brand: str
    last_four: str

class CertificateGift(BaseSavedPaymentMethod):
    source: Literal[PaymentSource.GIFT_CARD, PaymentSource.CERTIFICATE]
    amount: int

class SavedPassenger(Name):
    dob: str

class UserInfo(BaseModel):
    name: Name
    address: Address
    email: str
    dob: str
    payment_methods: List[Union[CreditCard, CertificateGift]]
    saved_passengers: List[SavedPassenger]
    membership: str
    reservations: List[str]