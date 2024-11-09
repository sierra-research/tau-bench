# Copyright Sierra

import json
from litellm import completion
from typing import List, Optional, Dict, Any

from tau_bench.envs.base import Env
from tau_bench.types import SolveResult, Action, RESPOND_ACTION_NAME
from tool_calling_agent import ToolCallingAgent


class CustomToolCallingAgent(ToolCallingAgent):

    def solve(
        self, env: Env, task_index: Optional[int] = None, max_num_steps: int = 30
    ) -> SolveResult:
        total_cost = 0.0
        env_reset_res = env.reset(task_index=task_index)
        obs = env_reset_res.observation
        info = env_reset_res.info.model_dump()
        reward = 0.0
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.wiki},
            {"role": "user", "content": obs},
        ]
        for _ in range(max_num_steps):
            # call model for assistant msse, output is res
            res = None # output of model completion
            next_message = res.choices[0].message.model_dump()
            total_cost += res._hidden_params["response_cost"]
            env_response = env.custom_step(res)
            reward = env_response.reward
            info = {**info, **env_response.info.model_dump()}

            if env_response.done:
                break
        return SolveResult(
            reward=reward,
            info=info,
            messages=messages,
            total_cost=total_cost,
        )
