# τ-bench on ASU SOL — Setup Guide

This document describes how to set up and verify this repository on ASU’s SOL cluster.
All commands shown here are run manually by a user. Nothing in this file executes automatically.

---

## 1) One-time: install Miniconda (per user)

Run the following commands on the SOL login node:

```bash
cd ~
curl -L -o Miniconda3-latest-Linux-x86_64.sh \
  https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh


After installation, restart your shell.
If conda is not found, run:
source ~/miniconda3/etc/profile.d/conda.sh

2) Create the project environment
From the repository root directory:
conda env create -f environment.yml
conda activate taubench-py312
./scripts/verify_env.sh
The verification script should print:
the Python version
the active conda environment name
tau_bench import ok

3) Updating the environment (only if environment.yml changes)
If the environment specification is updated in the future, update your local environment with:
conda env update -n taubench-py312 -f environment.yml --prune
conda activate taubench-py312
pip install -e .
./scripts/verify_env.sh

4) Cluster etiquette
Use the login node for git operations and environment setup.
Use Slurm compute nodes for τ-bench runs, evaluations, and any GPU workloads.

Save the file. Do **not** run anything from it.

For vLLM-hosted models, use `--platform vllm-chat` and pass the full OpenAI-compatible endpoint via `--base-url` (e.g., http://localhost:8000/v1). τ-bench does not start vLLM servers; they must be running beforehand.
