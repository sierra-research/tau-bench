# Verified


import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool


class ManageDevices(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], 
                customer_id: str, 
                action: str) -> str:

        customers = data.get("customers", {})
        devices = data.get("devices", {})

        if customer_id not in customers:
            return f"Error: Customer not found: {customer_id}"
        
        customer = customers[customer_id]
        customer_devices = customer.get("devices", [])

        if action == "list":
            result = []
            for device_id in customer_devices:
                if device_id in devices:
                    device = devices[device_id]
                    result.append({
                        "device_id": device_id,
                        "name": device.get('name', device_id),
                    })
            return json.dumps({"customer_id": customer_id, "devices": result})
        
        else:
            return f"Error: Invalid action: {action}. Valid actions are: add, remove, list"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "manage_devices",
                "description": "Manage customer devices: add, remove, or list devices.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The customer's unique identifier, such as 'john_smith_1234'.",
                        },
                        "action": {
                            "type": "string",
                            "description": "Action to perform: 'list'.",
                        },
                    },
                    "required": ["customer_id", "action"],
                },
            },
        }
