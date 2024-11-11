# Copyright Sierra

from typing import List, Optional, Dict, Any

from tau_bench.envs.base import Env
from tau_bench.types import SolveResult, Action, RESPOND_ACTION_NAME
from tau_bench.agents.tool_calling_agent import ToolCallingAgent
from cashier.agent_executor import AgentExecutor
from cashier.model import Model
from cashier.graph_data.cashier import cashier_graph_schema


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

        model = Model()
        AE = AgentExecutor(
            model,
            None,
            cashier_graph_schema,
            False,
            True,
        )

        AE.add_user_turn(obs)

        for _ in range(max_num_steps):
            model_completion = model.chat(
                model_name=self.model,
                stream=False,
                temperature=self.temperature,
                **AE.get_model_completion_kwargs(),
            )
            action = message_to_action(model_completion)
            env_response = env.custom_step(action, model_completion, AE)
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


def message_to_action(
    model_completion,
) -> Action:
    fn_call = next(model_completion.get_or_stream_fn_calls(), None)
    if fn_call is not None:
        return Action(
            name=fn_call.function_name,
            kwargs=fn_call.function_args,
        )
    else:
        return Action(
            name=RESPOND_ACTION_NAME,
            kwargs={"content": model_completion.get_or_stream_message()},
        )
