# Copyright Sierra

from typing import List, Optional, Dict, Any

from tau_bench.envs.base import Env
from tau_bench.types import SolveResult, Action, RESPOND_ACTION_NAME
from tau_bench.agents.tool_calling_agent import ToolCallingAgent
from cashier.agent_executor import AgentExecutor
from cashier.model import Model
from tau_bench.agents.custom_tool_call_data.book_flight_graph import BOOK_FLIGHT_GRAPH
from tau_bench.agents.custom_tool_call_data.change_flight_graph import CHANGE_FLIGHT_GRAPH
from cashier.model_util import ModelProvider


class CustomToolCallingAgent(ToolCallingAgent):

    def solve(
        self, env: Env, task_index: Optional[int] = None, max_num_steps: int = 90
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
        model_provider = ModelProvider(self.provider.upper())
        model = Model()
        AE = AgentExecutor(
            model,
            None,
            BOOK_FLIGHT_GRAPH,
            False,
            True,
            model_provider,
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

        model_provider = Model.get_model_provider(self.model)
        return SolveResult(
            reward=reward,
            info=info,
            messages=AE.TC.model_provider_to_message_manager[model_provider].message_dicts,
            total_cost=total_cost,
        )


def message_to_action(
    model_completion,
) -> Action:
    fn_call = next(model_completion.get_or_stream_fn_calls(), None)
    if fn_call is not None:
        return Action(
            name=fn_call.name,
            kwargs=fn_call.args,
        )
    else:
        return Action(
            name=RESPOND_ACTION_NAME,
            kwargs={"content": model_completion.get_or_stream_message()},
        )
