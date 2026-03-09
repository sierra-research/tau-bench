# Copyright Sierra
# One wrapped agent for Phase 3 smoke test: orchestrated tool-calling with logging.
# Uses minimal run loop (proposer → validator stub → executor) and run_logger from kwargs.

from typing import Any, Dict, List, Optional

from tau_bench.agents.base import Agent
from tau_bench.agents.tool_calling_agent import ToolCallingAgent
from tau_bench.envs.base import Env
from tau_bench.orchestration.logging import NoOpRunLogger, create_run_logger
from tau_bench.orchestration.run_loop import run_orchestrated_loop
from tau_bench.types import SolveResult


class OrchestratedToolCallingAgent(Agent):
    """Wraps ToolCallingAgent; runs via orchestrator loop and logs when run_logger is provided."""

    def __init__(
        self,
        tools_info: List[Dict[str, Any]],
        wiki: str,
        model: str,
        provider: str,
        temperature: float = 0.0,
    ):
        self._agent = ToolCallingAgent(
            tools_info=tools_info,
            wiki=wiki,
            model=model,
            provider=provider,
            temperature=temperature,
        )

    def solve(
        self,
        env: Env,
        task_index: Optional[int] = None,
        max_num_steps: int = 30,
        **kwargs,
    ) -> SolveResult:
        run_logger = kwargs.get("run_logger")
        if run_logger is None:
            run_logger = NoOpRunLogger()
        return run_orchestrated_loop(
            env=env,
            proposer=self._agent,
            run_logger=run_logger,
            task_index=task_index,
            max_num_steps=max_num_steps,
        )
