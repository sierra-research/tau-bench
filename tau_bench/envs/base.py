# Copyright Sierra

import json
import os
import sys
import random
from hashlib import sha256
from tau_bench.envs.tool import Tool
from typing import Any, Callable, Dict, List, Type, Optional, Set, Union, Tuple

# Temporary debug flag for respond-path investigation. When set, Env.step respond branch logs to stderr.
_DEBUG_RESPOND_PATH = os.environ.get("TAU_BENCH_DEBUG_RESPOND_PATH", "").lower() in ("1", "true", "yes")


def _respond_path_debug_env(extra: Dict[str, Any]) -> None:
    if not _DEBUG_RESPOND_PATH:
        return
    payload = {"respond_path_debug": "env_step_respond", **extra}
    print(json.dumps(payload, default=str), file=sys.stderr)

from tau_bench.envs.user import load_user, UserStrategy
from tau_bench.types import (
    Action,
    Task,
    EnvInfo,
    EnvResetResponse,
    EnvResponse,
    RewardResult,
    RewardOutputInfo,
    RewardActionInfo,
    RESPOND_ACTION_NAME,
)

ToHashable = Union[
    str, int, float, Dict[str, "ToHashable"], List["ToHashable"], Set["ToHashable"]
]
Hashable = Union[str, int, float, Tuple["Hashable"], Tuple[Tuple[str, "Hashable"]]]


def to_hashable(item: ToHashable) -> Hashable:
    if isinstance(item, dict):
        return tuple((key, to_hashable(value)) for key, value in sorted(item.items()))
    elif isinstance(item, list):
        return tuple(to_hashable(element) for element in item)
    elif isinstance(item, set):
        return tuple(sorted(to_hashable(element) for element in item))
    else:
        return item


def consistent_hash(
    value: Hashable,
) -> str:
    return sha256(str(value).encode("utf-8")).hexdigest()


class Env(object):
    def __init__(
        self,
        data_load_func: Callable[[], Dict[str, Any]],
        tools: List[Type[Tool]],
        tasks: List[Task],
        wiki: str,
        rules: List[str],
        user_strategy: Union[str, UserStrategy],
        user_model: str,
        user_provider: Optional[str] = None,
        task_index: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.data_load_func = data_load_func
        self.data = data_load_func()
        self.tools_map: Dict[str, Type[Tool]] = {
            tool.get_info()["function"]["name"]: tool for tool in tools
        }
        self.tools_info = [tool.get_info() for tool in tools]
        self.terminate_tools = []
        self.tasks = tasks
        if task_index is not None:
            self.task_index = task_index
        else:
            self.task_index = random.randint(0, len(tasks))
        self.task = tasks[self.task_index]
        self.wiki = wiki
        self.rules = rules
        self.user = load_user(
            user_strategy=user_strategy, model=user_model, provider=user_provider
        )
        self.actions: List[Action] = []

    def reset(self, task_index: Optional[int] = None) -> EnvResetResponse:
        if task_index is None:
            task_index = random.randint(0, len(self.tasks))
        self.task_index = task_index
        self.data = self.data_load_func()
        self.task = self.tasks[task_index]
        self.actions = []
        initial_observation = self.user.reset(instruction=self.task.instruction)
        return EnvResetResponse(
            observation=initial_observation, info=EnvInfo(task=self.task, source="user")
        )

    def step(self, action: Action) -> EnvResponse:
        self.actions.append(action)

        info = EnvInfo(task=self.task)
        reward = 0
        done = False
        if action.name == RESPOND_ACTION_NAME:
            action_content = action.kwargs.get("content") if isinstance(action.kwargs, dict) else None
            observation = self.user.step(action_content)
            info.source = "user"
            done = "###STOP###" in observation
            if _DEBUG_RESPOND_PATH:
                obs_preview = (observation or "")[:500] if isinstance(observation, str) else str(observation)[:500]
                _respond_path_debug_env({
                    "action_content_preview": (action_content or "")[:300] if action_content else None,
                    "user_observation_raw_preview": obs_preview,
                    "done": done,
                    "stop_in_observation": "###STOP###" in (observation or ""),
                })
            if _DEBUG_RESPOND_PATH and isinstance(observation, str):
                simple_confirmations = {"yes", "yes.", "sure", "ok"}
                if observation.strip().lower() in simple_confirmations and done:
                    raise AssertionError(
                        "Simple confirmation reply should not set done=True; "
                        "user_observation_raw may contain ###STOP### unexpectedly"
                    )
        elif action.name in self.tools_map:
            try:
                observation = self.tools_map[action.name].invoke(
                    data=self.data, **action.kwargs
                )
            except Exception as e:
                observation = f"Error: {e}"
            info.source = action.name
            if action.name in self.terminate_tools:
                done = True
        else:
            observation = f"Unknown action {action.name}"
            info.source = action.name

        if done:
            reward_res = self.calculate_reward()
            reward = reward_res.reward
            info.reward_info = reward_res
            info.user_cost = self.user.get_total_cost()
        return EnvResponse(observation=observation, reward=reward, done=done, info=info)

    def get_data_hash(self) -> str:
        return consistent_hash(to_hashable(self.data))

    def calculate_reward(self) -> RewardResult:
        data_hash = self.get_data_hash()
        reward = 1.0
        actions = [
            action for action in self.task.actions if action.name != RESPOND_ACTION_NAME
        ]

        # Check if the database changes are correct. If they are not correct, then we set the reward to 0.
        # TODO: cache gt_data_hash in tasks.py (low priority)
        self.data = self.data_load_func()
        for action in self.task.actions:
            if action.name not in self.terminate_tools:
                self.step(action)
        gt_data_hash = self.get_data_hash()
        info = RewardActionInfo(
            r_actions=data_hash == gt_data_hash, gt_data_hash=gt_data_hash
        )
        if not info.r_actions:
            reward = 0.0

        if len(self.task.outputs) > 0:
            # check outputs
            r_outputs = 1.0
            outputs = {}
            for output in self.task.outputs:
                found = False
                for action in self.actions:
                    if (
                        action.name == RESPOND_ACTION_NAME
                        and output.lower()
                        in action.kwargs["content"].lower().replace(",", "")
                    ):
                        found = True
                        break
                outputs[output] = found
                if not found:
                    r_outputs = 0.0
                    reward = 0.0
            info = RewardOutputInfo(r_outputs=r_outputs, outputs=outputs)
            
        return RewardResult(reward=reward, info=info, actions=actions)
