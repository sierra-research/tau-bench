## TauBench Phase 3A — Orchestrated Tool-Calling Implementation Design

**Scope:** This document explains the concrete implementation of the Phase 3A orchestrated tool-calling agent in this repository. It is aimed at both newcomers to TauBench and experienced system engineers who need to understand how the orchestrated agent is wired into the existing benchmark, how control and data flow between modules, and how to extend the design.

Phase 3A implements an orchestration layer for the **tool-calling baseline** only, via `OrchestratedToolCallingAgent`. It uses a **single shared run loop** that adds validation, policy-guarding, grounding, and recovery on top of the existing `ToolCallingAgent`, while preserving compatibility with TauBench’s environment and metrics.

---

## 1. High-level architecture

### 1.1 Main participants

- **Environments (`tau_bench/envs`)**
  - `airline` and `retail` environments implement the task suites, tools, and user simulators.
  - Expose:
    - `Env.reset(task_index)` → initial observation and task metadata.
    - `Env.step(action: Action)` → `EnvResponse(observation, reward, done, info)`.
    - `tools_info` (OpenAPI-like tool schemas).
    - `tools_map` (name → callable tool).

- **Base agents (`tau_bench/agents`)**
  - `ToolCallingAgent`:
    - Knows how to call the model with `tools_info`.
    - Converts assistant tool-call messages into `Action` objects (`message_to_action`).
    - Baseline `solve()` loop: `reset → (completion → env.step → message append)*`.

- **Orchestrated wrapper (`OrchestratedToolCallingAgent`)**
  - Wraps a `ToolCallingAgent` instance.
  - Does **not** call `ToolCallingAgent.solve()`.
  - Instead, passes the inner agent as a **proposer** into the shared orchestrator loop:
    - `proposer.generate_next_step(messages) -> (next_message, action, cost)`.

- **Orchestration layer (`tau_bench/orchestration`)**
  - `run_loop.run_orchestrated_loop`: owns the **step loop** for orchestrated runs.
  - `task_state.TaskState`: per-run shared structured state for policy, grounding, recovery.
  - `validator.validate_action`: pre-execution action validator (schema, grounding sanity).
  - `policy_guard.check_policy`: policy and precondition guard using `TaskState`.
  - `grounding.apply_grounding` / `build_grounded_facts_summary`: extract and summarize facts from tool results.
  - `recovery.decide_recovery`: maps failures (validator/policy/tool errors) to strategies.
  - `message_utils.strip_think_tags` / `sanitize_user_observation`: clean model/user content.
  - `logging` + `logging_schemas`: structured run logging for Phase 3A.

- **Benchmark runner (`tau_bench/run.py`)**
  - Exposes `run(config: RunConfig)`.
  - Creates environments and agents.
  - For Phase 3A strategy `"orchestrated-tool-calling"`:
    - Creates **job-scoped log directory and job id**.
    - For each `(task_id, trial)`:
      - Creates a **run logger**.
      - Calls `agent.solve(env=isolated_env, task_index=idx, run_logger=..., domain=config.env)`.
  - Aggregates results, computes metrics, and writes trajectory checkpoints.

### 1.2 Architectural stance in Phase 3A

- **Orchestrator owns the step loop.**
  - Entry point remains `run(config) → agent.solve(env, task_index)`.
  - For Phase 3A, `OrchestratedToolCallingAgent.solve()` calls `run_orchestrated_loop`, which:
    - Calls `env.reset()`.
    - Repeatedly calls the **proposer** (inner `ToolCallingAgent.generate_next_step`).
    - Performs validation, policy guard, grounding, recovery, and logging.
    - Calls `env.step()` only after an action passes validation + policy.

- **Base agent is an action proposer.**
  - `ToolCallingAgent` exposes:
    - `generate_next_step(messages) -> (next_message, Action, cost)`.
  - This is the only place where the LLM is called for the **assistant** turn in Phase 3A.

- **Single shared orchestration path (Phase 3A subset).**
  - The run loop is written to be reusable across future orchestrated ACT/ReAct agents.
  - In Phase 3A, only the tool-calling variant is wired in.

- **Ablation-friendly design.**
  - Even though only some modules are enabled in Phase 3A, they are designed to be **individually disable-able** in the future:
    - Validator.
    - Policy guard.
    - Grounding.
    - Recovery.
    - Logging granularity.

---

## 2. Control-flow overview

### 2.1 End-to-end execution flow (Phase 3A)

