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
    strict_output_match: Optional[bool] = None,
    preserve_data_on_reward: Optional[bool] = None,
) -> Env:
    if env_name == "retail":
        from tau_bench.envs.retail import MockRetailDomainEnv

        return MockRetailDomainEnv(
            user_strategy=user_strategy,
            user_model=user_model,
            task_split=task_split,
            user_provider=user_provider,
            task_index=task_index,
            strict_output_match=strict_output_match,
            preserve_data_on_reward=preserve_data_on_reward,
        )
    elif env_name == "airline":
        from tau_bench.envs.airline import MockAirlineDomainEnv

        return MockAirlineDomainEnv(
            user_strategy=user_strategy,
            user_model=user_model,
            task_split=task_split,
            user_provider=user_provider,
            task_index=task_index,
            strict_output_match=strict_output_match,
            preserve_data_on_reward=preserve_data_on_reward,
        )
    else:
        raise ValueError(f"Unknown environment: {env_name}")
