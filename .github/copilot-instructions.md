# τ-bench — Copilot instructions for coding agents

Purpose: give a new AI coding agent short, actionable guidance so it can be immediately productive in this repo.

## Big picture (what to know first) 🔧
- τ-bench simulates conversations between a *user* (simulated by LLMs or human input) and an *agent* that can call domain-specific API tools. The main loop is in `run.py` → `tau_bench/run.py` → `agent.solve()` → `env.step()`.
- Major components:
  - `tau_bench/envs/*` — domain environments (airline, retail). Each Env binds a dataset, list of Tool classes, tasks, a `wiki` (system policy), and user-simulator.
  - `tau_bench/agents/*` — agent strategies (tool-calling, few-shot, react/act). Each strategy implements a different message format and decision loop.
  - `tau_bench/envs/*/tools/*` — concrete “API tools”. Each Tool class implements `invoke(...)` and `get_info()` (OpenAI-like function schema).
  - `tau_bench/model_utils/*` — model abstraction and utilities (sampling, routing, local/default models).
  - `run.py` — user-facing runner; passes `--model`, `--model-provider`, `--user-model`, `--agent-strategy`, etc.

## Quick workflows ✅
- Setup (developer):
  - Use the conda env in `environment.yml` (env name `taubench-py312`), or `pip install -e .` to install package dependencies.
- Run experiments (example):
  - `python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --user-model gpt-4o --user-model-provider openai --max-concurrency 10`
- Local vLLM servers (optional): helper scripts `start_vllm_user.sh` and `start_vllm_agent.sh` — read them for GPU/port conventions and model names.
- Error analysis: `python auto_error_identification.py --env <airline|retail> --results-path <file> --output-path <out.json>` uses the `model_utils` API for automated fault assignment and classification.

## Important code patterns & conventions 🧭
- Tools:
  - Implement static methods:
    - `invoke(data: Dict, **kwargs) -> str`: perform changes or queries and return a string (success commonly `json.dumps(...)`, errors are `"Error: ..."`).
    - `get_info() -> Dict`: returns a function-like schema used by the tool-calling agents. Example: `book_reservation.get_info()` (see `tau_bench/envs/airline/tools/book_reservation.py`).
  - Tools are listed in `ALL_TOOLS` and passed to an `Env` on init (see `tau_bench/envs/*/env.py`).
  - Tools that should terminate a task are listed on the Env as `terminate_tools` (e.g., `transfer_to_human_agents`).
- Agents / message formats:
  - `tool-calling` agents use `litellm.completion(..., tools=tools_info, ...)` and expect the response to include `tool_calls` that contain `function.arguments` (JSON string). See `ToolCallingAgent` and `FewShotToolCallingAgent` for exact parsing via `message_to_action`.
  - `act` / `react` (`ChatReActAgent`) uses an instruction + JSON action block in the content (Action JSON is parsed from the text). Follow the `REACT_INSTRUCTION` / `ACT_INSTRUCTION` templates strictly when constructing prompts.
  - `respond` action: Agents use a special action name `"respond"` (constant `RESPOND_ACTION_NAME`) with payload key `content` (`RESPOND_ACTION_FIELD_NAME`), which the environment routes to the user simulator.
- User simulation:
  - Implemented under `tau_bench/envs/user.py` with strategies: `human`, `llm`, `react`, `verify`, `reflection`. Use `load_user(...)` to construct.
  - LLM user simulators generate one-line messages and implement their own system prompts and verification loops (see `LLMUserSimulationEnv`, `ReactUserSimulationEnv`).
- Reward calculation:
  - `Env.calculate_reward()` checks two things: (1) DB changes vs. ground-truth actions (via consistent hashing) and (2) required textual outputs present in `actions` (checks `task.outputs`). Familiarize yourself with it if editing task or reward logic.

## When editing or adding features 💡
- Add a new Tool:
  1. Create `tau_bench/envs/<domain>/tools/<my_tool>.py` with `invoke` and `get_info`.
  2. Add the class to the tools package `__init__.py` and include it in `ALL_TOOLS`.
  3. If the tool should end a task, add its name to `terminate_tools` in the Env constructor.
- Add a new Env/domain:
  - Implement `load_data`, `WIKI`, `RULES`, `tasks_*` consistent with existing domains and register the Env in `tau_bench/envs/<domain>/env.py`.
- Add a new agent strategy:
  - Create agent class under `tau_bench/agents/` inheriting from `Agent` and implement `solve(env, task_index)` returning `SolveResult`.
  - Wire it in `tau_bench/run.py` in `agent_factory` and add a choice to CLI args in `run.py`.

## Integration notes, gotchas & examples ⚠️
- Model providers: valid providers come from `litellm.provider_list` (see `--model-provider` / `--user-model-provider`). Passing the wrong provider will assert at runtime.
- Tool outputs and errors are strings. Agents should handle `Error:` prefixes and not assume always-well-formed JSON unless explicitly documented by the tool.
- Function-calling vs custom JSON actions: both exist in this project — be careful to implement parsers for each agent style. Look at `message_to_action` and `ChatReActAgent.generate_next_step`.
- Checkpoints & logging: run writes per-trial incremental checkpoints into `--log-dir` (default `results`) named with a reproducible pattern (agent strategy, model, temperature, etc.).

## Helpful files to inspect when working here 📁
- Running & orchestration: `run.py`, `tau_bench/run.py`
- Agents: `tau_bench/agents/*.py` (especially `tool_calling_agent.py`, `chat_react_agent.py`, `few_shot_agent.py`)
- Environments & tools: `tau_bench/envs/*/env.py`, `tau_bench/envs/*/tools/*.py`
- User simulation: `tau_bench/envs/user.py`
- Reward & task structure: `tau_bench/envs/base.py`, `tau_bench/types.py`
- Model utilities & API wrapper: `tau_bench/model_utils/` and `auto_error_identification.py` (example usage)

---
If any section is unclear or you want examples for a specific change (e.g., add a tool or agent), I can add a short code snippet for that file and follow up. Please tell me what to improve or add. 📝