At a high level, **one orchestrated run** proceeds as:

1. `tau_bench.run.run(config)`
   - Validates `RunConfig`.
   - Computes checkpoint path.
   - Loads an environment via `get_env(config.env, ...)`.
   - Creates an agent via `agent_factory(...)`.

2. `agent_factory(..., agent_strategy="orchestrated-tool-calling")`
   - Returns an `OrchestratedToolCallingAgent` instance wrapping a `ToolCallingAgent`.

3. For each `trial` and each `task_id`:
   - `run()` instantiates an **isolated environment** for that task.
   - If strategy is `"orchestrated-tool-calling"`:
     - Creates a **run logger**.
     - Calls `agent.solve(env=isolated_env, task_index=task_id, run_logger=run_logger, domain=config.env)`.

4. `OrchestratedToolCallingAgent.solve(...)`
   - Ensures a logger (real or no-op).
   - Delegates to orchestration:
     - `run_orchestrated_loop(env, proposer=self._agent, run_logger=run_logger, task_index, max_num_steps, domain=config.env)`.

5. `run_orchestrated_loop(...)`
   - Creates and owns:
     - `TaskState` (via `create_initial_task_state`).
     - `RecoveryState`.
     - Local LLM **messages** list.
     - Reward, cost, and counters.
   - Runs the **main loop**:
     1. Writes a state snapshot trace event.
     2. Applies confirmation heuristics for previously pending side-effects.
     3. Builds and injects a **grounded facts summary** message.
     4. Calls the **proposer** (`ToolCallingAgent.generate_next_step`).
     5. Validates the candidate action via `validator.validate_action`.
     6. If invalid:
        - Logs validation failure.
        - Asks the recovery module for a decision.
        - Either **terminates safely** or injects an orchestrator rejection message into `messages` and continues.
     7. If valid:
        - Runs `policy_guard.check_policy`.
        - If blocked:
          - Invokes recovery (e.g., ask user for confirmation or replan).
          - Injects a rejection message; may terminate if recovery decides so.
     8. If policy allows:
        - Executes the action via `env.step(action)`.
        - Updates `TaskState` from the tool outcome.
        - Optionally applies grounding to capture persistent facts.
        - Appends assistant + tool/user messages to `messages` (tool-call vs respond branch).
        - Logs executor results.
     9. Checks termination:
        - If `env_response.done`:
          - Calls `run_logger.finish_run(exit_reason="success", ...)`.
          - Returns a `SolveResult`.
        - Else, loop continues until `max_num_steps`.
   - If the loop exhausts `max_num_steps`:
     - Calls `finish_run(exit_reason="budget_exhausted", ...)`.
     - Returns a `SolveResult`.
   - If any unhandled exception escapes:
     - Calls `finish_run(exit_reason="error", ...)`.
     - Reraises.

6. `run()` wraps returned `SolveResult` into `EnvRunResult`, persists trajectories to the checkpoint file, and finally prints metrics.

---

## 3. Module-by-module design

This section walks through the main Phase 3A modules and explains their responsibilities and how they interact at runtime.

### 3.1 Orchestrated tool-calling agent (`OrchestratedToolCallingAgent`)

- **Location:** `tau_bench/agents/orchestrated_tool_calling_agent.py`
- **Responsibility:** Adapter between TauBench’s `Agent` interface and the shared orchestrator loop.
- **Key behavior:**
  - On construction:
    - Instantiates a `ToolCallingAgent` with tools, wiki, model, provider, and temperature.
  - On `solve(env, task_index, max_num_steps, **kwargs)`:
    - Acquires `run_logger` from `kwargs` or uses `NoOpRunLogger`.
    - Requires `domain` in `kwargs` (e.g., `"airline"` or `"retail"`).
    - Calls `run_orchestrated_loop`:
      - `proposer=self._agent` (the inner `ToolCallingAgent`).
      - Passes env, logger, domain, and task index.
- **Notes for engineers:**
  - The inner agent is treated as **pure LLM + tool-call proposer**; it does not see the environment directly in this mode.

### 3.2 Shared task state (`TaskState`)

