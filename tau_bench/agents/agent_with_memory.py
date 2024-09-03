from tau_bench.agents.base import Agent
from tau_bench.envs.base import Env
from tau_bench.types import SolveResult
from typing import Optional


class AgentWithMemory(Agent):
    def solve(
        self, env: Env, index: Optional[int] = None, max_num_steps: int = 30
    ) -> SolveResult:
        # TODO: implement here
        pass
