# Copyright Sierra

import json
from typing import Any, Dict, List

from termcolor import colored


def display_conversation(
    messages: List[Dict[str, Any]], include_system_messages: bool = True
) -> str:
    message_displays = []
    for message in messages:
        if not isinstance(message, dict):
            message_displays.append(str(message.tool_calls[0].function))
            continue
        if message["role"] == "system" and include_system_messages:
            message_displays.append(f"system: {message['content']}")
        elif message["role"] == "user":
            message_displays.append(f"user: {message['content']}")
        elif message["role"] == "assistant" and message.get("tool_calls"):
            message_displays.append(f"assistant: {json.dumps(message['tool_calls'][0])}")
        elif message["role"] == "assistant" and not message.get("tool_calls"):
            message_displays.append(f"assistant: {message['content']}")
        elif message["role"] == "tool":
            message_displays.append(f"tool ({message['name']}): {message['content']}")
    return "\n".join(message_displays)


def pretty_print_conversation(messages: List[Dict[str, Any]]) -> None:
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "yellow",
        "tool": "magenta",
    }

    for message in messages:
        if not isinstance(message, dict):
            print(colored(str(message.tool_calls[0].function)))
            continue
        if message["role"] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and message.get("function_call"):
            print(
                colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]])
            )
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "tool":
            print(
                colored(
                    f"tool ({message['name']}): {message['content']}\n",
                    role_to_color[message["role"]],
                )
            )


def message_to_action(message):
    if message.tool_calls is not None:
        tool_call = message.tool_calls[0]
        return {
            "name": tool_call.function.name,
            "arguments": json.loads(tool_call.function.arguments),
        }
    else:
        return {"name": "respond", "arguments": {"content": message.content}}


def message_to_dict(message):
    if isinstance(message, dict):
        return message
    else:
        return {"role": "assistant", "function_call": str(message.tool_calls[0].function)}