- **Location:** `tau_bench/orchestration/task_state.py`
- **Responsibility:** A **structured, domain-aware state object** that captures everything the orchestrator needs to make policy and recovery decisions.
- **Key fields:**
  - `domain`: `"airline"` or `"retail"`.
  - `intent`: `IntentState` (task kind, objective, instruction; future hook for planner).
  - `identity`: `IdentityState` (user id, authentication, profile-grounded).
  - `grounded`: dictionary of reusable facts derived from tool results, e.g.:
    - `user_id`, `user_profile`.
    - `known_payment_method_ids`.
    - `reservation_ids`, `reservation_details`.
    - `order_ids`, `order_details`.
  - `confirmations`: set of confirmation keys (e.g. `"booking_confirmed"`).
  - `domain_state`: domain-specific substate, including:
    - For airline: `reservation_id`, `booking_flow_stage`, `policy_counters`.
    - For retail: `order_id`, `auth_method_used`, `user_id_from_lookup`, `policy_counters`.
- **Construction:**
  - `create_initial_task_state(domain, task, initial_observation)`:
    - Captures the initial task instruction.
    - Initializes default domain state.
    - Does **not** assume any prior grounding or authentication.
- **Lifecycle:**
  - Created at run start and passed to:
    - `policy_guard` (preconditions and business rules).
    - `grounding` (to update grounded facts).
    - `recovery` (for richer decisions).

### 3.3 Grounding layer (`grounding.py`)

- **Responsibility:** Convert **raw tool observations** into persistent, structured state in `TaskState`.
- **Key concepts:**
  - A registry mapping `(domain, tool_name)` to a **result type**:
    - `RESULT_TYPE_USER_PROFILE` → user profile JSON (e.g., `get_user_details`).
    - `RESULT_TYPE_USER_ID_LOOKUP` → user id lookup (e.g., `find_user_id_by_email`).
    - `RESULT_TYPE_RESERVATION_DETAILS` → airline reservation JSON.
    - `RESULT_TYPE_ORDER_DETAILS` → retail order JSON.
  - Extractors for each result type:
    - Parse JSON where applicable.
    - Update:
      - `grounded["user_id"]`, `grounded["user_profile"]`, `grounded["known_payment_method_ids"]`.
      - `grounded["reservation_ids"]`, `grounded["reservation_details"]`.
      - `grounded["order_ids"]`, `grounded["order_details"]`.
      - `identity` and `domain_state` fields (authentication method, focused reservation/order id).
- **Main entrypoint:**
  - `apply_grounding(env, domain, action, observation, task_state)`:
    - Skips empty or error observations (`"Error: ..."`) and non-env tools.
    - Looks up a result type from the registry.
    - Applies the corresponding extractor.
  - `build_grounded_facts_summary(task_state)`:
    - Generates a **short textual summary** of what is known so far, e.g.:
      - Whether a user id is known.
      - Whether the profile is grounded.
      - Which payment IDs, reservation IDs, or order IDs are known.
    - This summary is injected into the LLM context once per step as an orchestrator-sourced `user` message.

### 3.4 Validator (`validator.py`)

- **Responsibility:** **Pre-execution guard** to reject clearly invalid or under-specified actions before calling `env.step`.
- **Core checks (`validate_action(env, action, step_index)`):**
  1. **Respond action handling**:
     - If `action.name == RESPOND_ACTION_NAME`:
       - Require `kwargs` to be a dict with string `content`.
       - Returns `ValidatorResult(allowed=True, code="respond")` on success.
  2. **Tool existence**:
     - Ensure `action.name` is in `env.tools_map`.
     - If unknown, returns code `"tool_not_found"`.
  3. **Argument schema**:
     - Fetch the tool’s JSON schema from `env.tools_info`.
     - Enforce:
       - Presence of required arguments.
       - Basic type consistency (string/number/integer/boolean/array/object).
     - Returns code `"schema_mismatch"` on failure.
  4. **Grounding sanity**:
     - Ensure required string arguments are not empty/whitespace-only.
     - Returns code `"grounding_fail"` on failure.
- **Output:**
  - `ValidatorResult(allowed, code, message)` for logging and recovery.
- **Usage in run loop:**
  - If `allowed=False`:
    - Increments `num_validation_failures`.
    - Calls `decide_recovery` with `FAILURE_VALIDATION_ERROR`.
    - Injects a synthetic rejection message into the message stream and **skips** `env.step`.

### 3.5 Policy guard (`policy_guard.py`)

- **Responsibility:** Enforce **domain-specific business and safety rules** that go beyond schema-level validation.
- **Role in the system:** Conceptually acts as the **policy brain** for the orchestrated agent: it is the single place where domain policies, prerequisites, and business rules are interpreted and enforced at runtime.
- **Inputs:**
  - `Env` (access to underlying data when needed).
  - `Action` (tool name and kwargs).
  - `TaskState` (identity, grounded facts, domain_state).
