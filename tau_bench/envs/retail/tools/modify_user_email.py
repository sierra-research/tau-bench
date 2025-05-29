# Copyright Sierra

import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool


class ModifyUserEmail(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        user_id: str,
        email: str,
    ) -> str:
        users = data["users"]
        # Check if the user exists
        if user_id not in users:
            return "Error: user not found"
        # Check if the email is valid
        if "@" not in email or "." not in email.split("@")[-1]:
            return "Error: invalid email format"
        # Check if the email is already in use
        for user in users:
            if users[user]["email"] == email:
                return "Error: email already in use by another user"
        user = users[user_id]
        user["email"] = email
        return json.dumps(user)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "modify_user_email",
                "description": "Modify the default email of a user. The agent needs to explain the modification detail and ask for explicit user confirmation (yes/no) to proceed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "The user id, such as 'noah_brown_6181'.",
                        },
                        "email": {
                            "type": "string",
                            "description": "The new email address, such as noah.brown7922@example.com",
                        },
                    },
                    "required": [
                        "user_id",
                        "email",
                    ],
                },
            },
        }
