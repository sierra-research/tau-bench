# Copyright Sierra

import json
import time

from tenacity import retry, stop_after_attempt, wait_random_exponential

from tau_bench.agents.base import BaseAgent
from tau_bench.agents.utils import pretty_print_conversation

create = None
create_mode = None


def initialize_create(mode="openai", **kwargs):
    global create, create_mode
    if mode == "openai":
        from openai import OpenAI

        create = OpenAI(**kwargs).chat.completions.create
        create_mode = "openai"

    elif mode == "anthropic":
        from anthropic import Anthropic

        create = Anthropic().messages.create
        create_mode = "anthropic"

    elif mode == "google":
        global GenerativeModel
        from google.generativeai import GenerativeModel

        create = None
        create_mode = "google"


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(10))
def get_message_action(
    messages, model, **kwargs
):  # kwargs only contain temperature for now
    global create, create_mode
    if create_mode == "openai":
        kwargs["model"] = model
        kwargs["messages"] = messages
    elif create_mode == "anthropic":
        kwargs["system"] = messages[0]["content"]
        kwargs["max_tokens"] = 256
        kwargs["model"] = model
        kwargs["messages"] = messages[1:]
    elif create_mode == "google":
        create = GenerativeModel(
            model, system_instruction=messages[0]["content"], generation_config=kwargs
        ).generate_content
        kwargs = {
            "contents": [
                {
                    "role": {"user": "user", "assistant": "model"}[m["role"]],
                    "parts": [m["content"]],
                }
                for m in messages[1:]
            ]
        }
        time.sleep(2)

    response = create(**kwargs)

    if create_mode == "openai":
        message = response.choices[0].message.content
    elif create_mode == "anthropic":
        message = response.content[0].text
    elif create_mode == "google":
        message = response.text

    action_name = message.split("Action:")[-1].split("Arguments:")[0].strip()
    action_args = message.split("Arguments:")[-1].strip().split("\n")[0]
    if action_name == "respond" or action_name == "":
        action_args = {"content": action_args}
    else:
        action_args = json.loads(action_args)
    return message, {"name": action_name, "arguments": action_args}


class ChatReActAgent(BaseAgent):
    def __init__(self, tools, wiki, model: str = "gpt-4-turbo", reason: bool = True):
        instruction = react_instruction if reason else act_instruction
        self.prompt = wiki + "\n#Available tools\n" + json.dumps(tools) + instruction
        self.model = model
        self.reset()

    def reset(self):
        self.messages = [{"role": "system", "content": self.prompt}]

    def act(self, env, index=None, verbose=False, temperature=0.0):
        self.reset()
        obs, info = env.reset(index=index)
        reward = 0
        self.messages.append({"role": "user", "content": obs})
        if verbose:
            self.render(1)
        for _ in range(30):
            try:
                message, action = get_message_action(
                    self.messages, self.model, temperature=temperature
                )
            except Exception as e:
                print(e)
                info["error"] = str(e)
                break
            obs, reward, done, info = env.step(action)
            if action["name"] != "respond":
                obs = "API output: " + obs
            self.messages.append({"role": "assistant", "content": message})
            self.messages.append({"role": "user", "content": obs})
            if verbose:
                self.render(2)
            if done:
                break
        return reward, info

    def render(self, last_n=None):
        if last_n is not None:
            pretty_print_conversation(self.messages[-last_n:])
        else:
            pretty_print_conversation(self.messages)

    def get_messages(self):
        return self.messages


react_instruction = """
# Instruction
You need to act as an agent that use the above tools to help the user according to the above policy.

At each step, your generation should have exactly the following format and have exactly 6 lines (without ```):

```
Thought:
A single line of reasoning to process the context and inform the decision making. Do not include extra lines.
Action:
The name of the action to take. It has to come from "Available tools", or "respond" to respond to the user.
Arguments:
The arguments to the action in json format. If the action is "respond", the argument is the response to the user.
```

You should not use made-up or placeholder arguments.


For example, if the user says "I want to know the current weather of San Francisco", and there is such a tool available
```json
{
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The temperature unit to use. Infer this from the users location.",
                    },
                },
                "required": ["location", "format"],
            },
        }
    }
```

Your response can be like this:
```
Thought:
Since the user asks for the weather of San Francisco in USA, the unit should be in fahrenheit. I can query get_current_weather to get the weather.
Action:
get_current_weather
Arguments:
{"location": "San Francisco, CA", "format": "fahrenheit"}
```

And if the tool returns "70F", your response can be:
```
Thought:
I can answer the user now.
Action:
respond
Arguments:
The current weather of San Francisco is 70F.
```

Try to be helpful and always follow the policy.
"""


act_instruction = """
# Instruction
You need to act as an agent that use the above tools to help the user according to the above policy.

At each step, your generation should have exactly the following format and have exactly 4 lines (without ```):

```
Action:
The name of the action to take. It has to come from "Available tools", or "respond" to respond to the user.
Arguments:
The arguments to the action in json format. If the action is "respond", the argument is the response to the user.
```

You should not use made-up or placeholder arguments.


For example, if the user says "I want to know the current weather of San Francisco", and there is such a tool available
```json
{
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The temperature unit to use. Infer this from the users location.",
                    },
                },
                "required": ["location", "format"],
            },
        }
    }
```

Your response can be like this:
```
Action:
get_current_weather
Arguments:
{"location": "San Francisco, CA", "format": "fahrenheit"}
```

And if the tool returns "70F", your response can be:
```
Action:
respond
Arguments:
The current weather of San Francisco is 70F.
```

Try to be helpful and always follow the policy. Always make sure you generate four lines with the correct format.
"""