- **Metadata-driven configuration:**
  - A central `POLICY_METADATA` mapping `(domain, tool_name)` to:
    - Required preconditions (e.g., `REQUIRES_USER_ID`, `REQUIRES_AUTHENTICATED`, `REQUIRES_RESERVATION_CONTEXT`, `REQUIRES_CONFIRMATION_KEY`).
    - A set of **business rules** with ids and parameters:
      - `max_passengers`, `payment_limits`, `payment_methods_in_profile`.
      - `order_status_required`, `max_successful_executions_per_tool`, `payment_method_allowed`, `refund_method_allowed`.
      - `flight_must_be_available`, etc.
- **Main entrypoint:**
  - `check_policy(env, action, task_state) -> PolicyGuardResult`.
    - For `respond`, always allows.
    - If no metadata is configured, allows.
    - Enforces preconditions using `TaskState`, for example:
      - User must be authenticated before mutating retail orders.
      - A reservation id or order id must be grounded before certain operations.
      - A specific confirmation key must be present in `task_state.confirmations` before side-effecting actions.
    - After preconditions pass, evaluates business rules via a **pluggable registry**.
    - Returns a `PolicyGuardResult` indicating:
      - `allowed` (boolean).
      - Machine-readable `code` (for recovery).
      - Human-readable `message`.
      - Any `missing_prerequisites`.
      - Non-blocking `warnings` from rules with severity `"warn"`.
- **Usage in run loop:**
  - If `allowed=False`:
    - Constructs `RecoveryInput(FAILURE_POLICY_BLOCK, policy_result, ...)`.
    - `decide_recovery` may:
      - Ask user confirmation for tools that require it.
      - Recommend replanning from state.
    - The loop then injects a policy rejection message and either continues or terminates depending on the recovery strategy.
  - Because policy metadata is centralized in `POLICY_METADATA` and evaluated against grounded state in `TaskState`, the module can be naturally extended to read **versioned policy configurations** (e.g., from a policy catalog or config store) so that when the underlying business policy changes, the policy guard can be refreshed without redesigning the orchestrator.

### 3.6 Recovery (`recovery.py`)

- **Responsibility:** Provide a **central strategy engine** to handle failures consistently across modules:
  - Validation errors.
  - Policy blocks (including missing confirmation).
  - Tool execution errors (`"Error: ..."` observations).
  - No-progress and repeated-action patterns (hooks in place, partially used in Phase 3A).
- **Key types:**
  - `RecoveryState`:
    - Tracks:
      - Pending side-effect actions that are waiting for confirmation.
      - Retry counts for specific actions.
      - Per-failure-type counts.
      - Number of recovery invocations in this run.
      - One-shot confirmation usage after success.
  - `RecoveryInput`:
    - Failure type (`validation_error`, `policy_block`, `tool_execution_error`, etc.).
    - The `Action` that failed.
    - Step index, `TaskState`, `RecoveryState`.
    - Optional validator or policy results, observation text, and recent actions.
  - `RecoveryDecision`:
    - What strategy to apply:
      - `RETRY_SAME_ACTION`, `RETRY_REPAIRED_ACTION`, `ASK_USER_CONFIRMATION`, `ASK_CLARIFYING_QUESTION`, `REPLAN_FROM_STATE`, or `SAFE_TERMINATE`.
    - Optional message to user, repaired action, or replanning hint.
    - State updates to apply (e.g., mark an action as pending confirmation).
    - Retry keys and budget usage.
    - A terminal reason when the episode should end.
- **Main decision function:**
  - `decide_recovery(inp, domain, max_recovery_per_run=10, max_retries_per_action=2) -> RecoveryDecision`.
  - Core behaviors:
    - Enforces **global recovery budget** (`max_recovery_per_run`).
    - Tracks per-action retry counts; can terminate after too many retries.
    - Detects no-progress loops (same action repeated).
    - For validation and policy failures:
      - Usually returns `REPLAN_FROM_STATE` with a hint.
      - For missing confirmation cases:
        - Returns `ASK_USER_CONFIRMATION`.
        - Attaches `state_updates` that mark `pending_side_effect_action` and `pending_confirmation_key` in `RecoveryState`.
    - For tool errors:
      - Returns `REPLAN_FROM_STATE` with an observation preview.
