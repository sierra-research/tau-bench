
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class GetAppointmentDetails(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], appointment_id: str) -> str:
        """Get detailed information about an appointment.
        
        Args:
            appointment_id: The appointment's unique identifier
            
        Returns:
            Appointment details as formatted string, or error message if not found
        """
        appointments = data["appointments"]
        patients = data["patients"]
        providers = data["providers"]
        
        if appointment_id not in appointments:
            return f"Appointment with ID {appointment_id} not found."
            
        appointment = appointments[appointment_id]
        patient = patients.get(appointment["patient_id"], {})
        provider = providers.get(appointment["provider_id"], {})
        
        patient_name = f"{patient.get('name', {}).get('first_name', 'Unknown')} {patient.get('name', {}).get('last_name', 'Patient')}"
        provider_name = f"Dr. {provider.get('name', {}).get('last_name', 'Unknown Provider')}"
        provider_specialty = provider.get('specialty', 'Unknown')
        
        result = f"""Appointment Details (ID: {appointment_id})

Patient: {patient_name} (ID: {appointment['patient_id']})
Provider: {provider_name} - {provider_specialty} (ID: {appointment['provider_id']})

Appointment Information:
- Date: {appointment['date']}
- Time: {appointment['time']}
- Duration: {appointment['duration_minutes']} minutes
- Type: {appointment['type'].replace('_', ' ').title()}
- Status: {appointment['status'].replace('_', ' ').title()}

Clinical Information:
- Chief Complaint: {appointment['chief_complaint']}
- Notes: {appointment['notes']}

Billing Information:
- Insurance Authorization: {appointment['insurance_authorization']}
- Copay Amount: ${appointment['copay_amount']:.2f}

Meeting Information:
- Meeting Link: {appointment['meeting_link']}"""

        # Add additional fields if they exist
        if "prescription_issued" in appointment:
            prescription = appointment["prescription_issued"]
            result += f"\n\nPrescription Issued:\n- {prescription['medication']} {prescription['dosage']} {prescription['frequency']}\n- Quantity: {prescription['quantity']}, Refills: {prescription['refills']}"
            
        if "referral_from" in appointment:
            result += f"\n\nReferral from: {appointment['referral_from']}"
            
        if "cancellation_reason" in appointment:
            result += f"\n\nCancellation Details:\n- Reason: {appointment['cancellation_reason'].replace('_', ' ').title()}\n- Date: {appointment['cancellation_date']}"

        return result

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_appointment_details",
                "description": "Get detailed information about a scheduled appointment including patient, provider, date, time, and clinical details.",
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
