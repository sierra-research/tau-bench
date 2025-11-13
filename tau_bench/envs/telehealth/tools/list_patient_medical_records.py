from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


class ListPatientMedicalRecords(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], patient_id: str, limit: int | None = None) -> str:
        records: Dict[str, Dict[str, Any]] = data["medical_records"]
        filtered: List[Dict[str, Any]] = [
            record for record in records.values() if record.get("patient_id") == patient_id
        ]
        if not filtered:
            return f"No medical records found for patient {patient_id}."

        def _parse_date(record: Dict[str, Any]) -> datetime:
            return datetime.strptime(record.get("date", "1900-01-01"), "%Y-%m-%d")

        filtered.sort(key=_parse_date, reverse=True)
        if limit is not None and limit > 0:
            filtered = filtered[:limit]

        lines: List[str] = []
        for record in filtered:
            prescriptions = record.get("prescriptions", [])
            medication_list = ", ".join(item.get("medication") for item in prescriptions) if prescriptions else "None recorded"
            lines.append(
                " | ".join(
                    [
                        f"record_id={record['record_id']}",
                        f"date={record['date']}",
                        f"appointment_id={record['appointment_id']}",
                        f"medications={medication_list}",
                    ]
                )
            )
        return "Medical records (newest first):\n" + "\n".join(lines)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_patient_medical_records",
                "description": "List medical record identifiers for a patient sorted with the newest first.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "ID of the patient",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Optional maximum number of records to return",
                        },
                    },
                    "required": ["patient_id"],
                },
            },
        }
