# Copyright Sierra

import json
from typing import Dict, List

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

from tau_bench.agents.base import BaseAgent
from tau_bench.agents.utils import (
    message_to_action,
    message_to_dict,
    pretty_print_conversation,
)

client = None


def initialize_client(**kwargs):
    global client
    client = OpenAI(**kwargs)


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(10))
def chat_completion_request(
    messages: List[Dict[str, str]],
    model: str,
    tools=None,
    tool_choice="auto",
    temperature: float = 0.0,
):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
        temperature=temperature,
    )
    message = response.choices[0].message
    if hasattr(message, "tool_calls") and message.tool_calls is not None:
        tool_call = message.tool_calls[0]
        json.loads(tool_call.function.arguments)
    return message, dict(response.usage)


prompt_price_per_million = {
    "gpt-4o": 5,
    "gpt-4-turbo": 10,
    "gpt-4-32k-0613": 60,
    "gpt-3.5-turbo": 0.5,
    "meta-llama/Meta-Llama-3-8B-Instruct": 0.15,
    "meta-llama/Meta-Llama-3-70B-Instruct": 1.0,
}
completion_price_per_million = {
    "gpt-4o": 15,
    "gpt-4-turbo": 30,
    "gpt-4-32k-0613": 120,
    "gpt-3.5-turbo": 1.5,
    "meta-llama/Meta-Llama-3-8B-Instruct": 0.15,
    "meta-llama/Meta-Llama-3-70B-Instruct": 1.0,
}


class GPTFunctionCallingAgent(BaseAgent):
    def __init__(self, tools, wiki, model: str = "gpt-4-turbo"):
        self.tools = tools
        self.wiki = wiki
        self.model = model
        self.usage = {"completion_tokens": [], "prompt_tokens": [], "total_tokens": []}
        self.reset()

    def reset(self):
        self.messages = [{"role": "system", "content": self.wiki}]
        self.usage = {"completion_tokens": [], "prompt_tokens": [], "total_tokens": []}

    def act(self, env, index=None, verbose=False, temperature=0.0):
        self.reset()
        obs, info = env.reset(index=index)
        reward = 0
        self.messages.append({"role": "user", "content": obs})
        if verbose:
            self.render(1)
        for _ in range(30):
            message, usage = chat_completion_request(
                self.messages,
                model=self.model,
                tools=self.tools,
                temperature=temperature,
            )
            for key, value in usage.items():
                self.usage[key].append(value)
            if isinstance(message, Exception) and "context_length_exceeded" in str(
                message
            ):
                print(message)
                info["error"] = str(message)
                break
            action = message_to_action(message)
            obs, reward, done, info = env.step(action)
            if action["name"] == "respond":
                self.messages.append({"role": "assistant", "content": message.content})
                self.messages.append({"role": "user", "content": obs})
            else:
                message.tool_calls = message.tool_calls[:1]
                self.messages.append(message)
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": message.tool_calls[0].id,
                        "name": message.tool_calls[0].function.name,
                        "content": obs,
                    }
                )
            if verbose:
                self.render(2)
            if done:
                break
        self.usage.update(
            {"completion_price": [], "prompt_price": [], "total_price": []}
        )
        self.usage["completion_price"] = (
            completion_price_per_million[self.model]
            * sum(self.usage["completion_tokens"])
            / 1e6
        )
        self.usage["prompt_price"] = (
            prompt_price_per_million[self.model]
            * sum(self.usage["prompt_tokens"])
            / 1e6
        )
        self.usage["total_price"] = (
            self.usage["completion_price"] + self.usage["prompt_price"]
        )
        info["usage"] = self.usage
        return reward, info

    def render(self, last_n=None):
        if last_n is not None:
            pretty_print_conversation(self.messages[-last_n:])
        else:
            pretty_print_conversation(self.messages)

    def get_messages(self) -> List[Dict[str, str]]:
        return [message_to_dict(message) for message in self.messages]
