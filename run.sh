# --- GPT-4o Mini ---

# Airline all
python run.py --agent-strategy tool-calling --env retail \
--model gpt-4o --model-provider openai \
--user-model gpt-4o --user-model-provider openai \
--user-strategy llm --max-concurrency 20

# Retail all
# python run.py --agent-strategy tool-calling --env retail \
# --model gpt-4o-mini --model-provider openai \
# --user-model gpt-4o-mini --user-model-provider openai --user-strategy llm --max-concurrency 10

# --- Llama 4 Scout ---

# python run.py --agent-strategy react --env airline \
# --model meta-llama/Llama-4-Scout-17B-16E-Instruct --model-provider together_ai \
# --user-model gpt-4o --user-model-provider openai \
# --user-strategy llm --max-concurrency 10