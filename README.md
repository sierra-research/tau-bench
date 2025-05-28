# τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains


**Paper**: [https://arxiv.org/abs/2406.12045](https://arxiv.org/abs/2406.12045)

## Leaderboard

### Airline

| Strategy       | Pass^1 | Pass^2 | Pass^3 | Pass^4 |
| -------------- | ------ | ------ | ------ | ------ |
| [TC (claude-3-5-sonnet-20241022)](https://www.anthropic.com/news/3-5-models-and-computer-use)      | **0.460**     | **0.326**     | **0.263**     | **0.225**     |
| [TC (gpt-4o)](https://platform.openai.com/docs/guides/function-calling)     | 0.420     | 0.273     | 0.220     | 0.200     |
| [TC (claude-3-5-sonnet-20240620)](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)      | 0.360     | 0.224     | 0.169     | 0.139     |
| [TC (mistral-large-2407)](https://docs.mistral.ai/capabilities/function_calling/)     | ??     | ??     | ??     | ??     |
| [TC (gpt-4o-mini)](https://platform.openai.com/docs/guides/function-calling)     | 0.225     | 0.140     | 0.110     | 0.100     |
| [Act](https://arxiv.org/abs/2210.03629) (gpt-4o)     | 0.365 | 0.217 | 0.160 | 0.140     |
| [ReAct](https://arxiv.org/abs/2210.03629) (gpt-4o)     | 0.325 | 0.233 | 0.185 | 0.160     |

### Retail

| Strategy       | Pass^1 | Pass^2 | Pass^3 | Pass^4 |
| -------------- | ------ | ------ | ------ | ------ |
| [TC (claude-3-5-sonnet-20241022)](https://www.anthropic.com/news/3-5-models-and-computer-use)      | **0.692**     | **0.576**     | **0.509**     | **0.462**     |
| [TC (gpt-4o)](https://platform.openai.com/docs/guides/function-calling)     | 0.604     | 0.491     | 0.430     | 0.383     |
| [TC (claude-3-5-sonnet-20240620)](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)      | 0.626     | 0.506     | 0.435     | 0.387     |
| [TC (mistral-large-2407)](https://docs.mistral.ai/capabilities/function_calling/)     | ??     | ??     | ??     | ??     |
| [TC (gpt-4o-mini)](https://platform.openai.com/docs/guides/function-calling)     | ??     | ??     | ??     | ??     |
| [Act](https://arxiv.org/abs/2210.03629) (gpt-4o)     | ??     | ??     | ??     | ??     |
| [ReAct](https://arxiv.org/abs/2210.03629) (gpt-4o)     | ??     | ??     | ??     | ??     |

*TC = `tool-calling` strategy (the function-calling strategy reported in the paper)

# install DF CX SDK

```
gsutil cp gs://agent-evals/v3alpha1_dialogflow-v3alpha1-py.tar /content/v3alpha1_dialogflow-v3alpha1-py.tar
tar -xvf content/v3alpha1_dialogflow-v3alpha1-py.tar
venv/bin/python3 dialogflow-v3alpha1-py/setup.py sdist
venv/bin/pip install content/v3alpha1_dialogflow-v3alpha1-py.tar

venv/bin/pip install google-cloud-dialogflow-cx
```

## Setup

1. Clone this repository:

```bash
git clone https://github.com/sierra-research/tau-bench && cd ./tau-bench
```

2. Install from source (which also installs required packages):

```bash
pip install -e .
```

3. Set up your OpenAI / Anthropic / Google / Mistral / AnyScale API keys as environment variables.

```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
MISTRAL_API_KEY=...
```

## Run

Run a tool-calling agent on the τ-retail environment:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --user-model gpt-4o --user-model-provider openai --user-strategy llm --max-concurrency 10
```

Set max concurrency according to your API limit.

To run specific tasks, use the `--task-ids` flag. For example:

Run a decibel agent with gemini as user model: 

```bash
venv/bin/python3 tau-bench/run.py --env retail  --agent_strategy decibel --agent_id 429da584-b933-4372-822c-52d124ba5a26 --project_id df-decibel2-dev-test  --start_index 0 --end_index -1  --user_model gemini-1.5-pro
```

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --user-model gpt-4o --user-model-provider openai --user-strategy llm --max-concurrency 10 --task-ids 2 4 6
```

This command will run only the tasks with IDs 2, 4, and 6.

## User simulators

By default, we use `gpt-4o` as the user simulator with strategy `llm`. You can use other models by setting the `--user-model` flag, or other strategies by setting the `--user-strategy` flag. For example, run a tool-calling agent with a claude user simulator:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --max-concurrency 10 --user-model claude-3-5-sonnet-20240620 --user-model-provider anthropic --user-strategy llm
```

Other strategies:

To run `react` user simulator:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --max-concurrency 10 --user-model gpt-4o --user-model-provider openai --user-strategy react
```

Example of a `react` user response:

```md
Thought:
I should provide my name and zip code as I wasn't given an email address to use.

User Response:
Sure, my name is Yusuf Rossi, and my zip code is 19122.
```

To run `verify` user simulator:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --max-concurrency 10 --user-model gpt-4o --user-model-provider openai --user-strategy verify
```

This strategy uses a subsequent LLM verification step to check if the user simulator's response is satisfactory. If not, the user simulator will be prompted to generate a new response.

To run `reflection` user simulator:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --max-concurrency 10 --user-model gpt-4o --user-model-provider openai --user-strategy reflection
```

This strategy uses a subsequent LLM verification step to check if the user simulator's response is satisfactory. If not, the user simulator will be prompted to reflect on its response and generate a new response.

## Auto error identification

Often times, it is difficult and time consuming to manually identify specific error locations in trajectories as they can be long and the constraints can be complex. We have provided an auto error identification tool that can do the following:

1. Fault assignment: determine the entity that is responsible for the fault (user, agent, environment)
2. Fault type classification: classify the type of fault (goal_partially_completed, used_wrong_tool, used_wrong_tool_argument, took_unintended_action)

Both of the labels are accompanied with a description.

To run the auto error identification, run:

```bash
python auto_error_identification.py --env <airline/retail> --platform openai --results-path <the path to your results file here> --max-concurrency 16 --output-path test-auto-error-identification --max-num-failed-results 10
```

Please note that this feature utilizes an LLM, which may lead to inaccurate error identifications.

*Notice: If an error is raised due to the structure of your results file, you may have to rerun the benchmark to produce a new results file. We have recently [rewritten](https://github.com/sierra-research/tau-bench/commit/043b544371757ebb3762b3d02a6675dfe0c41798) the benchmark to be more type-safe and extensible.

## Historical trajectories

τ-bench might be expensive to run. We have provided a set of historical trajectories for the airline and retail environments in `./historical_trajectories`.

If you would like to contribute your historical trajectories to this benchmark, please submit a PR!

## License

See `./LICENSE`.

## Contact

Please submit issues or pull requests if you find problems with the benchmark.

## Citation

```bibtex
@misc{yao2024tau,
      title={$\tau$-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains}, 
      author={Shunyu Yao and Noah Shinn and Pedram Razavi and Karthik Narasimhan},
      year={2024},
      eprint={2406.12045},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2406.12045}, 
}
```
