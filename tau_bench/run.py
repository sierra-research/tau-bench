# Copyright Sierra

import os
import json
import random
import traceback
from math import comb
import multiprocessing
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from tau_bench.envs import get_env
from tau_bench.agents.base import Agent
from tau_bench.types import EnvRunResult, RunConfig
from litellm import provider_list
from tau_bench.envs.user import UserStrategy
from tau_bench.model_utils.provider_setup import load_env_file, setup_provider

# Extended provider list to include custom providers
EXTENDED_PROVIDERS = list(provider_list) + ["openrouter", "dashscope", "local"]


def run(config: RunConfig) -> List[EnvRunResult]:
    assert config.env in ["retail", "airline"], "Only retail and airline envs are supported"
    assert config.model_provider in EXTENDED_PROVIDERS, f"Invalid model provider: {config.model_provider}. Valid providers: {EXTENDED_PROVIDERS}"
    assert config.user_model_provider in EXTENDED_PROVIDERS, f"Invalid user model provider: {config.user_model_provider}"
    assert config.agent_strategy in ["tool-calling", "act", "react", "few-shot"], "Invalid agent strategy"
    assert config.task_split in ["train", "test", "dev"], "Invalid task split"
    assert config.user_strategy in [item.value for item in UserStrategy], "Invalid user strategy"

    # Load environment variables from .env file if specified
    if config.env_file:
        load_env_file(config.env_file)

    # Setup model provider (handles prefix formatting for openrouter, dashscope, local)
    model, model_provider, model_api_base = setup_provider(
        config.model, config.model_provider, config.model_base_url
    )
    
    # Setup user model provider
    user_model, user_provider, user_api_base = setup_provider(
        config.user_model, config.user_model_provider, config.user_model_base_url
    )
    
    print(f"Model: {model} (provider: {model_provider}, api_base: {model_api_base})")
    print(f"User Model: {user_model} (provider: {user_provider}, api_base: {user_api_base})")

    random.seed(config.seed)
    time_str = datetime.now().strftime("%m%d%H%M%S")
    # Sanitize model name for checkpoint filename (remove slashes)
    model_name_safe = model.replace('/', '_')
    ckpt_path = f"{config.log_dir}/{config.agent_strategy}-{model_name_safe}-{config.temperature}_range_{config.start_index}-{config.end_index}_user-{config.user_model}-{config.user_strategy}_{time_str}.json"
    if not os.path.exists(config.log_dir):
        os.makedirs(config.log_dir)

    print(f"Loading user with strategy: {config.user_strategy}")
    env = get_env(
        config.env,
        user_strategy=config.user_strategy,
        user_model=user_model,
        user_provider=user_provider,
        task_split=config.task_split,
        user_api_base=user_api_base,
    )
    agent = agent_factory(
        tools_info=env.tools_info,
        wiki=env.wiki,
        model=model,
        provider=model_provider,
        temperature=config.temperature,
        api_base=model_api_base,
        agent_strategy=config.agent_strategy,
        few_shot_displays_path=config.few_shot_displays_path,
    )
    end_index = (
        len(env.tasks) if config.end_index == -1 else min(config.end_index, len(env.tasks))
    )
    results: List[EnvRunResult] = []
    lock = multiprocessing.Lock()
    if config.task_ids and len(config.task_ids) > 0:
        print(f"Running tasks {config.task_ids} (checkpoint path: {ckpt_path})")
    else:
        print(
            f"Running tasks {config.start_index} to {end_index} (checkpoint path: {ckpt_path})"
    )
    for i in range(config.num_trials):
        if config.task_ids and len(config.task_ids) > 0:
            idxs = config.task_ids
        else:
            idxs = list(range(config.start_index, end_index))
        if config.shuffle:
            random.shuffle(idxs)

        def _run(idx: int) -> EnvRunResult:
            isolated_env = get_env(
                config.env,
                user_strategy=config.user_strategy,
                user_model=user_model,
                task_split=config.task_split,
                user_provider=user_provider,
                user_api_base=user_api_base,
                task_index=idx,
            )

            print(f"Running task {idx}")
            try:
                res = agent.solve(
                    env=isolated_env,
                    task_index=idx,
                )
                result = EnvRunResult(
                    task_id=idx,
                    reward=res.reward,
                    info=res.info,
                    traj=res.messages,
                    trial=i,
                )
            except Exception as e:
                result = EnvRunResult(
                    task_id=idx,
                    reward=0.0,
                    info={"error": str(e), "traceback": traceback.format_exc()},
                    traj=[],
                    trial=i,
                )
            print(
                "✅" if result.reward == 1 else "❌",
                f"task_id={idx}",
                result.info,
            )
            print("-----")
            with lock:
                data = []
                if os.path.exists(ckpt_path):
                    with open(ckpt_path, "r") as f:
                        data = json.load(f)
                with open(ckpt_path, "w") as f:
                    json.dump(data + [result.model_dump()], f, indent=2)
            return result

        with ThreadPoolExecutor(max_workers=config.max_concurrency) as executor:
            res = list(executor.map(_run, idxs))
            results.extend(res)

    display_metrics(results)

    with open(ckpt_path, "w") as f:
        json.dump([result.model_dump() for result in results], f, indent=2)
        print(f"\n📄 Results saved to {ckpt_path}\n")
    return results


