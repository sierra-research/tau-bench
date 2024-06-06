# Copyright Sierra

import json
from typing import Any, Dict


def get_reservation_details(data: Dict[str, Any], reservation_id: str) -> str:
    reservations = data["reservations"]
    if reservation_id in reservations:
        return json.dumps(reservations[reservation_id])
    return "Error: user not found"


get_reservation_details.__info__ = {
    "type": "function",
    "function": {
        "name": "get_reservation_details",
        "description": "Get the details of a reservation.",
        "parameters": {
            "type": "object",
            "properties": {
                "reservation_id": {
                    "type": "string",
                    "description": "The reservation id, such as '8JX2WO'.",
                },
            },
            "required": ["reservation_id"],
        },
    },
}
