# Copyright Sierra

from typing import Optional, Union

from tau_bench.envs.base import Env
from tau_bench.envs.user import UserStrategy


def get_env(
    env_name: str,
    user_strategy: Union[str, UserStrategy],
    user_model: str,
    task_split: str,
    user_provider: Optional[str] = None,
    task_index: Optional[int] = None,
    user_model_base_url: str=None,
) -> Env:
    if env_name == "retail":
        from tau_bench.envs.retail import MockRetailDomainEnv

        return MockRetailDomainEnv(
            user_strategy=user_strategy,
            user_model=user_model,
            user_model_base_url=user_model_base_url,
            task_split=task_split,
            user_provider=user_provider,
            task_index=task_index,
        )
    elif env_name == "airline":
        from tau_bench.envs.airline import MockAirlineDomainEnv

        return MockAirlineDomainEnv(
            user_strategy=user_strategy,
            user_model=user_model,
            user_model_base_url=user_model_base_url,
            task_split=task_split,
            user_provider=user_provider,
            task_index=task_index,
        )
    elif env_name == "telecom":
        from tau_bench.envs.telecom import MockTelecomDomainEnv

        return MockTelecomDomainEnv(
            user_strategy=user_strategy,
            user_model=user_model,
            user_model_base_url=user_model_base_url,
            task_split=task_split,
            user_provider=user_provider,
            task_index=task_index,
        )
    elif env_name == "telehealth":
        from tau_bench.envs.telehealth import MockTelehealthDomainEnv

        return MockTelehealthDomainEnv(
            user_strategy=user_strategy,
            user_model=user_model,
            user_model_base_url=user_model_base_url,
            task_split=task_split,
            user_provider=user_provider,
            task_index=task_index,
        )
    else:
        raise ValueError(f"Unknown environment: {env_name}")