def agent_factory(
    tools_info: List[Dict[str, Any]],
    wiki: str,
    model: str,
    provider: str,
    temperature: float,
    api_base: Optional[str] = None,
    agent_strategy: str = "tool-calling",
    few_shot_displays_path: Optional[str] = None,
) -> Agent:
    if agent_strategy == "tool-calling":
        # native tool calling
        from tau_bench.agents.tool_calling_agent import ToolCallingAgent

        return ToolCallingAgent(
            tools_info=tools_info,
            wiki=wiki,
            model=model,
            provider=provider,
            temperature=temperature,
            api_base=api_base,
        )
    elif agent_strategy == "act":
        # `act` from https://arxiv.org/abs/2210.03629
        from tau_bench.agents.chat_react_agent import ChatReActAgent

        return ChatReActAgent(
            tools_info=tools_info,
            wiki=wiki,
            model=model,
            provider=provider,
            use_reasoning=False,
            temperature=temperature,
            api_base=api_base,
        )
    elif agent_strategy == "react":
        # `react` from https://arxiv.org/abs/2210.03629
        from tau_bench.agents.chat_react_agent import ChatReActAgent

        return ChatReActAgent(
            tools_info=tools_info,
            wiki=wiki,
            model=model,
            provider=provider,
            use_reasoning=True,
            temperature=temperature,
            api_base=api_base,
        )
    elif agent_strategy == "few-shot":
        from tau_bench.agents.few_shot_agent import FewShotToolCallingAgent
        assert few_shot_displays_path is not None, "Few shot displays path is required for few-shot agent strategy"
        with open(few_shot_displays_path, "r") as f:
            few_shot_displays = [json.loads(line)["messages_display"] for line in f]

        return FewShotToolCallingAgent(
            tools_info=tools_info,
            wiki=wiki,
            model=model,
            provider=provider,
            few_shot_displays=few_shot_displays,
            temperature=temperature,
            api_base=api_base,
        )
    else:
        raise ValueError(f"Unknown agent strategy: {agent_strategy}")


def display_metrics(results: List[EnvRunResult]) -> None:
    def is_successful(reward: float) -> bool:
        return (1 - 1e-6) <= reward <= (1 + 1e-6)

    num_trials = len(set([r.trial for r in results]))
    rewards = [r.reward for r in results]
    avg_reward = sum(rewards) / len(rewards)
    # c from https://arxiv.org/pdf/2406.12045
    c_per_task_id: dict[int, int] = {}
    for result in results:
        if result.task_id not in c_per_task_id:
            c_per_task_id[result.task_id] = 1 if is_successful(result.reward) else 0
        else:
            c_per_task_id[result.task_id] += 1 if is_successful(result.reward) else 0
    pass_hat_ks: dict[int, float] = {}
    for k in range(1, num_trials + 1):
        sum_task_pass_hat_k = 0
        for c in c_per_task_id.values():
            sum_task_pass_hat_k += comb(c, k) / comb(num_trials, k)
        pass_hat_ks[k] = sum_task_pass_hat_k / len(c_per_task_id)
    print(f"🏆 Average reward: {avg_reward}")
    print("📈 Pass^k")
    for k, pass_hat_k in pass_hat_ks.items():
        print(f"  k={k}: {pass_hat_k}")
