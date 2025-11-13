import datetime
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool


class ListPatientAppointments(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        patient_id: str,
        status_filter: Optional[str] = None,
    ) -> str:
        """List appointments associated with a patient, optionally filtered by status."""
        patients = data["patients"]
        appointments = data["appointments"]
        providers = data["providers"]

        if patient_id not in patients:
            return f"Patient with ID {patient_id} not found."

        normalized_filter = status_filter.lower() if status_filter else None

        patient_appointments = []
        for appt_id, appointment in appointments.items():
            if appointment.get("patient_id") != patient_id:
                continue
            if normalized_filter and appointment.get("status", "").lower() != normalized_filter:
                continue
            patient_appointments.append((appt_id, appointment))

        if not patient_appointments:
            if normalized_filter:
                return (
                    f"No appointments found for patient {patient_id} with status "
                    f"{status_filter}."
                )
            return f"No appointments found for patient {patient_id}."

        def sort_key(item: Any) -> Any:
            appt_id, appointment = item
            date_str = appointment.get("date", "0001-01-01")
            time_str = appointment.get("time", "00:00")
            try:
                dt_value = datetime.datetime.strptime(
                    f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
                )
            except ValueError:
                dt_value = datetime.datetime.min
            return dt_value, appt_id

        patient_appointments.sort(key=sort_key)

        patient = patients[patient_id]
        patient_name = (
            f"{patient['name']['first_name']} {patient['name']['last_name']}"
        )
        header = f"Appointments for {patient_name} (ID: {patient_id})"
        if normalized_filter:
            header += f" with status {status_filter}"

        lines = [header]
        for appt_id, appointment in patient_appointments:
            provider = providers.get(appointment.get("provider_id", ""), {})
            provider_last_name = provider.get("name", {}).get("last_name", "Unknown")
            provider_title = provider.get("name", {}).get("title", "Dr.")
            provider_specialty = provider.get("specialty", "Unknown Specialty")
            provider_label = f"{provider_title} {provider_last_name}"
            status_readable = appointment.get("status", "Unknown").replace(
                "_", " "
            ).title()
            appointment_type = appointment.get("type", "").replace(
                "_", " "
            ).title()
            lines.append(
                (
                    f"- {appt_id}: {appointment.get('date')} at {appointment.get('time')} "
                    f"with {provider_label} ({provider_specialty}) [{status_readable}, "
                    f"Type: {appointment_type}]"
                )
            )

        return "\n".join(lines)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_patient_appointments",
                "description": (
                    "List all appointments for a patient, optionally filtering by an "
                    "appointment status such as scheduled, pending_approval, or cancelled."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "The patient's unique identifier.",
                        },
                        "status_filter": {
                            "type": "string",
                            "description": (
                                "Optional appointment status filter (e.g., "
                                "'scheduled', 'pending_approval', 'cancelled')."
                            ),
                        },
                    },
                    "required": ["patient_id"],
                },
            },
        }
