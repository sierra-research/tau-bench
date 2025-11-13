
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class FindPatientByEmail(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], email: str) -> str:
        """Find patient by email address.
        
        Args:
            data: The environment data containing patients information
            email: Patient's email address
            
        Returns:
            Patient ID if found, error message if not found
        """
        patients = data["patients"]
        
        for patient_id, patient_info in patients.items():
            if patient_info["demographics"]["email"] == email:
                return patient_id
                
        return f"No patient found with email: {email}"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "find_patient_by_email",
                "description": "Find a patient by their email address to authenticate their identity.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The patient's email address",
                        },
                    },
                    "required": ["email"],
                },
            },
        }
