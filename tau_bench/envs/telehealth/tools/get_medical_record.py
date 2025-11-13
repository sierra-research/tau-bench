from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool


class GetMedicalRecord(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        record_id: Optional[str] = None,
        appointment_id: Optional[str] = None,
    ) -> str:
        """Retrieve a medical record by record ID or appointment ID."""
        medical_records = data.get("medical_records", {})
        appointments = data.get("appointments", {})
        patients = data.get("patients", {})
        providers = data.get("providers", {})

        if not record_id and not appointment_id:
            return "Please provide a record_id or appointment_id to look up the medical record."

        record = None
        if record_id:
            record = medical_records.get(record_id)
            if record is None:
                return f"Medical record with ID {record_id} not found."
        else:
            for candidate in medical_records.values():
                if candidate.get("appointment_id") == appointment_id:
                    record = candidate
                    break
            if record is None:
                return (
                    f"No medical record found for appointment ID {appointment_id}."
                )

        appointment = appointments.get(record.get("appointment_id", ""), {})
        patient = patients.get(record.get("patient_id", ""), {})
        provider = providers.get(record.get("provider_id", ""), {})

        patient_name = " ".join(
            filter(
                None,
                [
                    patient.get("name", {}).get("first_name"),
                    patient.get("name", {}).get("last_name"),
                ],
            )
        ).strip() or "Unknown Patient"
        provider_name = " ".join(
            filter(
                None,
                [
                    provider.get("name", {}).get("title"),
                    provider.get("name", {}).get("first_name"),
                    provider.get("name", {}).get("last_name"),
                ],
            )
        ).strip() or "Unknown Provider"

        lines = [
            f"Medical Record (ID: {record['record_id']})",
            f"Patient: {patient_name} (ID: {record.get('patient_id', 'Unknown')})",
            f"Provider: {provider_name} (ID: {record.get('provider_id', 'Unknown')})",
        ]

        if appointment:
            lines.append(
                (
                    f"Related Appointment: {appointment.get('appointment_id', 'Unknown')} "
                    f"on {appointment.get('date', 'Unknown Date')} at {appointment.get('time', 'Unknown Time')}"
                )
            )

        lines.append(f"Date: {record.get('date', 'Unknown Date')}")
        lines.append(f"Type: {record.get('type', 'Unknown')}")

        for key in ["subjective", "objective", "assessment", "plan"]:
            if key in record:
                lines.append(f"{key.title()}: {record[key]}")

        if "recommendations" in record and record["recommendations"]:
            lines.append("Recommendations:")
            for rec in record["recommendations"]:
                lines.append(f"- {rec}")

        return "\n".join(lines)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_medical_record",
                "description": "Retrieve a patient's medical record by record ID or related appointment ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "record_id": {
                            "type": "string",
                            "description": "The unique medical record identifier.",
                        },
                        "appointment_id": {
                            "type": "string",
                            "description": "The appointment ID associated with the medical record.",
                        },
                    },
                    "required": [],
                },
            },
        }
