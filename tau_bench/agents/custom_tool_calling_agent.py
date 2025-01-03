# Copyright Sierra

from typing import List, Optional, Dict, Any

from tau_bench.envs.base import Env
from tau_bench.types import SolveResult, Action, RESPOND_ACTION_NAME
from tau_bench.agents.tool_calling_agent import ToolCallingAgent
from cashier.agent_executor import AgentExecutor
from cashier.model.model_completion import Model
from cashier.model.model_client import ModelClient
from tau_bench.agents.custom_tool_call_data.request_graph_schema import AIRLINE_REQUEST_GRAPH
from cashier.model.model_util import ModelProvider
from cashier.model.model_turn import NodeSystemTurn, AssistantTurn, UserTurn


class CustomToolCallingAgent(ToolCallingAgent):

    def solve(
        self, env: Env, task_index: Optional[int] = None, max_num_steps: int = 90
    ) -> SolveResult:
        total_cost = 0.0
        env_reset_res = env.reset(task_index=task_index)
        obs = env_reset_res.observation
        info = env_reset_res.info.model_dump()
        reward = 0.0
        oai_messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.wiki},
            {"role": "user", "content": obs},
        ]
        model_provider = ModelProvider(self.provider.upper())
        ModelClient.initialize()
        AE = AgentExecutor(
            False,
            True,
            AIRLINE_REQUEST_GRAPH,
        )

        AE.add_user_turn(obs)

        for _ in range(max_num_steps):
            model_completion = Model.chat(
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

        turns = AE.TC.turns
        oai_messages = []
        raw_messages = []
        anthropic_messages = []
        for turn in turns:
            if isinstance(turn, (NodeSystemTurn, AssistantTurn, UserTurn)):
                oai_messages.extend(turn.build_oai_messages())
            raw_messages.extend(turn.build_oai_messages())
            anthropic_messages.extend(turn.build_anthropic_messages())

        return SolveResult(
            reward=reward,
            info=info,
            messages=AE.TC.model_provider_to_message_manager[ModelProvider.OPENAI].conversation_dicts,
            total_cost=total_cost,
            raw_messages=raw_messages,
            node_turns = [node_turn.model_dump() for node_turn in AE.TC.turns],
            anthropic_messages=anthropic_messages,
            oai_messages=oai_messages,
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
