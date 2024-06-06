# Copyright Sierra

import os
from typing import Any, Dict, List, Optional

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from tenacity import retry, stop_after_attempt, wait_random_exponential

from tau_bench.agents.gpt_function_calling_agent import (
    GPTFunctionCallingAgent,
    message_to_action,
)

respond_info = {
    "type": "function",
    "function": {
        "name": "respond",
        "description": "Use the tool to reply to the user.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                },
            },
            "required": ["content"],
        },
    },
}


class MistralFunctionCallingAgent(GPTFunctionCallingAgent):
    def __init__(self, tools, wiki, model: str = "mistral-large-2402"):
        self.tools = tools + [respond_info]
        self.wiki = wiki
        self.model = model
        self.reset()

        api_key = os.getenv("MISTRAL_API_KEY")
        if api_key is None:
            raise ValueError("Please set the MISTRAL_API_KEY environment variable")
        self.client = MistralClient(api_key=api_key)

    def reset(self):
        self.messages = [
            {
                "role": "system",
                "content": self.wiki + "\nNow let's start the conversation.",
            }
        ]

    @retry(
        wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(10)
    )
    def chat_completion_request(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.0,
    ) -> ChatMessage:
        response = self.client.chat(
            messages=messages,
            model=self.model,
            tools=tools,
            temperature=temperature,
            tool_choice=tool_choice if tool_choice is not None else "auto",
        )
        assert response.choices[0].message.tool_calls is not None
        return response.choices[0].message

    def act(self, env, index=None, verbose=False, temperature=0.0):
        self.reset()
        obs, info = env.reset(index=index)
        reward = 0
        self.messages.append({"role": "user", "content": obs})
        if verbose:
            self.render(1)
        for _ in range(30):
            message = self.chat_completion_request(
                self.messages,
                tools=self.tools,
                temperature=temperature,
                tool_choice="any",
            )
            if isinstance(message, Exception) and "context_length_exceeded" in str(
                message
            ):
                print(message)
                info["error"] = str(message)
                break
            action = message_to_action(message)
            obs, reward, done, info = env.step(action)
            message.tool_calls = message.tool_calls[:1]
            self.messages.append(message)
            self.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_calls[0].id,
                    "name": action["name"],
                    "content": obs,
                }
            )
            if verbose:
                self.render(2)
            if done:
                break

        return reward, info
