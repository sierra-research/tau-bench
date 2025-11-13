
import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool


class AddDevice(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], 
                customer_id: str, 
                device_name: str) -> str:

        customers = data.get("customers", {})

        if customer_id not in customers:
            return f"Error: Customer not found: {customer_id}"
        
        customer = customers[customer_id]
        customer_devices = customer.get("devices", [])

        # check if the device name is a valid name 
        if device_name not in data.get("devices", {}):
            return f"Error: Invalid device name: {device_name}"

        # create a new device id for the device name 

        # add that device to the customer's devices
        customer_devices.append({
            "device_id": str(len(customer_devices) + 1),
            "name": device_name,
            "service": None,
        })

        return f"Success: Added device '{device_name}' to customer {customer_id}"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "add_device",
                "description": "Add a device to a customer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The customer's unique identifier, such as 'john_smith_1234'.",
                        },
                        "device_name": {
                            "type": "string",
                            "description": "".join(
                                (
                                    "The name of the device to add.",
                                    "Options: ",
                                    "iPhone 15 Pro",
                                    "iPhone 14",
                                    "iPhone 13",
                                    "Samsung Galaxy S23",
                                    "iPhone 12",
                                    "iPhone 15",
                                    "Google Pixel 8",
                                    "Samsung Galaxy A54",
                                    "iPhone SE (3rd gen)",
                                    "WiFi 6 Router",
                                    "Standard WiFi Router",
                                    "Enterprise Router",
                                    "Basic WiFi Router",
                                    "Samsung 65\" Smart TV",
                                    "HD Cable Box",
                                    "55\" Smart TV",
                                    "Conference Room TV",
                                    "Conference Phone System",
                                    "Home Security System",
                                )
                            )
                        },
                    },
                    "required": ["customer_id", "device_name"],
                },
            },
        }
