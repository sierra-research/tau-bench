
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class GetPatientDetails(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], patient_id: str) -> str:
        """Get detailed information about a patient.
        
        Args:
            patient_id: The patient's unique identifier
            
        Returns:
            Patient details as formatted string, or error message if not found
        """
        patients = data["patients"]
        
        if patient_id not in patients:
            return f"Patient with ID {patient_id} not found."
            
        patient = patients[patient_id]
        
        # Format patient information
        name = f"{patient['name']['first_name']} {patient['name']['last_name']}"
        demographics = patient["demographics"]
        address = patient["address"]
        insurance = patient["insurance"]["primary"]
        medical_history = patient["medical_history"]
        emergency_contact = patient["emergency_contact"]
        
        result = f"""Patient Details for {name} (ID: {patient_id})

Demographics:
- Date of Birth: {demographics['date_of_birth']}
- Gender: {demographics['gender']}
- Phone: {demographics['phone']}
- Email: {demographics['email']}

Address:
- {address['address1']}
- {address['address2']}
- {address['city']}, {address['state']} {address['zip']}
- {address['country']}

Insurance:
- Provider: {insurance['provider']}
- Policy Number: {insurance['policy_number']}
- Primary Care Copay: ${insurance['copay_primary']:.2f}
- Specialist Copay: ${insurance['copay_specialist']:.2f}

Medical History:
- Conditions: {', '.join(medical_history['conditions']) if medical_history['conditions'] else 'None'}
- Allergies: {', '.join(medical_history['allergies']) if medical_history['allergies'] else 'None'}
- Current Medications: {', '.join([f"{med['name']} {med['dosage']} {med['frequency']}" for med in medical_history['medications']]) if medical_history['medications'] else 'None'}

Emergency Contact:
- {emergency_contact['name']} ({emergency_contact['relationship']})
- Phone: {emergency_contact['phone']}"""

        return result

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_patient_details",
                "description": "Get detailed information about a patient including demographics, address, insurance, and medical history.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "The patient's unique identifier",
                        },
                    },
                    "required": ["patient_id"],
                },
            },
        }