- **Usage in run loop:**
  - After a failure:
    - The loop invokes `decide_recovery`.
    - Logs the decision as a `recovery` event.
    - Applies `state_updates` (e.g., track pending confirmation).
    - If `SAFE_TERMINATE`, calls `finish_run("recovery_terminated", ...)` and returns a partial `SolveResult`.

### 3.7 Run loop (`run_loop.py`)

- **Responsibility:** Implement the **minimal orchestrator loop** for Phase 3A:
  - Integrate validator, policy guard, grounding, recovery, logging, and message hygiene.
- **Key steps in `run_orchestrated_loop(...)`:**
  1. **Initialization:**
     - Calls `env.reset(task_index)` to get the initial observation and info.
     - Builds initial `messages`:
       - System message with `env.wiki`.
       - User message with the initial observation.
     - Creates a `TaskState` for the given domain using `env.task`.
     - Creates an empty `RecoveryState`.
     - Calls `run_logger.log_run_start()` and emits an initial trace event.
  2. **Per-step loop (1..max_num_steps):**
     - Emits a lightweight state snapshot trace event.
     - Handles pending confirmations by scanning the last user message and applying a small text heuristic.
     - Builds a grounded facts summary and injects it as a single orchestrator-generated `user` message.
     - Calls `proposer.generate_next_step(messages)`:
       - The proposer is the inner `ToolCallingAgent`.
       - The loop normalizes:
         - Ensures `next_message.role == "assistant"`.
         - Strips `<think>...</think>` blocks from assistant content.
     - Logs a `proposer` stage (including action name and cost).
     - Runs `validate_action`:
       - Logs `validator` stage.
       - If disallowed:
         - Increments validation counters.
         - Calls `decide_recovery`.
         - Logs `recovery` decision.
         - Injects a **rejection** message into the conversation:
           - For tools: as a synthetic `tool` message paired with the assistant tool call.
           - For respond: as an orchestrator-sourced user message.
         - Records the step and continues to the next iteration.
     - Runs `check_policy`:
       - Logs `policy_guard` stage.
       - If disallowed:
         - Calls `decide_recovery` with `FAILURE_POLICY_BLOCK`.
         - For missing confirmation:
           - Marks the side-effect action and confirmation key as pending.
         - Injects a policy rejection message, similar to validation.
         - May terminate via `SAFE_TERMINATE` or continue.
     - Calls `env.step(action)`:
       - Logs `executor` stage in both `.log` and `.trace`.
       - Updates reward, total cost, info dict, and observation summary.
       - Updates `TaskState` with last tool result or error.
       - Applies grounding (non-respond actions only).
       - Maintains policy counters (e.g., successful tool counts).
       - For tool failures (`"Error: ..."`), calls recovery again for error-specific handling and may terminate.
     - Appends messages to `messages`:
       - For tool actions:
         - Truncates `tool_calls` to a single entry.
         - Appends assistant message and corresponding `tool` message with the observation.
       - For respond actions:
         - Sanitizes user observations before appending a new role=`user` message.
         - When a debug flag is set, emits extra trace events for the respond path.
     - Updates loop-local tracking:
       - `last_action`, `last_observation_summary`, `recent_action_names`, `steps`.
     - If `env_response.done`:
       - Calls `finish_run(exit_reason="success", ...)`.
       - Returns a `SolveResult`.
  3. **Exit conditions:**
     - If the step budget is exhausted:
       - Calls `finish_run(exit_reason="budget_exhausted", ...)`.
       - Returns `SolveResult` with the last reward and messages.
     - If any exception bubbles up:
       - Calls `finish_run(exit_reason="error", ...)` with partial counters.
       - Reraises for the caller (which wraps into an `EnvRunResult` with error info).

### 3.8 Message utilities (`message_utils.py`)

- **Responsibility:** Keep model messages and user observations **clean and safe** to store.
- **Functions:**
  - `strip_think_tags(content: str) -> str`:
    - Removes `<think>...</think>` blocks using a depth-aware parser.
    - Ensures that intermediate chain-of-thought is not persisted into the long-term trajectory.
  - `sanitize_user_observation(content: str) -> str`:
    - Applies `strip_think_tags` and trims whitespace.
    - Used before appending user messages that come from the user simulator.

### 3.9 Logging (`logging.py`, `logging_schemas.py`)

- **Responsibility:** Provide a **consistent logging and tracing story** for Phase 3A runs.
- **Artifacts per run (under `log_dir/<job_id>/runs`)**
  - `<run_id>.log` — human-readable sequential log.
  - `<run_id>.trace.jsonl` — machine-readable trace events.
  - `<run_id>.summary.json` — run-level summary.
