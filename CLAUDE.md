# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

τ-bench (tau-bench) is a benchmark for evaluating language model agents in real-world domains (retail and airline) through tool-agent-user interactions. It simulates dynamic conversations between:
- A **Language Agent** using LLMs with domain-specific API tools
- A **User Simulator** (also LLM-based) simulating realistic user behavior
- An **Environment** managing state, tool execution, and reward calculation

**Paper**: https://arxiv.org/abs/2406.12045

## Common Commands

### Setup
```bash
conda activate Tau1
pip install -e .
pip install python-dotenv  # Optional, for .env file support
```

### Running Benchmarks

Basic run on retail domain:
```bash
python run.py --model gpt-4o --model-provider openai --env retail --max-concurrency 10
```

Run specific tasks:
```bash
python run.py --model gpt-4o --model-provider openai --env retail --task-ids 0 2 4
```

With OpenRouter (Qwen):
```bash
python run.py --model openrouter/qwen/qwen3-8b --model-provider openrouter --env retail --env-file .env
```

With DashScope (Alibaba):
```bash
python run.py --model qwen3-8b --model-provider dashscope --env retail --env-file .env
```

With local model (vLLM):
```bash
python run.py --model qwen3-8b --model-provider local --model-base-url http://localhost:8000/v1 --env retail
```

### Key CLI Arguments
- `--env {retail, airline}` - Domain environment
- `--agent-strategy {tool-calling, act, react, few-shot}` - Agent strategy
- `--task-split {train, test, dev}` - Task set (retail only)
- `--task-ids 1 2 3` - Run specific tasks
- `--max-concurrency N` - Parallel task execution
- `--env-file .env` - Load API keys from file
- `--model-base-url URL` - For local/custom model endpoints

### Auto Error Identification
```bash
python auto_error_identification.py --env retail --platform openai --results-path results/my_run.json --output-path error_analysis
```

## Architecture

```
tau_bench/
├── agents/           # Agent implementations
│   ├── tool_calling_agent.py  # Native function calling (best performance)
│   ├── chat_react_agent.py    # ReAct and Act strategies
│   └── few_shot_agent.py      # In-context learning
├── envs/             # Environment definitions
│   ├── base.py       # Base environment (state, rewards, tool dispatch)
│   ├── user.py       # User simulator strategies
│   ├── retail/       # Retail domain (16 tools, 3 task splits)
│   └── airline/      # Airline domain (13 tools)
├── model_utils/
│   └── provider_setup.py  # Multi-provider support (OpenRouter, DashScope, local)
├── run.py            # Core orchestration, metrics calculation
└── types.py          # Pydantic models (Task, Action, SolveResult, RunConfig)
```

### Key Abstractions

**Agent** (`agents/base.py`): Abstract base with `solve(env, task_index) -> SolveResult`

**Environment** (`envs/base.py`):
- `reset(task_index)` - Initialize task state
- `step(action)` - Execute tool, return observation
- `calculate_reward()` - Check DB changes and expected outputs

**Tool** (`envs/tool.py`): Static `invoke(data, **kwargs)` and `get_info()` for OpenAI function schema

**User Simulator** (`envs/user.py`): Strategies - `human`, `llm`, `react`, `verify`, `reflection`

### Execution Flow
1. Parse CLI args → `RunConfig`
2. Load environment variables (supports .env)
3. Setup model provider (handles prefixes for OpenRouter/DashScope)
4. Create environment and agent
5. ThreadPoolExecutor runs tasks in parallel
6. Each task: `env.reset()` → agent `solve()` loop (up to 30 steps) → `calculate_reward()`
7. Results checkpointed to JSON incrementally

## Provider Reference

### 1. Alibaba DashScope - Singapore (Default)

| Model | Model ID | Notes |
|-------|----------|-------|
| Qwen3-4B | qwen3-4b | |
| Qwen3-8B | qwen3-8b | Recommended start |
| Qwen3-14B | qwen3-14b | Better reasoning |
| Qwen3-32B | qwen3-32b | Best quality |

Setup: `DASHSCOPE_API_KEY` from https://dashscope.console.aliyun.com/
```bash
python run.py --model qwen3-8b --model-provider dashscope --dashscope-region singapore
```

### 2. Alibaba DashScope - US

| Model | Model ID |
|-------|----------|
| Qwen3-8B | qwen3-8b |
| Qwen3-32B | qwen3-32b |

```bash
python run.py --model qwen3-8b --model-provider dashscope --dashscope-region us
```

### 3. OpenRouter - Any Region

| Model | Model ID |
|-------|----------|
| Qwen3-8B | qwen/qwen3-8b |
| Qwen3-14B | qwen/qwen3-14b |
| Qwen3-32B | qwen/qwen3-32b |
| GPT-OSS-20B | openai/gpt-oss-20b |

Setup: `OPENROUTER_API_KEY` from https://openrouter.ai/
```bash
python run.py --model qwen/qwen3-8b --model-provider openrouter
```

### 4. Local / Self-Hosted

| Deployment | Example |
|------------|---------|
| Single Server | `--model-base-url http://localhost:8000/v1` |
| Remote Server | `--model-base-url http://192.168.1.50:8000/v1` |
| With Auth | `--model-api-key YOUR_AUTH_TOKEN` |

Setup: Start server with OpenAI-compatible API (vLLM, LM Studio, etc.)
```bash
python run.py --model qwen3-8b --model-provider local --model-base-url http://localhost:8000/v1
```

## Data Locations

- `few_shot_data/` - Example interactions for few-shot prompting
- `historical_trajectories/` - Pre-computed benchmark results
- `results/` - Output directory for runs (JSON format)
- `tau_bench/envs/retail/data/` - Retail task definitions and database
- `tau_bench/envs/airline/data/` - Airline task definitions and database

## API Keys

Set as environment variables or use `--env-file`:
```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
MISTRAL_API_KEY=...
OPENROUTER_API_KEY=...
DASHSCOPE_API_KEY=...
```

## Quick Start

See **QUICKSTART.md** for step-by-step instructions to get running in 5 minutes.

## Cost Estimates

See **COST_ESTIMATES.md** for detailed pricing:
- Run all 3 Qwen models on all 685 tasks for only **$3.78**
- Detailed breakdowns by model, task count, and time estimates
- Budget planning and optimization tips
