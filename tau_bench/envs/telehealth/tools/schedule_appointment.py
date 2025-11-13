
import datetime
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class ScheduleAppointment(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        patient_id: str,
        provider_id: str,
        date: str,
        time: str,
        appointment_type: str,
        bill_insurance: bool = True,
        voucher_id: str | None = None,
        payment_notes: str | None = None,
    ) -> str:
        """Schedule a new appointment for a patient.
        
        Args:
            patient_id: The patient's unique identifier
            provider_id: The provider's unique identifier
            date: Appointment date in YYYY-MM-DD format
            time: Appointment time in HH:MM format (24-hour)
            appointment_type: Type of appointment (routine_checkup, follow_up, consultation, etc.)
            
        Returns:
            Success message with appointment ID, or error message if scheduling fails
        """
        patients = data["patients"]
        providers = data["providers"]
        appointments = data["appointments"]
        
        # Validate patient exists
        if patient_id not in patients:
            return f"Patient with ID {patient_id} not found."
            
        # Validate provider exists
        if provider_id not in providers:
            return f"Provider with ID {provider_id} not found."
        
        patient = patients[patient_id]
        provider = providers[provider_id]
        
        # Check if provider is available at the requested time
        try:
            appointment_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            day_of_week = appointment_date.strftime("%A").lower()
            
            if day_of_week not in provider["schedule"]:
                return f"Provider {provider_id} does not work on {day_of_week.title()}."
                
            available_times = provider["schedule"][day_of_week]
            if time not in available_times:
                available_times_str = ', '.join(available_times) if available_times else 'None'
                return f"Provider {provider_id} is not available at {time} on {day_of_week.title()}. Available times: {available_times_str}"
                
        except ValueError:
            return f"Invalid date format: {date}. Please use YYYY-MM-DD format."
        
        # Check for conflicts with existing appointments
        for appt_id, appt in appointments.items():
            if (appt["provider_id"] == provider_id and 
                appt["date"] == date and 
                appt["time"] == time and 
                appt["status"] in ["scheduled", "pending_approval"]):
                return f"Provider {provider_id} already has an appointment scheduled at {time} on {date}."
        
        # Generate new appointment ID
        existing_ids = [int(appt_id.replace("APPT", "")) for appt_id in appointments.keys() if appt_id.startswith("APPT")]
        new_id_num = max(existing_ids) + 1 if existing_ids else 1
        new_appointment_id = f"APPT{new_id_num:03d}"
        
        # Determine copay amount based on provider specialty
        insurance = patient["insurance"]["primary"]
        if provider["specialty"] == "Primary Care":
            base_copay = insurance["copay_primary"]
        else:
            base_copay = insurance["copay_specialist"]

        if bill_insurance:
            copay_amount = base_copay
            payment_method = "insurance"
            insurance_billed = True
            applied_voucher = None
            insurance_auth = f"AUTH{new_id_num:06d}"
        else:
            payment_method = "telehealth_voucher" if voucher_id else "self_pay"
            insurance_billed = False
            applied_voucher = voucher_id
            copay_amount = 0.0
            insurance_auth = None

        # Create new appointment
        new_appointment = {
            "appointment_id": new_appointment_id,
            "patient_id": patient_id,
            "provider_id": provider_id,
            "date": date,
            "time": time,
            "duration_minutes": 30,  # Default duration
            "type": appointment_type,
            "status": "scheduled",
            "notes": payment_notes or "",
            "insurance_authorization": insurance_auth,
            "copay_amount": copay_amount,
            "meeting_link": f"https://telehealth.healthcenter.com/room/{new_appointment_id}",
            "payment_method": payment_method,
            "voucher_id": applied_voucher,
            "insurance_billed": insurance_billed,
        }
        
        # Add to appointments data
        appointments[new_appointment_id] = new_appointment
        
        patient_name = f"{patient['name']['first_name']} {patient['name']['last_name']}"
        provider_name = f"Dr. {provider['name']['last_name']}"
        
        message_lines = [
            "Appointment successfully scheduled!",
            "",
            f"Appointment ID: {new_appointment_id}",
            f"Patient: {patient_name}",
            f"Provider: {provider_name} - {provider['specialty']}",
            f"Date: {date}",
            f"Time: {time}",
            f"Type: {appointment_type.replace('_', ' ').title()}",
        ]

        if bill_insurance:
            message_lines.append(f"Copay: ${copay_amount:.2f}")
            message_lines.append(f"Insurance Authorization: {insurance_auth}")
        else:
            message_lines.append("Insurance Billing: Skipped")
            message_lines.append(f"Payment Method: {payment_method.replace('_', ' ').title()}")
            if applied_voucher:
                message_lines.append(f"Voucher Applied: {applied_voucher}")
            message_lines.append(f"Amount Due Today: ${copay_amount:.2f}")
            if payment_notes:
                message_lines.append(f"Billing Notes: {payment_notes}")

        message_lines.append(f"Meeting Link: {new_appointment['meeting_link']}")
        message_lines.append("")
        message_lines.append("Please save your appointment ID for future reference.")

        return "\n".join(message_lines)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "schedule_appointment",
                "description": "Schedule a new telehealth appointment for a patient with a healthcare provider.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "The patient's unique identifier",
                        },
                        "provider_id": {
                            "type": "string",
                            "description": "The provider's unique identifier",
                        },
                        "date": {
                            "type": "string",
                            "description": "Appointment date in YYYY-MM-DD format",
                        },
                        "time": {
                            "type": "string",
                            "description": "Appointment time in HH:MM format (24-hour)",
                        },
                        "appointment_type": {
                            "type": "string",
                            "description": "Type of appointment (routine_checkup, follow_up, consultation, specialist_consultation, sick_visit)",
                        },
                        "bill_insurance": {
                            "type": "boolean",
                            "description": "Set to false to skip insurance billing for this appointment",
                        },
                        "voucher_id": {
                            "type": "string",
                            "description": "Optional voucher identifier applied to this appointment",
                        },
                        "payment_notes": {
                            "type": "string",
                            "description": "Optional notes regarding payment handling",
                        },
                    },
                    "required": ["patient_id", "provider_id", "date", "time", "appointment_type"],
                },
            },
        }
