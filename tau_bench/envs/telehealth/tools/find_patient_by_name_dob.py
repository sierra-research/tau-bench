
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class FindPatientByNameDOB(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], first_name: str, last_name: str, date_of_birth: str) -> str:
        """Find patient by name and date of birth.
        
        Args:
            data: The environment data containing patients information
            first_name: Patient's first name
            last_name: Patient's last name
            date_of_birth: Patient's date of birth (YYYY-MM-DD format)
            
        Returns:
            Patient ID if found, error message if not found
        """
        patients = data["patients"]
        
        for patient_id, patient_info in patients.items():
            if (patient_info["name"]["first_name"].lower() == first_name.lower() and
                patient_info["name"]["last_name"].lower() == last_name.lower() and
                patient_info["demographics"]["date_of_birth"] == date_of_birth):
                return patient_id
                
        return f"No patient found with name: {first_name} {last_name} and DOB: {date_of_birth}"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "find_patient_by_name_dob",
                "description": "Find a patient by their full name and date of birth to authenticate their identity.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "first_name": {
                            "type": "string",
                            "description": "The patient's first name",
                        },
                        "last_name": {
                            "type": "string",
                            "description": "The patient's last name",
                        },
                        "date_of_birth": {
                            "type": "string",
                            "description": "The patient's date of birth in YYYY-MM-DD format",
                        },
                    },
                    "required": ["first_name", "last_name", "date_of_birth"],
                },
            },
        }
