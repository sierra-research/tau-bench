
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool


class ListAvailableProviders(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], specialty: Optional[str] = None) -> str:
        """List all available healthcare providers, optionally filtered by specialty.
        
        Args:
            specialty: Optional specialty to filter by (e.g., "Primary Care", "Cardiology")
            
        Returns:
            List of available providers as formatted string
        """
        providers = data["providers"]
        
        filtered_providers = []
        for provider_id, provider_info in providers.items():
            if specialty is None or provider_info["specialty"].lower() == specialty.lower():
                filtered_providers.append((provider_id, provider_info))
        
        if not filtered_providers:
            if specialty:
                return f"No providers found with specialty: {specialty}"
            else:
                return "No providers found."
        
        result = f"Available Providers{f' - {specialty}' if specialty else ''}:\n\n"
        
        for provider_id, provider_info in filtered_providers:
            name = provider_info["name"]
            provider_name = f"{name.get('title', 'Dr.')} {name['first_name']} {name['last_name']}"
            
            result += f"• {provider_name} (ID: {provider_id})\n"
            result += f"  Specialty: {provider_info['specialty']}\n"
            result += f"  Experience: {provider_info['years_experience']} years\n"
            result += f"  Languages: {', '.join(provider_info['languages'])}\n"
            result += f"  Consultation Fee: ${provider_info['consultation_fee']:.2f}\n"
            result += f"  Phone: {provider_info['contact']['phone']}\n\n"
        
        return result.strip()

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_available_providers",
                "description": "List all available healthcare providers, optionally filtered by specialty (e.g., Primary Care, Cardiology, Dermatology, Psychiatry).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "specialty": {
                            "type": "string",
                            "description": "Optional specialty to filter providers by (e.g., 'Primary Care', 'Cardiology', 'Dermatology', 'Psychiatry')",
                        },
                    },
                    "required": [],
                },
            },
        }
