
import json
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool


class CheckNetworkStatus(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], region: Optional[str] = None, service_type: Optional[str] = None) -> str:
        network_data = data.get("network_status", {})
        
        # If specific region and service requested, return that specific status
        if region and service_type:
            regions = network_data.get("network_regions", {})
            if region not in regions:
                return f"Error: Region not found: {region}"
            
            region_data = regions[region]
            services = region_data.get('services', {})
            
            if service_type not in services:
                return f"Error: Service type '{service_type}' not found for region {region}"
            
            service_data = services[service_type]
            return json.dumps({
                "region": region_data.get('name', region),
                "service_type": service_type,
                "status": service_data.get('status', 'Unknown'),
                "details": service_data
            })
        
        # Otherwise return full network status
        return json.dumps(network_data)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "check_network_status",
                "description": "Check network status for regions and services, including current outages and planned maintenance.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "Optional region to check, such as 'denver_co' or 'austin_tx'.",
                        },
                        "service_type": {
                            "type": "string",
                            "description": "Optional service type to check: 'mobile', 'internet', or 'tv'.",
                        },
                    },
                    "required": [],
                },
            },
        }