- **Run id and job id:**
  - `job_id_new()` — generates a new job id (e.g. timestamp).
  - `run_id_from(domain, task_id, trial)` — `A_T32_R3` or `R_T4_R1`.
- **Logger types:**
  - `OrchestrationRunLogger`:
    - Opened with log paths based on `log_dir`, `job_id`, and `run_id`.
    - Methods:
      - `log_run_start(metadata)` — START header.
      - `log_step_stage(step_index, stage, payload)` — per-stage blocks.
      - `write_trace_event(event)` — one JSON event per line.
      - `finish_run(exit_reason, steps, total_cost, reward, done, counters)`:
        - Writes RUN END block.
        - Emits a final `"final"` trace event.
        - Writes summary JSON (including ablations/config signatures when present).
        - Closes files.
  - `NoOpRunLogger`:
    - Same interface, but all methods are no-ops (used when logging is disabled).
  - `create_run_logger(log_dir, job_id, run_id, metadata, enabled)`:
    - Factory that returns either a real logger or a no-op instance.
- **Schemas:**
  - `RunMetadata`, `TraceEvent`, `SummaryPayload`, `StagePayload` are all simple `Dict[str, Any]`, defined in `logging_schemas.py`.
- **Usage in run loop:**
  - `run_orchestrated_loop` is the sole writer:
    - It never exposes the logger to domain modules (validator/policy/grounding).
    - All logging calls originate at orchestrator hook points.

### 3.10 Benchmark runner integration (`tau_bench/run.py`)

- **Agent strategy selection:**
  - `agent_factory` returns:
    - `ToolCallingAgent`, `ChatReActAgent`, `FewShotToolCallingAgent`, or `OrchestratedToolCallingAgent`.
  - Phase 3A adds `"orchestrated-tool-calling"` as a new strategy.
- **Job and run-scoped logging:**
  - For `"orchestrated-tool-calling"`:
    - `phase3_job_id` is created (from SLURM or `job_id_new()`).
    - Each run uses:
      - `run_id = run_id_from(config.env, task_id, trial)`.
      - `create_run_logger(config.log_dir, phase3_job_id, run_id, metadata, enabled=config.enable_logging)`.
    - That logger is passed into `agent.solve` via `solve_kwargs["run_logger"]`.
- **Trajectory persistence:**
  - Regardless of strategy, `run()` writes combined trajectories to a checkpoint JSON file under:
    - For Phase 3A: `log_dir/<job_id>/trajectories/...`.
    - For baseline runs: a flat path under `log_dir`.

---

## 4. Execution flow charts

### 4.1 End-to-end run (from `run(config)` to `SolveResult`)

```text
                      +---------------------------+
                      | tau_bench.run.run(config)|
                      +------------+--------------+
                                   |
                                   v
                   +-------------------------------+
                   | Validate config, build env    |
                   |   env = get_env(...)         |
                   +-------------------------------+
                                   |
                                   v
                      +------------------------+
                      | agent_factory(...)     |
                      |  - strategy switch     |
                      +-----------+------------+
                                  |
                                  v
           +-------------------------------------------+
           | OrchestratedToolCallingAgent (Phase 3A)  |
           +-------------------+-----------------------+
                               |
                               v
         +----------------------------------------------+
         | For each trial and task_id:                 |
         |  - build isolated_env                       |
         |  - create run_logger (Phase 3A only)        |
         |  - call agent.solve(env=isolated_env, ...)  |
         +-------------------+-------------------------+
                             |
                             v
        +-----------------------------------------------+
        | OrchestratedToolCallingAgent.solve           |
        |  - ensure run_logger                         |
        |  - call run_orchestrated_loop(...)           |
        +--------------------+-------------------------+
                             |
                             v
        +-----------------------------------------------+
        | run_orchestrated_loop                        |
        |  - env.reset                                 |
        |  - create TaskState & RecoveryState          |
        |  - main loop (proposer → validator →         |
        |    policy_guard → executor → grounding       |
        |    → message append → termination)           |
        +--------------------+-------------------------+
                             |
                             v
                +-----------------------------+
                | SolveResult (reward, info,  |
                |  messages, total_cost)      |
                +-------------+---------------+
                              |
                              v
         +---------------------------------------------+
         | Wrap in EnvRunResult, append to results,   |
         | update checkpoints and metrics, return.    |
         +---------------------------------------------+
```

