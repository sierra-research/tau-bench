# Copyright Sierra

import json
from typing import Any, Dict, List, Optional, Union

from tau_bench.agents.gpt_function_calling_agent import GPTFunctionCallingAgent


class CustomFunctionCallingAgent(GPTFunctionCallingAgent):
    def __init__(
        self, tools, wiki, model_name_or_path: str, num_gpus: Optional[int] = None
    ) -> None:
        self.tools = tools
        self.wiki = wiki
        self.reset()

        from vllm import LLM, SamplingParams

        if num_gpus is not None:
            self.num_gpus = num_gpus
        else:
            import torch

            self.num_gpus = torch.cuda.device_count()
        self.model = LLM(model_name_or_path, tensor_parallel_size=self.num_gpus)

        def generate(
            messages: List[Dict[str, str]],
            model: LLM,
            tools: Optional[List[dict]] = None,
            temperature: float = 0.0,
        ) -> Dict[str, Union[str, Dict[str, str]]]:
            if len(messages) == 0:
                raise ValueError("messages must have at least one message")
            elif messages[-1]["role"] != "user":
                raise ValueError("Last message must be from the user")
            if tools is not None and len(tools) > 0:
                messages[-1]["content"] += "\n\n" + tools_to_prompt(tools)
            messages[-1]["content"] += "\n\nassistant:"
            sampling_params = SamplingParams(temperature=temperature)
            outputs = model.generate(
                [messages_to_prompt(messages)], sampling_params=sampling_params
            )
            if len(outputs) == 0:
                raise ValueError("No outputs generated")
            completion = outputs[0].strip()
            if tools is not None and len(tools) > 0:
                # check that the function call parses correctly
                func_call = parse_function_call(
                    completion, [tool["name"] for tool in tools]
                )
                return {
                    "role": "assistant",
                    "content": {
                        "name": func_call["name"],
                        "arguments": json.dumps(func_call["arguments"]),
                    },
                }
            return {"role": "assistant", "content": completion}

        self.generate = generate

    def reset(self):
        self.messages = [{"role": "system", "content": self.wiki}]

    def act(self, env, index=None, verbose=False, temperature=0.0):
        self.reset()
        obs, info = env.reset(index=index)
        reward = 0
        self.messages.append({"role": "user", "content": obs})
        if verbose:
            self.render(1)
        for _ in range(30):
            message = self.generate(self.messages, self.model, self.tools, temperature)
            action = message_to_action(message)
            obs, reward, done, info = env.step(action)
            if action["name"] == "respond":
                self.messages.append({"role": "assistant", "content": message.content})
                self.messages.append({"role": "user", "content": obs})
            else:
                self.messages.append(message)
            if verbose:
                self.render(2)
            if done:
                break
        return reward, info


def message_to_action(message: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    if isinstance(message["content"], str):
        return {"name": "respond", "arguments": {"content": message["content"]}}
    arguments = message["content"]["arguments"]
    parsed_arguments = json.loads(arguments)
    return {"name": message["content"]["name"], "arguments": parsed_arguments}


def messages_to_prompt(messages: List[Dict[str, Union[str, Dict[str, str]]]]) -> str:
    return "\n\n".join(
        [f"{message['role']}: {message['content']}" for message in messages]
    )


def parse_function_call(text: str, available_tools_names: List[str]) -> Dict[str, Any]:
    try:
        obj = json.loads(text)
        if not isinstance(obj, dict):
            raise ToolCallingParsingError("JSON must be an object")
        if "name" not in obj:
            raise ToolCallingParsingError("JSON object must have a 'name' field")
        name = obj["name"]
        if name not in available_tools_names:
            raise ToolCallingToolDoesNotExistError(f"Tool {name} does not exist")
        if "arguments" not in obj:
            raise ToolCallingInvalidArgumentsError(
                "Tool must have an 'arguments' field"
            )
        return obj

    except json.JSONDecodeError as e:
        raise ToolCallingParsingError(f"Error parsing JSON: {e}")


AVAILABLE_TOOLS_HEADER = "Available Tools"


def tool_use_few_shot() -> str:
    return f"""Example of tool use:

# {AVAILABLE_TOOLS_HEADER}
[
    {{
        "name": "search_web",
        "description": "Perform a web search given a query.",
        "parameters": {{
            "type": "object",
            "properties": {{
                "query": {{
                    "type": "string",
                    "description": "The query to search by"
                }}
            }},
            "required": ["query"]
        }}
    }},
    {{
        "name": "book_flight",
        "description": "Book a flight given a departure and destination.",
        "parameters": {{
            "type": "object",
            "properties": {{
                "departure": {{
                    "type": "string",
                    "description": "The departure location"
                }},
                "destination": {{
                    "type": "string",
                    "description": "The destination location"
                }}
            }},
            "required": ["departure", "destination"]
        }}
    }}
]

assistant: {{
    "name": "book_flight",
    "arguments": "{{\\"departure\\": \\"New York\\", \\"destination\\": \\"Los Angeles\\"}}"
}}"""


def tools_to_prompt(tools: List[Dict[str, Any]], with_few_shots: bool = True) -> str:
    prefix = ""
    if with_few_shots:
        prefix = f"{tool_use_few_shot()}\n\n"
    return f"""{prefix}# {AVAILABLE_TOOLS_HEADER}
{json.dumps(tools, indent=4)}"""


class ToolCallingParsingError(Exception):
    pass


class ToolCallingToolDoesNotExistError(Exception):
    pass


class ToolCallingInvalidArgumentsError(Exception):
    pass
