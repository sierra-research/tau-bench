# Verified

import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class GetServices(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any]) -> str:
        services = data.get("services", {})
        
        return json.dumps(services)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_services",
                "description": "Get detailed information about all telecom services.",
                "parameters": {
                    "type": "object",
                    "properties": {
                    },
                    "required": [],
                },
            },
        }
