# Copyright Sierra

from tau_bench.agents.base import BaseAgent
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_random_exponential
from termcolor import colored

client = Anthropic()


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(10))
def chat_completion_request(messages, model, system, tools=None, temperature=0.0):
    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            tools=tools,
            messages=messages,
            temperature=temperature,
            system=system,
        )
        assert response.stop_reason in ["end_turn", "tool_use"]
        return response
    except Exception as e:
        print(f"chat_completion_request Exception: {e}")
        return e


class ClaudeFunctionCallingAgent(BaseAgent):
    def __init__(self, tools, wiki, model="claude-3-opus-20240229"):
        self.tools = [
            {
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"],
            }
            for tool in tools
        ]
        self.wiki = wiki
        self.model = model
        self.reset()

    def reset(self):
        self.messages = []

    def act(self, env, index=None, verbose=False, temperature=0.0):
        self.reset()
        obs, info = env.reset(index=index)
        reward = 0
        self.messages.append({"role": "user", "content": obs})
        if verbose:
            print(colored(f"user: {obs}\n", "green"))
        for _ in range(30):
            response = chat_completion_request(
                messages=self.messages,
                tools=self.tools,
                model=self.model,
                system=self.wiki,
                temperature=temperature,
            )

            if response.stop_reason == "end_turn":
                if response.content == []:
                    print("No response from Claude")
                    print(response)
                    break
                content = response.content[0].text
                # remove things after </thinking>
                content = content.split("</thinking>")[-1].strip()
                action = {"name": "respond", "arguments": {"content": content}}
                obs, reward, done, info = env.step(action)
                self.messages.extend(
                    [
                        {"role": "assistant", "content": response.content},
                        {"role": "user", "content": obs},
                    ]
                )

                if verbose:
                    text = "\n--new--\n".join([_.text for _ in response.content])
                    print(colored(f"assistant: {text}", "yellow"))
                    print(colored(f"user: {obs}\n", "green"))
            elif response.stop_reason == "tool_use":
                tool_call = response.content[-1]
                action = {
                    "name": tool_call.name,
                    "arguments": tool_call.input,
                }
                obs, reward, done, info = env.step(action)
                self.messages.extend(
                    [
                        {"role": "assistant", "content": response.content},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_call.id,
                                    "content": obs,
                                }
                            ],
                        },
                    ]
                )
                if verbose:
                    text = "\n--new--\n".join([_.text for _ in response.content[:-1]])
                    print(colored(f"assistant: {text}", "yellow"))
                    print(
                        colored(
                            f"assistant: {tool_call.name} ({tool_call.input})", "yellow"
                        )
                    )
                    print(colored(f"tool ({tool_call.name}): {obs}\n", "magenta"))
            if done:
                break
            # time.sleep(2)  # deal with rate limiting?
        return reward, info

    def get_messages(self):
        return [message_to_dict(message) for message in self.messages]


def message_to_dict(message):
    if isinstance(message["content"], str):
        return message
    elif isinstance(message["content"], list):
        return {
            "role": message["role"],
            "content": [
                _ if isinstance(_, dict) else _.to_dict() for _ in message["content"]
            ],
        }
