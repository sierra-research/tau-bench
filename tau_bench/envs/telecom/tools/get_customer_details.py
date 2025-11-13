# Verified

import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class GetCustomerDetails(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], customer_id: str) -> str:
        customers = data.get("customers", {})
        
        if customer_id not in customers:
            return f"Error: Customer not found: {customer_id}"
        
        return json.dumps(customers[customer_id])

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_customer_details",
                "description": "Get detailed information about a customer, including their account, services, and devices.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The customer's unique identifier, such as 'first_last_1234'.",
                        },
                    },
                    "required": ["customer_id"],
                },
            },
        }
