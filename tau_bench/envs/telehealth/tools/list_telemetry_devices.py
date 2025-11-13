import json
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


class ListTelemetryDevices(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        status_filter: str | None = None,
        limit: int | None = None,
    ) -> str:
        inventory: List[Dict[str, Any]] = data.get("telemetry_inventory", [])
        if not inventory:
            return "Telemetry inventory is empty."

        filtered = inventory
        if status_filter:
            filtered = [item for item in filtered if item.get("status", "").lower() == status_filter.lower()]
            if not filtered:
                return f"No telemetry devices with status {status_filter}."

        filtered = sorted(filtered, key=lambda item: item.get("device_id", ""))
        if limit is not None and limit > 0:
            filtered = filtered[:limit]

        lines = []
        for entry in filtered:
            lines.append(
                f"{entry.get('device_id')} | status={entry.get('status')} | last_audit={entry.get('last_audit')} | notes={entry.get('notes')}"
            )

        return "Telemetry devices:\n" + "\n".join(lines)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_telemetry_devices",
                "description": "List telemetry wearable devices optionally filtered by status.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status_filter": {
                            "type": "string",
                            "description": "Optional status filter (e.g., 'available', 'missing_overdue').",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Optional maximum number of devices to list.",
                        },
                    },
                    "required": [],
                },
            },
        }

