# Copyright Sierra

import os
import abc
from tenacity import retry, stop_after_attempt, wait_random_exponential
from typing import Callable


class BaseUserSimulationEnv:
    metadata = {}

    def reset(self, instruction: str) -> str:
        return ""

    def step(self, content: str) -> str:
        return ""

    def get_total_cost(self) -> float:
        return 0


class HumanUserSimulationEnv(BaseUserSimulationEnv):
    def reset(self, instruction: str) -> str:
        return input(f"{instruction}\n")

    def step(self, content: str) -> str:
        return input(f"{content}\n")


SYSTEM_PROMPT = """You are an user interacting with an agent.

Instruction: {instruction}

Rules:
- Just generate one line at a time to simulate the user's message.
- Do not give away all the instruction at once. Only provide the information that is necessary for the current step.
- Do not hallucinate information that is not provided in the instruction. For example, if the agent asks for the order id but it is not mentioned in the instruction, do not make up an order id, just say you do not remember or have it.
- If the instruction goal is satisified, generate '###STOP###' as a standalone message without anything else to end the conversation.
- Do not repeat the exact instruction in the conversation. Instead, use your own words to convey the same information.
- Try to make the conversation as natural as possible, and stick to the personalities in the instruction.
"""


class OpenAIChatFunc(object):
    def __init__(self, model: str) -> None:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError("OPENAI_API_KEY is not set")

        self.client = OpenAI(api_key=api_key)

        self.prompt_price_per_million = {
            "gpt-4o-2024-08-06": 2.5,
            "gpt-4o-mini": 0.15,
            "gpt-4o-mini-2024-07-18": 0.15,
            "gpt-4o-2024-05-13": 5,
            "gpt-4o": 5,
            "gpt-4-turbo": 10,
            "gpt-4": 30,
            "gpt-4-32k-0613": 60,
            "gpt-3.5-turbo": 0.5,
        }
        self.completion_price_per_million = {
            "gpt-4o-2024-08-06": 10,
            "gpt-4o-mini": 0.6,
            "gpt-4o-mini-2024-07-18": 0.6,
            "gpt-4o-2024-05-13": 15,
            "gpt-4o": 15,
            "gpt-4-turbo": 30,
            "gpt-4": 60,
            "gpt-4-32k-0613": 120,
            "gpt-3.5-turbo": 1.5,
        }

        if (
            model not in self.prompt_price_per_million
            or model not in self.completion_price_per_million
        ):
            raise ValueError(f"Model {model} is not supported")
        self.model = model

    @retry(
        wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(10)
    )
    def chat_completion_request(
        self, messages: list[dict[str, str]], temperature: float = 1.0
    ) -> tuple[str, float]:
        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=temperature,
        )
        content = response.choices[0].message.content
        cost = (
            self.prompt_price_per_million[self.model]
            * response.usage.prompt_tokens
            / 1e6
            + self.completion_price_per_million[self.model]
            * response.usage.completion_tokens
            / 1e6
        )
        return content, cost

    def __call__(self, messages: list[dict[str, str]]) -> tuple[str, float]:
        return self.chat_completion_request(messages, temperature=1.0, max_tokens=150)


class ClaudeChatFunc(object):
    def __init__(self, model: str) -> None:
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key is None:
            raise ValueError("ANTHROPIC_API_KEY is not set")

        self.client = Anthropic(api_key=api_key, max_retries=5)

        self.prompt_price_per_million = {
            "claude-3-5-sonnet-20240620": 3,
        }
        self.completion_price_per_million = {
            "claude-3-5-sonnet-20240620": 15,
        }
        if (
            model not in self.prompt_price_per_million
            or model not in self.completion_price_per_million
        ):
            raise ValueError(f"Model {model} is not supported")
        self.model = model

    def remap_msgs(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        msgs = [
            {
                "role": msg["role"] if msg["role"] != "system" else "user",
                "content": msg["content"],
            }
            for msg in messages
        ]
        remapped = []
        for msg in msgs:
            if (
                msg["role"] == "user"
                and len(remapped) > 0
                and remapped[-1]["role"] == "user"
            ):
                remapped[-1]["content"] += f"\n\n{msg['content']}"
            else:
                remapped.append(msg)
        return remapped

    def __call__(self, messages: list[dict[str, str]]) -> tuple[str, float]:
        remapped_msgs = self.remap_msgs(messages)
        response = self.client.messages.create(
            messages=remapped_msgs,
            model=self.model,
            max_tokens=150,
        )
        content = response.content[0].text
        cost = (
            self.prompt_price_per_million[self.model]
            * response.usage.input_tokens
            / 1e6
            + self.completion_price_per_million[self.model]
            * response.usage.output_tokens
            / 1e6
        )
        return content, cost


class MistralChatFunc(object):
    def __init__(self, model: str) -> None:
        from mistralai import Mistral

        api_key = os.getenv("MISTRAL_API_KEY")
        if api_key is None:
            raise ValueError("MISTRAL_API_KEY is not set")

        self.client = Mistral(api_key=api_key)

        self.prompt_price_per_million = {
            "mistral-large-latest": 3,
        }
        self.completion_price_per_million = {
            "mistral-large-latest": 9,
        }
        if (
            model not in self.prompt_price_per_million
            or model not in self.completion_price_per_million
        ):
            raise ValueError(f"Model {model} is not supported")
        self.model = model

    def __call__(self, messages: list[dict[str, str]]) -> tuple[str, float]:
        response = self.client.chat.complete(
            messages=messages,
            model=self.model,
            max_tokens=150,
        )
        content = response.choices[0].message.content
        cost = (
            self.prompt_price_per_million[self.model]
            * response.usage.prompt_tokens
            / 1e6
            + self.completion_price_per_million[self.model]
            * response.usage.completion_tokens
            / 1e6
        )
        return content, cost


def chat_func_factory(
    model: str,
) -> Callable[[list[dict[str, str]]], tuple[str, float]]:
    if model.startswith("gpt-4") or model.startswith("gpt-3.5"):
        return OpenAIChatFunc(model)
    elif model.startswith("claude"):
        return ClaudeChatFunc(model=model)
    elif model.startswith("mistral"):
        return MistralChatFunc(model=model)
    else:
        raise ValueError(f"Unknown model {model}")


class LLMUserSimulationEnv(BaseUserSimulationEnv):
    def __init__(
        self, chat_func: Callable[[list[dict[str, str]]], tuple[str, float]]
    ) -> None:
        super().__init__()
        self.messages = []
        self.system_prompt = SYSTEM_PROMPT
        self.chat_func = chat_func
        self.total_cost = 0

    def reset(self, instruction=None) -> str:
        self.total_cost = 0
        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt.format(instruction=instruction),
            },
            {"role": "user", "content": "Hi! How can I help you today?"},
        ]
        content, cost = self.chat_func(self.messages)
        self.messages.append({"role": "assistant", "content": content})
        self.total_cost += cost
        return content

    def step(self, content: str) -> str:
        self.messages.append({"role": "user", "content": content})
        content, cost = self.chat_func(self.messages)
        self.messages.append({"role": "assistant", "content": content})
        self.total_cost += cost
        return content

    def get_total_cost(self):
        return self.total_cost


def load_user(user_mode: str, model: str = "gpt-4") -> BaseUserSimulationEnv:
    if user_mode == "human":
        return HumanUserSimulationEnv()
    elif user_mode == "naive":
        chat_func = chat_func_factory(model)
        return LLMUserSimulationEnv(chat_func=chat_func)
    else:
        raise ValueError(f"Unknown user mode {user_mode}")
