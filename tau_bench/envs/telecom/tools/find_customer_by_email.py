# Verified

from typing import Any, Dict

from tau_bench.envs.tool import Tool


class FindCustomerByEmail(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], email: str) -> str:
        customers = data.get("customers", {})
        
        for customer_id, customer_info in customers.items():
            if customer_info.get("demographics", {}).get("email", "").lower() == email.lower():
                return customer_id
        
        return f"Error: No customer found with email address: {email}"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "find_customer_by_email",
                "description": "Find a customer by their email address.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The customer's email address, such as 'john.smith@email.com'.",
                        },
                    },
                    "required": ["email"],
                },
            },
        }
