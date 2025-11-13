# Verified

import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class GetBillingDetails(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], customer_id: str) -> str:
        billing = data.get("billing", {})
        
        if customer_id not in billing:
            return f"Error: No billing information found for customer: {customer_id}"
        
        return json.dumps(billing[customer_id])

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_billing_details",
                "description": "Get billing information for a customer, including current balance, payment history, and monthly charges.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The customer's unique identifier, such as 'john_smith_1234'.",
                        },
                    },
                    "required": ["customer_id"],
                },
            },
        }
