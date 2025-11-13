
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class TransferToHumanSupport(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], reason: str) -> str:
        """Transfer the patient to human support staff.
        
        Args:
            reason: Reason for transferring to human support
            
        Returns:
            Transfer confirmation message
        """
        return f"""Transferring you to a human support representative.

Reason for transfer: {reason}

Please hold while we connect you to a member of our support team. They will be able to assist you with your request.

Estimated wait time: 2-3 minutes.

Thank you for your patience."""

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "transfer_to_human_support",
                "description": "Transfer the patient to human support staff when the request cannot be handled by the automated system.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for transferring to human support",
                        },
                    },
                    "required": ["reason"],
                },
            },
        }
