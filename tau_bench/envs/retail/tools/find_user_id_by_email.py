# Copyright Sierra

from typing import Any, Dict


def find_user_id_by_email(data: Dict[str, Any], email: str) -> str:
    users = data["users"]
    for user_id, profile in users.items():
        if profile["email"].lower() == email.lower():
            return user_id
    return "Error: user not found"


find_user_id_by_email.__info__ = {
    "type": "function",
    "function": {
        "name": "find_user_id_by_email",
        "description": "Find user id by email. If the user is not found, the function will return an error message.",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "The email of the user, such as 'something@example.com'.",
                },
            },
            "required": ["email"],
        },
    },
}
