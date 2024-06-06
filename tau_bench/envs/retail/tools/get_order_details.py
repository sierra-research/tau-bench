# Copyright Sierra

import json
from typing import Any, Dict


def get_order_details(data: Dict[str, Any], order_id: str) -> str:
    orders = data["orders"]
    if order_id in orders:
        return json.dumps(orders[order_id])
    return "Error: order not found"


get_order_details.__info__ = {
    "type": "function",
    "function": {
        "name": "get_order_details",
        "description": "Get the status and details of an order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.",
                },
            },
            "required": ["order_id"],
        },
    },
}