### 4.2 Per-step orchestration flow (Phase 3A)

```text
  +-------------------------------------------------------------+
  |             run_orchestrated_loop main loop                 |
  +-------------------------------------------------------------+
  | Input: env, proposer, TaskState, RecoveryState, run_logger  |
  +-------------------------------------------------------------+
                             |
                             v
        [1] Emit state snapshot trace (last_action, obs, cost, len(messages))
                             |
                             v
        [2] Handle pending confirmation (if any) via text heuristic
            - If last user message affirms, add confirmation to TaskState
            - Clear pending side-effect from RecoveryState
                             |
                             v
        [3] Build grounded facts summary from TaskState
            - Remove older summary message (if any)
            - Append fresh orchestrator "Grounded facts: ..." user message
                             |
                             v
        [4] Proposer call: ToolCallingAgent.generate_next_step(messages)
            - Get next_message, Action, cost
            - Normalize next_message.role = "assistant"
            - Strip <think>...</think> from next_message.content
            - Accumulate total_cost
            - Log proposer stage + trace
                             |
                             v
        [5] Validator: validate_action(env, action)
            - If allowed: continue
            - If not allowed:
                - Increment validation failure counters
                - Build RecoveryInput(FAILURE_VALIDATION_ERROR, ...)
                - Call decide_recovery(...)
                - Log recovery decision
                - Append rejection message into messages:
                    - Tool case: assistant tool-call + tool role with "Validation failed: ...".
                    - Respond case: assistant + orchestrator user message.
                - Update last_action, last_observation_summary, recent_action_names
                - continue (next loop iteration)
                             |
                             v
        [6] Policy Guard: check_policy(env, action, TaskState)
            - If allowed: continue
            - If not allowed:
                - Build RecoveryInput(FAILURE_POLICY_BLOCK, ...)
                - Call decide_recovery(...)
                - If strategy is ASK_USER_CONFIRMATION:
                    - Update RecoveryState pending_side_effect_action and pending_confirmation_key
                - Append "Policy blocked: ..." rejection via tool or user message
                - Update last_action, last_observation_summary, recent_action_names
                - If strategy is SAFE_TERMINATE:
                    - finish_run(exit_reason="recovery_terminated", ...)
                    - return SolveResult
                - else:
                    - continue (next loop iteration)
                             |
                             v
        [7] Executor: env.step(action)
            - Receive observation, reward, done, info
            - Log executor stage + trace
            - Update TaskState.update_after_step(action_name, observation)
            - If action is a tool:
                - apply_grounding(...) to update TaskState.grounded and domain_state
                - update policy counters (tool_success_count)
                - if observation starts with "Error:":
                    - call decide_recovery(FAILURE_TOOL_EXECUTION_ERROR, ...)
                    - log recovery decision
                    - possibly SAFE_TERMINATE early
            - Update last_action, last_observation_summary, recent_action_names
                             |
                             v
        [8] Message append:
            - Tool action:
                - Truncate next_message.tool_calls to a single call
                - Append assistant message + tool role message with observation
            - Respond action:
                - Sanitize user observation via sanitize_user_observation
                - Append assistant message + user message with sanitized text
                             |
                             v
        [9] Check termination:
            - If done:
                - finish_run(exit_reason="success", steps, total_cost, reward, done=True, counters)
                - return SolveResult
            - Else:
                - Continue loop (back to [1]) until max_num_steps
```

---

## 5. Data and message shapes

### 5.1 Messages passed to the proposer

- **Initial messages:**
  - System: `{"role": "system", "content": env.wiki}`.
  - User: initial observation string from `env.reset(...)`.
- **Per-step augmentation:**
  - At the top of each step, the orchestrator appends:
    - `{"role": "user", "content": "Grounded facts: ...", "source": "orchestrator"}`.
  - Over time, the message list interleaves:
    - Assistant tool calls and respond messages.
    - Tool messages (tool output).
    - User messages from the user simulator.
    - Orchestrator-injected user messages with state summaries or rejections.

### 5.2 Action objects

- **Type:** `tau_bench.types.Action`.
- **Generated by:** `ToolCallingAgent.message_to_action(...)`.
- **Main variants:**
  - **Tool action:**
    - `Action(name="<tool_name>", kwargs=<dict parsed from tool_calls[0].function.arguments>)`.
  - **Respond action:**
    - `Action(name=RESPOND_ACTION_NAME, kwargs={"content": <assistant message content>})`.

