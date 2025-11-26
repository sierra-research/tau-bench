#!/usr/bin/env bash
set -euo pipefail

# ---- Env (offline) ----
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

# ---- Model path ----
MODEL_DIR="/data/datasets/community/huggingface/models--Qwen--Qwen3-4B/snapshots/82d62bb073771e7a1ea59435f548908540217d1f/"
# MODEL_DIR="/data/datasets/community/huggingface/models--openai--gpt-oss-20b/snapshots/f47b95650b3ce7836072fb6457b362a795993484/"
# ---- Launch vLLM in background ----
python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_DIR" \
  --port 8000 \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.9 \
  --served-model-name qwen3-4b \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --chat-template /home/rksing18/applied/UserBench/tool_template/hermes.jinja \
  --tensor-parallel-size 1 \
  > vllm.log 2>&1 &

VLLM_PID=$!
echo "vLLM started as PID $VLLM_PID; logs -> vllm.log"

# ---- Wait for readiness ----
echo -n "Waiting for vLLM to be ready"
until curl -sSf http://localhost:8000/v1/models >/dev/null 2>&1; do
  echo -n "."
  sleep 1
done
echo " ready."

# ---- Run eval ----
python run.py \
  --agent-strategy tool-calling \
  --env telecom \
  --model hosted_vllm/qwen3-4b \
  --model-provider hosted_vllm \
  --user-model hosted_vllm/qwen3-4b \
  --user-model-provider hosted_vllm \
  --user-strategy llm \
  --max-concurrency 10 \
  --task-ids 2 \
  --model-base-url http://localhost:8000/v1 \
  --user-model-base-url http://localhost:8000/v1


# python run.py \
#   --agent-strategy tool-calling \
#   --env telecom \
#   --model hosted_vllm/gpt-oss-20b \
#   --model-provider hosted_vllm \
#   --user-model hosted_vllm/gpt-oss-20b \
#   --user-model-provider hosted_vllm \
#   --user-strategy llm \
#   --max-concurrency 10 \
#   --task-ids 2 \
#   --model-base-url http://sg237:8000/v1 \
#   --user-model-base-url http://sg237:8000/v1
