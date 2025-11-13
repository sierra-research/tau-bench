
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class TransferToHumanSupport(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], summary: str) -> str:
        # This method simulates the transfer to a human support agent.
        return "Transfer successful"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "transfer_to_human_support",
                "description": (
                    "Transfer the customer to a human support agent, with a summary of the customer's issue. "
                    "Only transfer if the customer explicitly asks for a human agent, or if the customer's issue cannot be resolved with the available tools."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "A summary of the customer's issue.",
                        },
                    },
                    "required": ["summary"],
                },
            },
        }
