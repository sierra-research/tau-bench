# Verified

import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class ModifySupportTicket(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], ticket_id: str, status: str, priority: str) -> str:
        tickets = data.get("support_tickets", {})
        
        if ticket_id not in tickets:
            return f"Error: Support ticket not found: {ticket_id}"
        
        tickets[ticket_id]["status"] = status
        tickets[ticket_id]["priority"] = priority
        
        return f"Success: Modified support ticket {ticket_id} with status {status} and priority {priority}"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "modify_support_ticket",
                "description": "Modify the status and priority of a support ticket.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "The support ticket identifier, such as 'TICKET001'.",
                        },
                        "status": {
                            "type": "string",
                            "description": "The status of the support ticket, such as 'open' or 'closed'.",
                        },
                        "priority": {
                            "type": "string",
                            "description": "The priority of the support ticket, such as 'low', 'medium', 'high', or 'urgent'.",
                        },
                    },
                    "required": ["ticket_id", "status", "priority"],
                },
            },
        }