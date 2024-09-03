# Copyright Sierra

from typing import Optional
from tau_bench.envs.base import Env


def get_env(
    env_name: str,
    user_strategy: str,
    user_model: str,
    task_split: str,
    user_provider: Optional[str] = None,
) -> Env:
    if env_name == "retail":
        from tau_bench.envs.retail import MockRetailDomainEnv

        return MockRetailDomainEnv(
            user_strategy=user_strategy,
            user_model=user_model,
            task_split=task_split,
            user_provider=user_provider,
        )
    elif env_name == "airline":
        from tau_bench.envs.airline import MockAirlineDomainEnv

        return MockAirlineDomainEnv(
            user_strategy=user_strategy,
            user_model=user_model,
            task_split=task_split,
            user_provider=user_provider,
        )
    else:
        raise ValueError(f"Unknown environment: {env_name}")
