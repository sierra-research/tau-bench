#!/bin/bash
# Phase 3 smoke test: orchestrated-tool-calling with run logging.
# Output layout:
#   system_logs/{job_id}_smoketest.log, _smoketest.err, _taubench.log, _vllm_agent.log, _vllm_user.log
#   jobs/{job_id}/runs/A_T0_R0.log, .trace.jsonl, .summary.json
#   jobs/{job_id}/trajectories/{strategy}-{model}-...-{job_id}.json
# Ensure system_logs/ and jobs/ exist before sbatch (e.g. mkdir -p system_logs jobs).

#SBATCH --partition=gaudi
#SBATCH --qos=class_gaudi
#SBATCH --gres=gpu:hl225:4
#SBATCH --cpus-per-task=32
#SBATCH --mem=120G
#SBATCH --time=00:20:00
#SBATCH --output=system_logs/%j_smoketest.log
#SBATCH --error=system_logs/%j_smoketest.err

set -euo pipefail

# --- Models ---
AGENT_MODEL="Qwen/Qwen3-14B"
USER_MODEL="Qwen/Qwen3-32B"

###############################################################################

# --- Arguments (for smoke use start 0 end 1) ---
echo "Phase 3 smoke: orchestrated-tool-calling, 1 task, 1 trial"
DOMAIN="${1:-airline}"
START_IDX="${2:-0}"
END_IDX="${3:-1}"

# --- Params (smoke: one task, one trial) ---
MAX_LEN=16384
DTYPE="bfloat16"
GPU_UTIL=0.78
MAX_CONCURRENCY=1
NUM_TRIALS=1

SYSTEM_LOGS_DIR="$(pwd)/system_logs"
JOBS_DIR="$(pwd)/jobs"


echo "  AGENT_MODEL=$AGENT_MODEL  USER_MODEL=$USER_MODEL"
echo "  SYSTEM_LOGS_DIR=$SYSTEM_LOGS_DIR  JOBS_DIR=$JOBS_DIR"
###############################################################################


AGENT_STRATEGY="orchestrated-tool-calling"
echo "Job: Domain=$DOMAIN | Strategy=$AGENT_STRATEGY | Tasks $START_IDX to $END_IDX"

###############################################################################
cd "${SLURM_SUBMIT_DIR:-$PWD}"
mkdir -p "$SYSTEM_LOGS_DIR" "$JOBS_DIR"

echo "Node: $(hostname)"
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-}"
hl-smi || true

###############################################################################
source ~/miniconda3/etc/profile.d/conda.sh
conda activate taubench-py312
python -V

###############################################################################
SCRATCH_BASE="${SLURM_TMPDIR:-${SCRATCH:-/scratch/$USER}}"
JOB_ID="${SLURM_JOB_ID:-local}"
TB_SCRATCH="$SCRATCH_BASE/taubench/$JOB_ID"
mkdir -p "$TB_SCRATCH"/{hf,vllm,torch,xdg,tmp,logs,habana_logs}

HABANA_LOGS_HOST="$TB_SCRATCH/habana_logs"
export HF_HOME="$TB_SCRATCH/hf"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
export TRANSFORMERS_CACHE="$HF_HOME/transformers"
export HF_HUB_DISABLE_TELEMETRY=1
export VLLM_CACHE_ROOT="$TB_SCRATCH/vllm"
export TORCHINDUCTOR_CACHE_DIR="$TB_SCRATCH/torch"
export XDG_CACHE_HOME="$TB_SCRATCH/xdg"
export TMPDIR="$TB_SCRATCH/tmp"
export HABANA_LOGS_DIR="$TB_SCRATCH/habana_logs"
export HUGGINGFACE_HUB_TOKEN="${HUGGINGFACE_HUB_TOKEN:-${HF_TOKEN:-}}"
export NCCL_P2P_DISABLE=1
export NCCL_IB_DISABLE=1

CONTAINER="/data/sse/gaudi/containers/vllm-gaudi.sif"
export APPTAINERENV_HF_HOME="$HF_HOME"
export APPTAINERENV_HUGGINGFACE_HUB_CACHE="$HUGGINGFACE_HUB_CACHE"
export APPTAINERENV_TRANSFORMERS_CACHE="$TRANSFORMERS_CACHE"
export APPTAINERENV_VLLM_CACHE_ROOT="$VLLM_CACHE_ROOT"
export APPTAINERENV_XDG_CACHE_HOME="$XDG_CACHE_HOME"
export APPTAINERENV_TMPDIR="$TMPDIR"
export APPTAINERENV_HABANA_LOGS_DIR="/var/log/habana_logs"
export APPTAINERENV_VLLM_SKIP_WARMUP=true
export APPTAINERENV_VLLM_ENABLE_EXPERIMENTAL_FLAGS=1

USER_PORT=$((9000 + JOB_ID % 1000))
AGENT_PORT=$((9500 + JOB_ID % 1000))
HPU_AGENT=0,1
HPU_USER=2,3

