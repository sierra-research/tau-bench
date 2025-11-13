
import datetime
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class RescheduleAppointment(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], appointment_id: str, new_date: str, new_time: str) -> str:
        """Reschedule an existing appointment to a new date and time.
        
        Args:
            appointment_id: The appointment's unique identifier
            new_date: New appointment date in YYYY-MM-DD format
            new_time: New appointment time in HH:MM format (24-hour)
            
        Returns:
            Success message or error message if rescheduling fails
        """
        appointments = data["appointments"]
        providers = data["providers"]
        patients = data["patients"]
        
        if appointment_id not in appointments:
            return f"Appointment with ID {appointment_id} not found."
            
        appointment = appointments[appointment_id]
        
        # Check if appointment can be rescheduled
        if appointment["status"] == "cancelled":
            return f"Cannot reschedule appointment {appointment_id} - appointment has been cancelled."
            
        if appointment["status"] == "completed":
            return f"Cannot reschedule appointment {appointment_id} - appointment has already been completed."
        
        provider_id = appointment["provider_id"]
        provider = providers[provider_id]
        
        # Check if provider is available at the new time
        try:
            appointment_date = datetime.datetime.strptime(new_date, "%Y-%m-%d")
            day_of_week = appointment_date.strftime("%A").lower()
            
            if day_of_week not in provider["schedule"]:
                return f"Provider {provider_id} does not work on {day_of_week.title()}."
                
            available_times = provider["schedule"][day_of_week]
            if new_time not in available_times:
                available_times_str = ', '.join(available_times) if available_times else 'None'
                return f"Provider {provider_id} is not available at {new_time} on {day_of_week.title()}. Available times: {available_times_str}"
                
        except ValueError:
            return f"Invalid date format: {new_date}. Please use YYYY-MM-DD format."
        
        # Check for conflicts with existing appointments
        for appt_id, appt in appointments.items():
            if (appt_id != appointment_id and  # Don't check against the appointment being rescheduled
                appt["provider_id"] == provider_id and 
                appt["date"] == new_date and 
                appt["time"] == new_time and 
                appt["status"] in ["scheduled", "pending_approval"]):
                return f"Provider {provider_id} already has an appointment scheduled at {new_time} on {new_date}."
        
        # Store old details for confirmation
        old_date = appointment["date"]
        old_time = appointment["time"]
        
        # Update appointment
        appointment["date"] = new_date
        appointment["time"] = new_time
        
        # Get patient and provider info for confirmation message
        patient = patients.get(appointment["patient_id"], {})
        patient_name = f"{patient.get('name', {}).get('first_name', 'Unknown')} {patient.get('name', {}).get('last_name', 'Patient')}"
        provider_name = f"Dr. {provider.get('name', {}).get('last_name', 'Unknown Provider')}"
        
        return f"""Appointment successfully rescheduled.

Appointment ID: {appointment_id}
Patient: {patient_name}
Provider: {provider_name} - {provider['specialty']}

Previous Date/Time: {old_date} at {old_time}
New Date/Time: {new_date} at {new_time}

Meeting Link: {appointment['meeting_link']}

Please update your calendar with the new appointment time."""

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "reschedule_appointment",
                "description": "Reschedule an existing appointment to a new date and time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "appointment_id": {
                            "type": "string",
                            "description": "The appointment's unique identifier",
                        },
                        "new_date": {
                            "type": "string",
                            "description": "New appointment date in YYYY-MM-DD format",
                        },
                        "new_time": {
                            "type": "string",
                            "description": "New appointment time in HH:MM format (24-hour)",
                        },
                    },
                    "required": ["appointment_id", "new_date", "new_time"],
                },
            },
        }
