# τ-bench Quick Start Guide

Get started running benchmarks with Qwen models in 5 minutes!

## 1. Setup (One-time)

```bash
# Activate conda environment
conda activate Tau1

# Copy environment template
cp .env.template .env

# Edit and add your API keys
nano .env
```

**Add these lines to .env:**
```
DASHSCOPE_API_KEY=sk-...  # Get from https://dashscope.console.aliyun.com/
OPENROUTER_API_KEY=sk-or-v1-...  # Get from https://openrouter.ai/
```

## 2. Quick Commands

### Using the Convenience Script (Easiest)

```bash
# See all available commands
./run_examples.sh

# Run examples
./run_examples.sh dashscope-sg-8b
./run_examples.sh openrouter-32b
./run_examples.sh local-8000
```

### Direct Commands

```bash
# DashScope Singapore - Qwen3-8B
python run.py \
  --env retail \
  --model qwen3-8b \
  --model-provider dashscope \
  --dashscope-region singapore \
  --user-model openai/gpt-oss-20b \
  --user-model-provider openrouter

# DashScope US - Qwen3-14B
python run.py \
  --env retail \
  --model qwen3-14b \
  --model-provider dashscope \
  --dashscope-region us \
  --user-model openai/gpt-oss-20b \
  --user-model-provider openrouter

# OpenRouter - Qwen3-32B
python run.py \
  --env airline \
  --model qwen/qwen3-32b \
  --model-provider openrouter \
  --user-model openai/gpt-oss-20b \
  --user-model-provider openrouter

# Local Model on Port 8000
python run.py \
  --env retail \
  --model qwen3-8b \
  --model-provider local \
  --model-base-url http://localhost:8000/v1 \
  --user-model openai/gpt-oss-20b \
  --user-model-provider openrouter
```

## 3. Common Options

```bash
--env retail|airline              # Choose environment
--task-ids 0 1 2 3               # Run specific tasks (optional)
--max-concurrency 5              # Parallel tasks (default: 1)
--num-trials 3                   # Run each task N times
--agent-strategy tool-calling|react|act|few-shot
--user-strategy llm|react|verify|reflection
--max-tokens 1000               # Agent response length
--user-max-tokens 500           # User response length
```

## 4. Model Overview

### All DashScope Models

| Model | Singapore | US |
|-------|-----------|-----|
| qwen3-4b | Yes | Yes |
| qwen3-8b | Yes | Yes |
| qwen3-14b | Yes | Yes |
| qwen3-32b | Yes | Yes |

```bash
# Use --dashscope-region singapore or us (default: singapore)
python run.py --model qwen3-8b --model-provider dashscope --dashscope-region us ...
```

### All OpenRouter Models

- `qwen/qwen3-8b`
- `qwen/qwen3-14b`
- `qwen/qwen3-32b`
- `openai/gpt-oss-20b`

```bash
python run.py --model qwen/qwen3-8b --model-provider openrouter ...
```

### Local Models

Run on your own servers with OpenAI-compatible API (vLLM, LM Studio, etc.)

```bash
# Start your local server first
python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen-3-8B --port 8000

# Then run benchmark
python run.py \
  --model qwen3-8b \
  --model-provider local \
  --model-base-url http://localhost:8000/v1 \
  --user-model openai/gpt-oss-20b \
  --user-model-provider openrouter
```

## 5. Real-World Examples

### Example 1: Quick Test (2 minutes)

```bash
./run_examples.sh dashscope-sg-4b --task-ids 0 1 2
```

### Example 2: Full Benchmark Suite

```bash
./run_examples.sh dashscope-sg-8b --task-split test --max-concurrency 5
```

### Example 3: Compare DashScope vs OpenRouter

```bash
# Run on DashScope Singapore
./run_examples.sh dashscope-sg-8b --task-ids 0 1 2 3 4

# Run on OpenRouter
./run_examples.sh openrouter-8b --task-ids 0 1 2 3 4

# Compare results in results/ directory
```

### Example 4: Local + Cloud Hybrid

```bash
# Agent on local server, user on OpenRouter
./run_examples.sh local-8000 --env retail --max-concurrency 2
```

### Example 5: Multiple Trials for Stability

```bash
./run_examples.sh dashscope-sg-14b --num-trials 3 --max-concurrency 2
```

## 6. Check Results

```bash
# List all results
ls -lh results/

# View latest result
cat results/*.json | tail -1 | jq '.'

# Calculate average reward
cat results/*.json | jq '.[].reward' | awk '{sum+=$1; count++} END {print "Average:", sum/count}'
```

## 7. Troubleshooting

### Error: DASHSCOPE_API_KEY not set
```bash
# Add to .env file:
echo "DASHSCOPE_API_KEY=sk-..." >> .env
```

### Error: Connection refused (localhost:8000)
```bash
# Start your local server:
python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen-3-8B --port 8000
```

### Error: Model not found
- Check spelling: `qwen3-8b` (not `qwen-3-8b`)
- For OpenRouter: `qwen/qwen3-8b` (with prefix)

## 8. Performance Tips

| Scenario | Command |
|----------|---------|
| Fastest test | `--max-concurrency 1 --task-ids 0` |
| Quick run | `--max-concurrency 3 --task-ids 0 1 2 3 4` |
| Full test | `--max-concurrency 5 --task-split test` |
| Full train | `--max-concurrency 10 --task-split train` |
| Local models | `--max-concurrency 1` (limited by server) |

## 9. Running All Qwen Models

### All DashScope Singapore Models

```bash
# 4B
./run_examples.sh dashscope-sg-4b

# 8B
./run_examples.sh dashscope-sg-8b

# 14B
./run_examples.sh dashscope-sg-14b

# 32B
./run_examples.sh dashscope-sg-32b
```

### All DashScope US Models

```bash
./run_examples.sh dashscope-us-8b
./run_examples.sh dashscope-us-32b
```

### All OpenRouter Models

```bash
./run_examples.sh openrouter-8b
./run_examples.sh openrouter-14b
./run_examples.sh openrouter-32b
./run_examples.sh openrouter-gpt
```

### All Local Models

```bash
# Single local server
./run_examples.sh local-8000

# Dual local servers (agent + user)
./run_examples.sh local-dual

# Remote server
./run_examples.sh local-remote
```

## 10. Advanced: Custom Configuration

```bash
# Custom agent + user combination
python run.py \
  --env retail \
  --agent-strategy react \
  --model qwen/qwen3-14b \
  --model-provider openrouter \
  --user-model qwen3-8b \
  --user-model-provider dashscope \
  --dashscope-region us \
  --user-strategy react \
  --task-split test \
  --max-concurrency 2 \
  --num-trials 3 \
  --temperature 0.2
```

---

## Full Documentation

For detailed examples and advanced configurations, see:
- **CLAUDE.md** - Architecture, design patterns, and extending the system
- **run.py --help** - All available CLI arguments

## Ready?

```bash
# Start here:
conda activate Tau1
./run_examples.sh

# Or jump straight to:
./run_examples.sh dashscope-sg-8b
```
