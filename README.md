# τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains

https://arxiv.org/abs/2406.12045

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
GEMINI_API_KEY=...
MISTRAL_API_KEY=...
ANYSCALE_API_KEY=...
```


## Run

Run a function calling agent on the τ-retail environment:

```bash
python run.py --env retail --model gpt-4o --max_concurrency 10
```

Set max concurrency according to your API limit.

## User simulators

By default, we use `gpt-4o` as the user simulator. You can use other models by setting the `--user_model` flag. For example, run a function calling agent with a claude user simulator:

```bash
python run.py --env retail --model gpt-4o --max_concurrency 10 --user_model claude-3-5-sonnet-20240620
```

## License

MIT.

## Contact

Please submit issues or pull requests if you find problems with the benchmark.
