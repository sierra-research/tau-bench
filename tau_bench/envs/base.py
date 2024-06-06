# Copyright Sierra

import random
from copy import deepcopy
from hashlib import sha256
from typing import Any, Callable, Dict, List, Tuple, TypedDict

from tau_bench.envs.user import load_user


class Action(TypedDict):
    name: str
    arguments: Dict[str, Any]


def to_hashable(item):
    """
    Recursively converts an item into a hashable type. This function handles
    dictionaries, lists, and basic nested structures.
    """
    if isinstance(item, dict):
        return tuple((key, to_hashable(value)) for key, value in sorted(item.items()))
    elif isinstance(item, list):
        return tuple(to_hashable(element) for element in item)
    else:
        return item


def consistent_hash(value):
    return sha256(str(value).encode("utf-8")).hexdigest()


class BaseEnv:
    def __init__(
        self,
        data: Dict[str, Any],
        tools: List[Callable],
        tasks: List[Dict[str, Any]],
        wiki: str,
        rules: List[str],
        user_mode: str,
        user_model: str,
    ):
        super().__init__()
        self.init_data = data
        self.data = None
        self.tools = tools
        self.tools_dict = {tool.__name__: tool for tool in tools}
        self.tools_info = [tool.__info__ for tool in tools]
        self.terminate_tools = []
        self.tasks = tasks
        self.task = None
        self.wiki = wiki
        self.rules = rules
        self.user = load_user(user_mode, user_model)
        self.actions = []
        self.index = None

    def reset(self, index=None, obs=True) -> Tuple[str, Dict[str, Any]]:
        if index is None:
            index = random.randint(0, len(self.tasks))
        self.index = index
        self.data = deepcopy(self.init_data)
        self.task = self.tasks[index]
        self.actions = []  # store the actions from the agent
        observation = (
            self.user.reset(instruction=self.task["instruction"]) if obs else ""
        )
        return observation, {"task": self.task, "source": "user"}

    def step(self, action: Action) -> Tuple[str, float, bool, Dict[str, Any]]:
        if not isinstance(action, dict):
            raise TypeError("action must be a dictionary")
        if "name" not in action or not isinstance(action["name"], str):
            raise ValueError("action: 'name' key must be present and must be a string")
        if "arguments" not in action or not isinstance(action["arguments"], dict):
            raise ValueError(
                "action: 'arguments' key must be present and must be a dictionary"
            )

        self.actions.append(action)

        if action["name"] == "respond":
            observation = self.user.step(action["arguments"]["content"])
            reward, done, info = 0, False, {"source": "user"}
            if observation == "###STOP###":
                done = True
        elif action["name"] in self.tools_dict:
            try:
                observation = self.tools_dict[action["name"]](
                    data=self.data, **action["arguments"]
                )
            except Exception as e:
                observation = f"Error: {e}"
            reward, done, info = 0, False, {"source": action["name"]}
            if action["name"] in self.terminate_tools:
                done = True
        else:
            observation = f"Unknown action {action['name']}"
            reward, done, info = 0, False, {"source": action["name"]}

        if done:
            reward, info = self.calculate_reward()
            info["user_cost"] = self.user.get_total_cost()
        return str(observation), reward, done, info

    def get_data_hash(self) -> str:
        return consistent_hash(to_hashable(self.data))

    def calculate_reward(self) -> Tuple[float, Dict[str, Any]]:
        data_hash = self.get_data_hash()
        reward, info = 1, {
            "data_hash": data_hash,
            "actions": [
                action for action in self.actions if action["name"] != "respond"
            ],
        }

        # check outputs
        if "outputs" in self.task:
            info["r_outputs"] = 1
            info["outputs"] = {}
            for output in self.task["outputs"]:
                found = False
                for action in self.actions:
                    if action["name"] == "respond" and output.lower() in action[
                        "arguments"
                    ]["content"].lower().replace(",", ""):
                        found = True
                        break
                info["outputs"][output] = found
                if not found:
                    info["r_outputs"] = 0
                    reward = 0

        # check database change
        if "actions" in self.task:
            # TODO: cache gt_data_hash in tasks.py (low priority)
            self.data = deepcopy(self.init_data)
            for action in self.task["actions"]:
                if action["name"] not in self.terminate_tools:
                    self.step(action)
            gt_data_hash = self.get_data_hash()
            info["r_actions"] = data_hash == gt_data_hash
            info["gt_data_hash"] = gt_data_hash
            if not info["r_actions"]:
                reward = 0

        return reward, info
