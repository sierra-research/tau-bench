# Copyright Sierra

from tau_bench.envs.airline.data import load_data
from tau_bench.envs.airline.rules import rules
from tau_bench.envs.airline.tools import tools
from tau_bench.envs.airline.wiki import wiki
from tau_bench.envs.base import BaseEnv


class MockAirlineDomainEnv(BaseEnv):
    def __init__(
        self,
        user_mode: str = "naive",
        user_model: str = "gpt-4",
        task_split: str = "test",
    ):
        # switch over task_split
        match task_split:
            case "test":
                from tau_bench.envs.airline.tasks import tasks
            case _:
                raise ValueError(f"Unknown task split: {task_split}")
        super().__init__(load_data, tools, tasks, wiki, rules, user_mode, user_model)
        self.terminate_tools = ["transfer_to_human_agents"]
