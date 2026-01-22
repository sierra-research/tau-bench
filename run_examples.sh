#!/bin/bash
# Tau-Bench Example Commands
# This script contains example commands for running benchmarks with different providers

# ============================================
# Environment Setup
# ============================================
# Activate the Tau1 conda environment first:
#   conda activate Tau1
#
# Make sure you have the required packages:
#   pip install -e .
#   pip install litellm python-dotenv

# Set the path to your .env file
ENV_FILE=".env"

echo "=== Tau-Bench Example Commands ==="
echo "Note: Default user model is now OpenRouter's openai/gpt-oss-20b"
echo ""

# ============================================
# OpenRouter Examples
# ============================================
echo "📡 OpenRouter Examples:"
echo ""

# OpenRouter with Qwen model (retail domain, single task for testing)
echo "1. OpenRouter - Qwen 3 8B (retail):"
echo "   python run.py --model openrouter/qwen/qwen3-8b --model-provider openrouter \\"
echo "     --env retail --task-ids 0 --env-file $ENV_FILE"
echo ""

# Uncomment to run:
# python run.py --model openrouter/qwen/qwen3-8b --model-provider openrouter \
#   --env retail --task-ids 0 --env-file "$ENV_FILE"

# ============================================
# DashScope (Alibaba) Examples
# ============================================
echo "🌏 DashScope (Alibaba) Examples:"
echo ""

# DashScope with Qwen model
echo "2. DashScope - Qwen 3 8B (retail):"
echo "   python run.py --model qwen3-8b --model-provider dashscope \\"
echo "     --env retail --task-ids 0 --env-file $ENV_FILE"
echo ""

# Uncomment to run:
# python run.py --model qwen3-8b --model-provider dashscope \
#   --env retail --task-ids 0 --env-file "$ENV_FILE"

# DashScope with Qwen Max (larger model)
echo "3. DashScope - Qwen Max (retail):"
echo "   python run.py --model qwen-max --model-provider dashscope \\"
echo "     --env retail --task-ids 0 --env-file $ENV_FILE"
echo ""

# ============================================
# Local Model Examples (OpenAI-Compatible API)
# ============================================
echo "🖥️  Local Model Examples:"
echo ""

# Local model with vLLM or similar
echo "4. Local Model (vLLM):"
echo "   python run.py --model qwen3-8b --model-provider local \\"
echo "     --model-base-url http://localhost:8000/v1 \\"
echo "     --env retail --task-ids 0 --env-file $ENV_FILE"
echo ""

# Uncomment to run:
# python run.py --model qwen3-8b --model-provider local \
#   --model-base-url http://localhost:8000/v1 \
#   --env retail --task-ids 0 --env-file "$ENV_FILE"

# ============================================
# Standard OpenAI/Anthropic Examples (with OpenRouter user)
# ============================================
echo "🔧 Standard Provider Examples:"
echo ""

echo "5. OpenAI GPT-4o (retail) with OpenRouter user:"
echo "   python run.py --model gpt-4o --model-provider openai \\"
echo "     --env retail --task-ids 0 --env-file $ENV_FILE"
echo ""

echo "6. Anthropic Claude (retail) with OpenRouter user:"
echo "   python run.py --model claude-3-5-sonnet-20241022 --model-provider anthropic \\"
echo "     --env retail --task-ids 0 --env-file $ENV_FILE"
echo ""

# ============================================
# Full Benchmark Run Examples
# ============================================
echo "📊 Full Benchmark Run Examples:"
echo ""

echo "7. Full retail benchmark with OpenRouter Qwen:"
echo "   python run.py --model openrouter/qwen/qwen3-8b --model-provider openrouter \\"
echo "     --env retail --max-concurrency 5 --env-file $ENV_FILE"
echo ""

echo "8. Full airline benchmark with DashScope Qwen:"
echo "   python run.py --model qwen3-8b --model-provider dashscope \\"
echo "     --env airline --max-concurrency 5 --env-file $ENV_FILE"
echo ""

# ============================================
# Quick Test Command (copy-paste ready)
# ============================================
echo "🚀 Quick Test Command (copy-paste ready):"
echo ""
echo "conda activate Tau1 && python run.py --model openrouter/qwen/qwen3-8b --model-provider openrouter --env retail --task-ids 0 --env-file \"$ENV_FILE\""
echo ""

echo "=== End of Examples ==="
