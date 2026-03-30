# Copyright Sierra

import random
from hashlib import sha256
from tau_bench.envs.tool import Tool
from typing import Any, Callable, Dict, List, Type, Optional, Set, Union, Tuple

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

# Simplified type aliases (avoid over-constraining for hashing convenience)
ToHashable = Any
Hashable = Any


def to_hashable(item: ToHashable) -> Hashable:
    if isinstance(item, dict):
        return sorted((key, to_hashable(value)) for key, value in item.items())
    elif isinstance(item, list):
        return [to_hashable(element) for element in item]
    elif isinstance(item, set):
        return sorted(to_hashable(element) for element in item)
    else:
        return item


def consistent_hash(value: Hashable) -> str:
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
        # track resilience (whether a transient tool error was encountered and later recovered)
        self._transient_errors: List[str] = []  # store order_ids (or identifiers) where a 503 occurred
        self._successful_retries: Set[str] = set()

    def reset(self, task_index: Optional[int] = None) -> EnvResetResponse:
        if task_index is None:
            task_index = random.randint(0, len(self.tasks))
        self.task_index = task_index
        self.data = self.data_load_func()
        self.task = self.tasks[task_index]
        self.actions = []
        self._transient_errors = []
        self._successful_retries = set()
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
            observation = self.user.step(action.kwargs["content"])
            info.source = "user"
            done = "###STOP###" in observation
        elif action.name in self.tools_map:
            try:
                observation = self.tools_map[action.name].invoke(
                    data=self.data, **action.kwargs
                )
            except Exception as e:
                observation = f"Error: {e}"
            info.source = action.name
            # detect simulated transient error pattern
            if isinstance(observation, str) and "503 Service Unavailable" in observation:
                # mark this order/tool context as transient error
                identifier = action.kwargs.get("order_id") or action.name
                self._transient_errors.append(str(identifier))
            else:
                # if we previously saw a transient error for same identifier and now success json, count as recovered
                identifier = action.kwargs.get("order_id") or action.name
                if (
                    identifier is not None
                    and str(identifier) in self._transient_errors
                    and isinstance(observation, str)
                    and "503 Service Unavailable" not in observation
                ):
                    self._successful_retries.add(str(identifier))
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
        # Base success logic (existing)
        data_hash = self.get_data_hash()
        base_success_reward = 1.0
        actions = [
            action for action in self.task.actions if action.name != RESPOND_ACTION_NAME
        ]

        # Replay ground truth actions to compute expected hash
        self.data = self.data_load_func()
        for action in self.task.actions:
            if action.name not in self.terminate_tools:
                self.step(action)
        gt_data_hash = self.get_data_hash()
        info: Union[RewardActionInfo, RewardOutputInfo]
        action_info = RewardActionInfo(
            r_actions=data_hash == gt_data_hash, gt_data_hash=gt_data_hash
        )
        success = action_info.r_actions
        if not success:
            base_success_reward = 0.0

        # Output check (overrides info type if outputs specified)
        if len(self.task.outputs) > 0:
            r_outputs = 1.0
            outputs: Dict[str, bool] = {}
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
                    base_success_reward = 0.0
            info = RewardOutputInfo(r_outputs=r_outputs, outputs=outputs)
        else:
            info = action_info

        # Efficiency penalty: -0.01 per step actually taken (excluding the implicit system messages)
        num_steps = len(self.actions)
        efficiency_penalty = -0.01 * num_steps

        # Resilience bonus: +0.1 if at least one transient error encountered and later recovered
        resilience_bonus = 0.0
        if success and len(self._successful_retries) > 0:
            resilience_bonus = 0.1

        # Composite reward should be 0 if the task was not successfully completed, as many other score parts can be misleading
        composite = 0 if base_success_reward == 0 else max(0, base_success_reward + efficiency_penalty + resilience_bonus)

        return RewardResult(
            reward=composite,
            info=info,
            actions=actions,
            components={
                "base_success": base_success_reward,
                "efficiency_penalty": efficiency_penalty,
                "resilience_bonus": resilience_bonus,
                "steps": num_steps,
                "resilience_triggered": list(self._successful_retries),
                "composite": composite,
            },
        )
