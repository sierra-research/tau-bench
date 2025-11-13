
from datetime import datetime
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class CancelAppointment(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], appointment_id: str) -> str:
        """Cancel a scheduled appointment.
        
        Args:
            appointment_id: The appointment's unique identifier
            
        Returns:
            Success message or error message if cancellation fails
        """
        appointments = data["appointments"]
        patients = data["patients"]
        providers = data["providers"]
        
        if appointment_id not in appointments:
            return f"Appointment with ID {appointment_id} not found."
            
        appointment = appointments[appointment_id]
        
        # Check if appointment can be cancelled
        if appointment["status"] == "cancelled":
            return f"Appointment {appointment_id} is already cancelled."
            
        if appointment["status"] == "completed":
            return f"Cannot cancel appointment {appointment_id} - appointment has already been completed."
        
        # Update appointment status
        appointment["status"] = "cancelled"
        appointment["cancellation_reason"] = "patient_cancelled"
        appointment["cancellation_date"] = datetime.now().strftime("%Y-%m-%d")
        
        # Get patient and provider info for confirmation message
        patient = patients.get(appointment["patient_id"], {})
        provider = providers.get(appointment["provider_id"], {})
        
        patient_name = f"{patient.get('name', {}).get('first_name', 'Unknown')} {patient.get('name', {}).get('last_name', 'Patient')}"
        provider_name = f"Dr. {provider.get('name', {}).get('last_name', 'Unknown Provider')}"
        
        return f"""Appointment successfully cancelled.

Appointment ID: {appointment_id}
Patient: {patient_name}
Provider: {provider_name}
Original Date/Time: {appointment['date']} at {appointment['time']}
Cancellation Reason: {appointment['cancellation_reason'].replace('_', ' ').title()}
Cancellation Date: {appointment['cancellation_date']}

The appointment slot is now available for other patients. If this was a patient cancellation, please remind them of the cancellation policy."""

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "cancel_appointment",
                "description": "Cancel a scheduled appointment.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "appointment_id": {
                            "type": "string",
                            "description": "The appointment's unique identifier",
                        },
                    },
                    "required": ["appointment_id"],
                },
            },
        }
