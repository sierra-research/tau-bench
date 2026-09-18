# Copyright Sierra

"""Regression test for issue #77: update_reservation_flights must update
``reservation["cabin"]`` when the cabin changes, not just the flight prices.

Before the fix, ``invoke`` rewrote ``reservation["flights"]`` (with the new
cabin's prices) but left ``reservation["cabin"]`` at its old value, so the
returned reservation reported the old cabin while charging for the new one.
The sibling project tau2-bench already carries this fix
(``src/tau2/domains/airline/tools.py: reservation.cabin = cabin  # This was
missing from original TauBench``).

Run with:  pytest tests/test_update_reservation_flights.py
Or directly: python tests/test_update_reservation_flights.py
"""

import json
import os
import sys

# Allow running without an editable install of tau-bench.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tau_bench.envs.airline.tools.update_reservation_flights import (  # noqa: E402
    UpdateReservationFlights,
)


def _build_data(initial_cabin: str = "economy") -> dict:
    """Minimal but valid airline world state that lets a cabin upgrade succeed."""
    return {
        "users": {
            "user_1": {
                "payment_methods": {
                    "credit_card_1": {"source": "credit_card", "amount": 1000},
                }
            }
        },
        "reservations": {
            "RES1": {
                "user_id": "user_1",
                "passengers": [{"name": "A"}],  # len 1
                "cabin": initial_cabin,
                "flights": [
                    {
                        "flight_number": "HAT001",
                        "date": "2024-05-16",
                        "price": 100,
                        "origin": "X",
                        "destination": "Y",
                    }
                ],
                "payment_history": [],
            }
        },
        "flights": {
            "HAT001": {
                "origin": "X",
                "destination": "Y",
                "dates": {
                    "2024-05-16": {
                        "status": "available",
                        "available_seats": {
                            "basic_economy": 10,
                            "economy": 10,
                            "business": 10,
                        },
                        "prices": {
                            "basic_economy": 50,
                            "economy": 100,
                            "business": 200,
                        },
                    }
                },
            }
        },
    }


def test_cabin_is_updated_on_upgrade() -> None:
    """Upgrading economy -> business must set reservation["cabin"] = business."""
    data = _build_data(initial_cabin="economy")
    out = UpdateReservationFlights.invoke(
        data,
        "RES1",
        "business",
        [{"flight_number": "HAT001", "date": "2024-05-16"}],
        "credit_card_1",
    )
    assert not out.startswith("Error"), f"unexpected error: {out}"
    reservation = json.loads(out)
    assert reservation["cabin"] == "business"
    # Pricing must be consistent with the new cabin (business price = 200).
    assert reservation["flights"][0]["price"] == 200


def test_no_cabin_change_is_a_noop() -> None:
    """Re-supplying the same cabin leaves the reservation unchanged (no price swing)."""
    data = _build_data(initial_cabin="economy")
    out = UpdateReservationFlights.invoke(
        data,
        "RES1",
        "economy",
        [{"flight_number": "HAT001", "date": "2024-05-16"}],
        "credit_card_1",
    )
    assert not out.startswith("Error"), f"unexpected error: {out}"
    reservation = json.loads(out)
    assert reservation["cabin"] == "economy"
    assert reservation["flights"][0]["price"] == 100
    assert reservation["payment_history"] == []


def test_downgrade_keeps_cabin_consistent() -> None:
    """Downgrading business -> basic_economy must also update cabin."""
    data = _build_data(initial_cabin="business")
    out = UpdateReservationFlights.invoke(
        data,
        "RES1",
        "basic_economy",
        [{"flight_number": "HAT001", "date": "2024-05-16"}],
        "credit_card_1",
    )
    assert not out.startswith("Error"), f"unexpected error: {out}"
    reservation = json.loads(out)
    assert reservation["cabin"] == "basic_economy"
    assert reservation["flights"][0]["price"] == 50


if __name__ == "__main__":
    test_cabin_is_updated_on_upgrade()
    test_no_cabin_change_is_a_noop()
    test_downgrade_keeps_cabin_consistent()
    print("all 3 update_reservation_flights tests passed")
