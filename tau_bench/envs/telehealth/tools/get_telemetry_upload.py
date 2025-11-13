from __future__ import annotations

import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class GetTelemetryUpload(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], device_id: str, date: str) -> str:
        uploads = data.get("telemetry_uploads", [])
        for entry in uploads:
            if entry.get("device_id") == device_id and entry.get("date") == date:
                return json.dumps(entry)
        return (
            "No telemetry upload found for device "
            f"{device_id} on {date}."
        )

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_telemetry_upload",
                "description": "Retrieve a specific telemetry upload artifact for a device and date.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Unique identifier of the telemetry device",
                        },
                        "date": {
                            "type": "string",
                            "description": "Target date (YYYY-MM-DD)",
                        },
                    },
                    "required": ["device_id", "date"],
                },
            },
        }

