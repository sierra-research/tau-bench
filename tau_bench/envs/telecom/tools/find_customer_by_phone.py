# Verified

from typing import Any, Dict

from tau_bench.envs.tool import Tool


class FindCustomerByPhone(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], phone: str) -> str:
        customers = data.get("customers", {})
        
        # Normalize phone number (remove formatting)
        normalized_phone = ''.join(filter(str.isdigit, phone))
        
        for customer_id, customer_info in customers.items():
            customer_phone = customer_info.get("demographics", {}).get("phone", "")
            normalized_customer_phone = ''.join(filter(str.isdigit, customer_phone))
            
            if normalized_customer_phone == normalized_phone:
                return customer_id
        
        return f"Error: No customer found with phone number: {phone}"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "find_customer_by_phone",
                "description": "Find a customer by their phone number.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone": {
                            "type": "string",
                            "description": "The customer's phone number, such as '(555) 123-4567'.",
                        },
                    },
                    "required": ["phone"],
                },
            },
        }
