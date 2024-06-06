# Copyright Sierra

from typing import Any, Dict


def think(data: Dict[str, Any], thought: str) -> str:
    return ""


think.__info__ = {
    "type": "function",
    "function": {
        "name": "think",
        "description": "Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning is needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "thought": {
                    "type": "string",
                    "description": "A thought to think about.",
                },
            },
            "required": ["thought"],
        },
    },
}
