import random

from datasets import Dataset, DatasetDict

from tau_bench.model_utils import Datapoint
from tau_bench.model_utils.training_tools.build_prompts import (
    InputType,
    PromptSuffixStrategy,
    build_prompts,
)


def datapoints_to_hf_dataset(
    dps: list[Datapoint],
    input_type: InputType = InputType.CHAT,
    prompt_suffix_strategy: PromptSuffixStrategy | None = None,
    train_test_split: float | None = None,
) -> Dataset | DatasetDict:
    grouped_by_type: dict[type, list[Datapoint]] = {}
    for dp in dps:
        if type(dp) not in grouped_by_type:
            grouped_by_type[type(dp)] = []
        grouped_by_type[type(dp)].append(dp)
    grouped_prompts = [
        build_prompts(
            dps=dps_from_type, input_type=input_type, prompt_suffix_strategy=prompt_suffix_strategy
        )
        for dps_from_type in grouped_by_type.values()
    ]
    prompts = [prompt for prompts in grouped_prompts for prompt in prompts]
    if input_type == InputType.CHAT:
        prompts = [{"messages": [msg.model_dump() for msg in prompt]} for prompt in prompts]
    random.shuffle(prompts)
    if train_test_split is None:
        return Dataset.from_list(prompts)
    split_idx = int(len(prompts) * train_test_split)
    return DatasetDict(
        {
            "train": Dataset.from_list(prompts[:split_idx]),
            "eval": Dataset.from_list(prompts[split_idx:]),
        }
    )
