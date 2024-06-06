# Copyright Sierra

import time

import google.ai.generativelanguage as glm
import google.generativeai as genai
import proto.marshal.collections.maps
import proto.marshal.collections.repeated
from tau_bench.agents.base import BaseAgent
from tenacity import retry, stop_after_attempt, wait_random_exponential
from termcolor import colored


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(10))
def chat_completion_request(func, **kwargs):
    return func(**kwargs)


def map_composite_to_dict(map_composite):
    return {key: make_json_dumpable(value) for key, value in map_composite.items()}


def repeated_composite_to_list(repeated_composite):
    return [make_json_dumpable(item) for item in repeated_composite]


def make_json_dumpable(data):
    if isinstance(data, dict):
        return {key: make_json_dumpable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [make_json_dumpable(item) for item in data]
    elif isinstance(data, proto.marshal.collections.maps.MapComposite):
        return map_composite_to_dict(data)
    elif isinstance(data, proto.marshal.collections.repeated.RepeatedComposite):
        return repeated_composite_to_list(data)
    else:
        return data


class GeminiFunctionCallingAgent(BaseAgent):
    def __init__(self, tools, wiki, model="gemini-1.0-pro"):
        self.wiki = wiki
        kwargs = {
            "model_name": model,
            "tools": [{"function_declarations": [tool["function"] for tool in tools]}],
        }
        if model == "gemini-1.5-pro-latest" or model == "gemini-1.5-flash-latest":
            kwargs["system_instruction"] = self.wiki
            self.wiki = ""
        else:
            self.wiki += "\nAbove is the rule for you. Now you'll chat with an user. Below is the first message from the user:\n"
        self.model = genai.GenerativeModel(**kwargs)
        self.chat = self.model.start_chat()
        self.safety = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ]

    def reset(self):
        self.chat = self.model.start_chat()

    def act(self, env, index=None, verbose=False, temperature=0.0):
        self.reset()
        obs, info = env.reset(index=index)
        reward = 0
        if verbose:
            print(colored(f"user: {obs}\n", "green"))
        obs = self.wiki + obs
        for _ in range(30):
            response = chat_completion_request(
                self.chat.send_message,
                content=obs,
                safety_settings=self.safety,
                generation_config={"temperature": temperature},
            )
            if function_call := response.candidates[0].content.parts[0].function_call:
                action = {
                    "name": function_call.name,
                    "arguments": make_json_dumpable(function_call.args),
                }
                obs, reward, done, info = env.step(action)
                if verbose:
                    print(colored(f"assistant: {action}\n", "yellow"))
                    print(colored(f"tool ({function_call.name}): {obs}\n", "magenta"))
                obs = glm.Content(
                    parts=[
                        glm.Part(
                            function_response=glm.FunctionResponse(
                                name=function_call.name, response={"result": obs}
                            )
                        )
                    ]
                )
            else:
                text = response.candidates[0].content.parts[0].text
                action = {
                    "name": "respond",
                    "arguments": {"content": text},
                }
                obs, reward, done, info = env.step(action)
                if verbose:
                    print(colored(f"assistant: {text}", "yellow"))
                    print(colored(f"user: {obs}\n", "green"))
            if done:
                break
            time.sleep(30)
        return reward, info

    def get_messages(self):
        return [{"role": m.role, "content": str(m.parts[0])} for m in self.chat.history]
