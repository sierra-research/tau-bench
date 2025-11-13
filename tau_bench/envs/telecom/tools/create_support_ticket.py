# Verified

import json
from datetime import datetime
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class CreateSupportTicket(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], customer_id: str, category: str, priority: str = "medium") -> str:
        tickets = data.get("support_tickets", {})
        customers = data.get("customers", {})
        
        if customer_id not in customers:
            return f"Error: Customer not found: {customer_id}"
        
        valid_categories = ["mobile", "internet", "tv", "billing", "account", "device", "security", "phone"]
        if category not in valid_categories:
            return f"Error: Invalid category: {category}. Valid categories: {', '.join(valid_categories)}"
        
        valid_priorities = ["low", "medium", "high", "urgent"]
        if priority not in valid_priorities:
            return f"Error: Invalid priority: {priority}. Valid priorities: {', '.join(valid_priorities)}"
        
        # Generate ticket ID (in real system, this would be more sophisticated)
        # get the len of the tickets and add 1
        ticket_id = f"TICKET{len(tickets) + 1:03d}"

        tickets[ticket_id] = {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "status": "open",
            "priority": priority,
            "category": category,
        }
        
        return f"Success: Created support ticket {ticket_id} for customer {customer_id}"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_support_ticket",
                "description": "Create a new support ticket for a customer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The customer's unique identifier, such as 'john_smith_1234'.",
                        },
                        "category": {
                            "type": "string",
                            "description": "Ticket category: 'mobile', 'internet', 'tv', 'billing', 'account', 'device', 'security', or 'phone'.",
                        },
                        "priority": {
                            "type": "string",
                            "description": "Priority level: 'low', 'medium', 'high', or 'urgent'. Defaults to 'medium'. \
                            Low is non-urgent, medium is standard, high is important, and urgent is critical (within 24 hours)",
                        },
                    },
                    "required": ["customer_id", "category"],
                },
            },
        }