cleanup() {
  echo "[CLEANUP] $(date) Stopping vLLM..."
  kill "${AGENT_PID:-}" "${USER_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT

for p in "$AGENT_PORT" "$USER_PORT"; do
  lsof -ti "tcp:${p}" 2>/dev/null | xargs -r kill -9 || true
done

echo "Starting USER vLLM: $USER_MODEL on port $USER_PORT..."
(
  HABANA_VISIBLE_DEVICES="$HPU_USER" APPTAINERENV_HABANA_VISIBLE_DEVICES="$HPU_USER" \
  apptainer exec \
    --bind /scratch:/scratch --bind /data:/data \
    --bind "$HABANA_LOGS_HOST:/var/log/habana_logs" \
    --env HABANA_LOGS_DIR=/var/log/habana_logs --env HABANA_VISIBLE_DEVICES="$HPU_USER" \
    "$CONTAINER" \
    vllm serve "$USER_MODEL" --device hpu --host 127.0.0.1 --port "$USER_PORT" \
    --dtype "$DTYPE" --max-model-len "$MAX_LEN" --gpu-memory-utilization "$GPU_UTIL" \
    --tensor-parallel-size 2 --trust-remote-code \
) > "$SYSTEM_LOGS_DIR/${JOB_ID}_vllm_user.log" 2>&1 &
USER_PID=$!

echo "Starting AGENT vLLM: $AGENT_MODEL on port $AGENT_PORT..."
(
  HABANA_VISIBLE_DEVICES="$HPU_AGENT" APPTAINERENV_HABANA_VISIBLE_DEVICES="$HPU_AGENT" \
  apptainer exec \
    --bind /scratch:/scratch --bind /data:/data \
    --bind "$HABANA_LOGS_HOST:/var/log/habana_logs" \
    --env HABANA_LOGS_DIR=/var/log/habana_logs --env HABANA_VISIBLE_DEVICES="$HPU_AGENT" \
    "$CONTAINER" \
    vllm serve "$AGENT_MODEL" --device hpu --host 127.0.0.1 --port "$AGENT_PORT" \
    --dtype "$DTYPE" --max-model-len "$MAX_LEN" --gpu-memory-utilization "$GPU_UTIL" \
    --tensor-parallel-size 2 --enable-auto-tool-choice --tool-call-parser hermes --trust-remote-code \
) > "$SYSTEM_LOGS_DIR/${JOB_ID}_vllm_agent.log" 2>&1 &
AGENT_PID=$!

wait_for_model() {
  local port="$1" model="$2" name="$3"
  echo "Waiting for $name on port $port..."
  timeout 1800 bash -c "until curl -s http://127.0.0.1:${port}/v1/models | grep -q '\"id\":\"${model}\"'; do sleep 5; done" || { echo "$name not ready"; exit 1; }
  echo "$name ready"
}
wait_for_model "$USER_PORT"  "$USER_MODEL"  "USER"
wait_for_model "$AGENT_PORT" "$AGENT_MODEL" "AGENT"

export OPENAI_API_BASE="http://127.0.0.1:${AGENT_PORT}/v1"
export USER_MODEL_API_BASE="http://127.0.0.1:${USER_PORT}/v1"
export OPENAI_API_KEY="EMPTY"
export TAU_BENCH_DEBUG_RESPOND_PATH=1

echo "Running Phase 3 benchmark (orchestrated-tool-calling)..."
python run.py \
  --agent-strategy "$AGENT_STRATEGY" \
  --env "$DOMAIN" \
  --model "$AGENT_MODEL" \
  --model-provider openai \
  --user-model "$USER_MODEL" \
  --user-model-provider openai \
  --user-strategy react \
  --max-concurrency "$MAX_CONCURRENCY" \
  --max-task-retries 3 \
  --task-retry-base-delay 5.0 \
  --num-trials "$NUM_TRIALS" \
  --temperature 0.0 \
  --start-index "$START_IDX" \
  --end-index "$END_IDX" \
  --log-dir "$JOBS_DIR" \
  --enable-logging 1 \
  > "$TB_SCRATCH/logs/${JOB_ID}_taubench.log" 2>&1

echo "Done."
#mkdir -p "jobs/${JOB_ID}/runs" "jobs/${JOB_ID}/trajectories"
cp "$TB_SCRATCH/logs/${JOB_ID}_taubench.log" "jobs/${JOB_ID}/runs/${JOB_ID}_taubench.log"
echo "Outputs:"
echo "  system_logs: ${JOB_ID}_smoketest.log, _smoketest.err, _taubench.log, _vllm_agent.log, _vllm_user.log"
echo "  jobs/${JOB_ID}/runs/: A_T*_R*.log, .trace.jsonl, .summary.json"
echo "  jobs/${JOB_ID}/trajectories/: *_{JOB_ID}.json"
