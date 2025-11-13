# Verified

import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class GetDeviceDetails(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], device_name: str) -> str:
        devices = data.get("devices", {})
        
        if device_name not in devices:
            return f"Error: Device not found: {device_name}"
        
        return json.dumps(devices[device_name])

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_device_details",
                "description": "Get detailed information about a device on the market",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "device_name": {
                            "type": "string",
                            "description": "".join(
                                (
                                    "The name of the device to get details about.",
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
                    "required": ["device_name"],
                },
            },
        }
