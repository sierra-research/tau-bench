from __future__ import annotations

import json
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


class ListTelemetryUploads(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        device_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
    ) -> str:
        uploads: List[Dict[str, Any]] = data.get("telemetry_uploads", [])

        def in_range(entry: Dict[str, Any]) -> bool:
            if entry.get("device_id") != device_id:
                return False
            entry_date = entry.get("date")
            if start_date and entry_date < start_date:
                return False
            if end_date and entry_date > end_date:
                return False
            return True

        filtered = [entry for entry in uploads if in_range(entry)]
        filtered.sort(key=lambda item: item.get("date"))

        if limit is not None and limit > 0:
            filtered = filtered[:limit]

        if not filtered:
            return (
                "No telemetry uploads found for device "
                f"{device_id} in the specified window."
            )

        return json.dumps(filtered)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_telemetry_uploads",
                "description": "List telemetry upload artifacts for a device over an optional date window.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Unique identifier of the telemetry device",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date (inclusive, YYYY-MM-DD)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (inclusive, YYYY-MM-DD)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Optional maximum number of entries to return",
                        },
                    },
                    "required": ["device_id"],
                },
            },
        }

