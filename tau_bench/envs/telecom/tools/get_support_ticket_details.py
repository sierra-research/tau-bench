# Verified

import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class GetSupportTicketDetails(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], ticket_id: str) -> str:
        tickets = data.get("support_tickets", {})
        
        if ticket_id not in tickets:
            return f"Error: Support ticket not found: {ticket_id}"
        
        return json.dumps(tickets[ticket_id])

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_support_ticket_details",
                "description": "Get details of a support ticket.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "The support ticket identifier, such as 'TICKET001'.",
                        },
                    },
                    "required": ["ticket_id"],
                },
            },
        }