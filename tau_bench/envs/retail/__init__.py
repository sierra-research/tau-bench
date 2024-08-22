# Copyright Sierra

from tau_bench.envs.base import BaseEnv
from tau_bench.envs.retail.data import load_data
from tau_bench.envs.retail.rules import rules
from tau_bench.envs.retail.tools import tools
from tau_bench.envs.retail.wiki import wiki


class MockRetailDomainEnv(BaseEnv):
    def __init__(
        self,
        user_mode: str = "naive",
        user_model: str = "gpt-4",
        task_split: str = "test",
    ):
        # switch over task_split
        match task_split:
            case "test":
                from tau_bench.envs.retail.tasks import tasks
            case "train":
                from tau_bench.envs.retail.tasks_train import tasks
            case "dev":
                from tau_bench.envs.retail.tasks_dev import tasks
            case _:
                raise ValueError(f"Unknown task split: {task_split}")
        super().__init__(load_data, tools, tasks, wiki, rules, user_mode, user_model)
        self.terminate_tools = ["transfer_to_human_agents"]