---

## 6. Extensibility and future directions (beyond Phase 3A)

Phase 3A intentionally implements a **minimal but structured** orchestrator for a single baseline (tool-calling). The design is meant to be extended in several directions:

- **Module-level extensibility**
  - All current orchestration modules (`TaskState`, validator, policy guard, grounding, recovery, run loop, logging, and the orchestrated agent wrapper) are implemented as **minimal v1s**: they focus on the most important behavior needed for Phase 3A and are structured so that their internals can be elaborated (richer state, rules, heuristics) without changing their public contracts or how `run_orchestrated_loop` is wired.

- **Orchestrated ReAct / ACT agents**
  - Wrap `ChatReActAgent` (with and without reasoning) in orchestrated adapters analogous to `OrchestratedToolCallingAgent`.
  - Reuse:
    - The same `TaskState`, `validator`, `policy_guard`, `grounding`, `recovery`, and `logging`.
    - A unified `run_orchestrated_loop`, with per-agent adapters for:
      - Proposer (`generate_next_step` invocation).
      - Message append semantics (how observations are turned into the next user message).

- **Planner and decomposition module**
  - Introduce an explicit planner that:
    - Uses LLM calls to decompose the task into checkpoints or subgoals.
    - Stores plan state in `TaskState.progress` and `TaskState.checklist`.
  - Integrate planner calls between:
    - Grounding/intent extraction.
    - Proposer calls, so that `generate_next_step` benefits from more structured context.

- **Policy evolution**
  - Extend the policy guard “policy brain” so that:
    - Policy metadata (`POLICY_METADATA`) can be sourced from a versioned policy definition (e.g., YAML/JSON files or a policy service).
    - New policies or updated business rules can be rolled out by updating the policy source, with the orchestrator automatically picking up the new configuration on restart (or via a refresh hook), instead of hard-coding logic into the run loop.

- **Memory and context management**
  - Add a dedicated **memory manager** module that:
    - Compresses long histories while preserving tool outputs and key user constraints.
    - Returns agent-specific message lists that still respect each baseline’s expected schema.
  - Interpose memory management either:
    - Before each proposer call (to build `messages_for_proposer`).
    - After each step (to update summaries and pinned facts).

- **Tool master and dynamic tool catalogs**
  - Today, tools are discovered from `env.tools_info` / `env.tools_map`, and the orchestrated agent assumes the **TauBench tool set is relatively static** for a given environment.
  - The same interface can be extended into a “tool master” layer that:
    - Periodically or on demand scans for new tool definitions (e.g., new Python tool modules or externally registered tools).
    - Updates the master list of tools exposed through `tools_info` / `tools_map` so that new tools automatically become available to the agent without changing orchestrator code.
  - Because tool definitions do not change very often in the current benchmark, Phase 3A limits itself to the tools already provided by TauBench, but the orchestration boundaries are compatible with a more dynamic tool catalog.

- **Escalation gate and human handoff**
  - Introduce an **escalation gate** module:
    - Recognizes escalation tools (e.g., `transfer_to_human_agents`).
    - Applies policy and heuristics before allowing escalations to execute.
  - Use the same recovery infrastructure to:
    - Ask the user for confirmation before escalation.
    - Provide alternate fallback strategies (e.g., additional clarifying questions).

- **Richer orchestrated React-style agent**
  - Implement a higher-level orchestrated agent that:
    - Chooses between:
      - Tool calls.
      - Direct respond actions.
      - Asking for clarification.
      - Triggering planner, memory refresh, or escalation.
    - Uses `TaskState` as a shared memory between multiple LLM calls (action proposer, planner, recovery).

---

## 7. Summary

Phase 3A adds an **orchestrated tool-calling agent** that cleanly separates roles:

- The **base agent** (`ToolCallingAgent`) remains responsible only for **proposing** the next assistant message and tool action.
- The **orchestrator** (`run_orchestrated_loop`) owns:
  - The environment interaction loop.
  - Validation, policy checking, grounding, and recovery.
  - Structured logging and tracing.
- The **TaskState** and related orchestration modules provide a **shared stateful backbone** that will support:
  - Orchestrated ReAct/ACT agents.
  - Planner, memory, escalation gate, and richer multi-agent orchestration in future phases.

This separation of concerns allows Phase 3A to remain backward-compatible with the TauBench benchmark API while enabling iterative extensions toward a full orchestrated agent stack.

