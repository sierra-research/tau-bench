from __future__ import annotations

import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class UpdateMedicalRecordNote(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        record_id: str,
        note: str,
        metadata: Dict[str, Any] | None = None,
    ) -> str:
        records = data.get("medical_records", {})
        record = records.get(record_id)
        if not record:
            return f"Error: medical record {record_id} not found"

        notes = record.setdefault("notes", [])
        entry = {"note": note}
        if metadata:
            entry["metadata"] = metadata
        notes.append(entry)

        return json.dumps(record)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "update_medical_record_note",
                "description": "Append an audit or compliance note to a medical record.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "record_id": {
                            "type": "string",
                            "description": "Identifier of the medical record to update",
                        },
                        "note": {
                            "type": "string",
                            "description": "Note text to append",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Optional structured metadata to attach",
                        },
                    },
                    "required": ["record_id", "note"],
                },
            },
        }

