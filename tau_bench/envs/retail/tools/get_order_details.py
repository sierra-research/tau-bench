# Copyright Sierra

import json
import random
import functools
from typing import Any, Dict
from tau_bench.envs.tool import Tool


def flaky_tool(prob: float = 0.1, error_message: str = "Error: 503 Service Unavailable"):
    """Decorator to introduce a controlled failure rate simulating transient service errors."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 10% chance to simulate a transient upstream outage
            if random.random() < prob:
                return error_message
            return func(*args, **kwargs)
        return wrapper
    return decorator


class GetOrderDetails(Tool):
    @staticmethod
    @flaky_tool(prob=0.3)
    def invoke(data: Dict[str, Any], order_id: str) -> str:  # type: ignore
        orders = data["orders"]
        if order_id in orders:
            return json.dumps(orders[order_id])
        return "Error: order not found"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_order_details",
                "description": "Get the status and details of an order. (Note: This endpoint may intermittently return a simulated '503 Service Unavailable' error; simply retry the same call.)",
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
