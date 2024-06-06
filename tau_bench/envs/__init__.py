# Copyright Sierra


def get_env(env_name: str, user_mode: str, user_model: str, task_split: str):
    if env_name == "retail":
        from tau_bench.envs.retail import MockRetailDomainEnv

        return MockRetailDomainEnv(
            user_mode=user_mode, user_model=user_model, task_split=task_split
        )
    elif env_name == "airline":
        from tau_bench.envs.airline import MockAirlineDomainEnv

        return MockAirlineDomainEnv(
            user_mode=user_mode, user_model=user_model, task_split=task_split
        )
    else:
        raise ValueError(f"Unknown environment: {env_name}")
