# Verified

import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class GetServiceDetails(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], service_id: str) -> str:
        services = data.get("services", {})
        
        if service_id not in services:
            return f"Error: Service not found: {service_id}"
        
        return json.dumps(services[service_id])

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_service_details",
                "description": "Get detailed information about a telecom service.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service_id": {
                            "type": "string",
                            "description": "The service identifier, such as 'mobile_unlimited' or 'internet_fiber_1gb'.",
                        },
                    },
                    "required": ["service_id"],
                },
            },
        }
