# Copyright Sierra

from .book_reservation import book_reservation
from .calculate import calculate
from .cancel_reservation import cancel_reservation
from .get_reservation_details import get_reservation_details
from .get_user_details import get_user_details
from .list_all_airports import list_all_airports
from .search_direct_flight import search_direct_flight
from .search_onestop_flight import search_onestop_flight
from .send_certificate import send_certificate
from .think import think
from .transfer_to_human_agents import transfer_to_human_agents
from .update_reservation_baggages import update_reservation_baggages
from .update_reservation_flights import update_reservation_flights
from .update_reservation_passengers import update_reservation_passengers

tools = [
    book_reservation,
    calculate,
    cancel_reservation,
    get_reservation_details,
    get_user_details,
    list_all_airports,
    search_direct_flight,
    search_onestop_flight,
    send_certificate,
    think,
    transfer_to_human_agents,
    update_reservation_baggages,
    update_reservation_flights,
    update_reservation_passengers,
]

assert all(tool.__info__ for tool in tools)

for tool in tools:
    assert tool.__name__ == tool.__info__["function"]["name"], tool
    assert list(tool.__info__["function"]["parameters"]["properties"].keys()) == list(
        tool.__info__["function"]["parameters"]["required"]
    ), tool
