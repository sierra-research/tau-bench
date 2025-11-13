
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class GetProviderDetails(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], provider_id: str) -> str:
        """Get detailed information about a healthcare provider.
        
        Args:
            provider_id: The provider's unique identifier
            
        Returns:
            Provider details as formatted string, or error message if not found
        """
        providers = data["providers"]
        
        if provider_id not in providers:
            return f"Provider with ID {provider_id} not found."
            
        provider = providers[provider_id]
        name = provider["name"]
        contact = provider["contact"]
        schedule = provider["schedule"]
        
        provider_name = f"{name.get('title', 'Dr.')} {name['first_name']} {name['last_name']}"
        
        result = f"""Provider Details (ID: {provider_id})

Name: {provider_name}
Specialty: {provider['specialty']}
License Number: {provider['license_number']}
Credentials: {', '.join(provider['credentials'])}
Years of Experience: {provider['years_experience']}

Contact Information:
- Phone: {contact['phone']}
- Email: {contact['email']}

Languages: {', '.join(provider['languages'])}
Consultation Fee: ${provider['consultation_fee']:.2f}

Weekly Schedule:"""

        for day, times in schedule.items():
            if times:
                result += f"\n- {day.title()}: {', '.join(times)}"
            else:
                result += f"\n- {day.title()}: Not available"

        return result

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_provider_details",
                "description": "Get detailed information about a healthcare provider including specialty, schedule, credentials, and contact information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "provider_id": {
                            "type": "string",
                            "description": "The provider's unique identifier",
                        },
                    },
                    "required": ["provider_id"],
                },
            },
        }
