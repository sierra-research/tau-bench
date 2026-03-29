# TauBench Phase 3 (taubench_phase3_v1) — Implementation Plan

**Goal:** Build a shared orchestration layer wrapped around existing baseline strategies (OrchestratedActAgent, OrchestratedReActAgent, OrchestratedToolCallingAgent). Base agents remain action proposers; orchestration owns the loop. Ablation-friendly; baseline comparability preserved.

---

## A. Architectural stance

- **Orchestrator owns the loop.** Entry point remains `agent.solve(env, task_index)`; for Phase 3, the agent is an orchestrated wrapper that runs its own step loop and never calls `inner_agent.solve()`.
- **Base agents are action proposers.** Each baseline exposes a step-level API: given `messages`, return a candidate `(message, Action, cost)`. The orchestrator calls this once per step, then runs validation, policy, execution, and recovery. Baseline `solve()` is not invoked by the orchestrator.
- **Single shared orchestration code path.** ACT, ReAct, and Tool-Calling differ only in which proposer is called (and in message-append semantics after execution). All other modules (validator, policy guard, executor, recovery, memory, escalation gate) are shared and receive a normalized `Action`.
- **Structural adaptation allowed.** Refactors to the current codebase are acceptable (e.g., extracting `generate_next_step` from ToolCallingAgent) so long as baseline behavior is preserved when the same agent is run without orchestration.
- **Ablations via configuration.** Each orchestration module is gated by a config flag (e.g., `use_validator`, `use_memory_manager`). Disabling a module skips it without changing control flow for others.
- **Benchmark protocol unchanged.** Same `Env`, `env.reset()`, `env.step()`, `SolveResult`, `EnvRunResult`, pass^k, and checkpoint format. Orchestrated runs use a distinct `agent_strategy` (e.g., `orchestrated-act`, `orchestrated-react`, `orchestrated-tool-calling`) so results remain comparable and distinguishable.

---

## B. Required refactors in current codebase

### B.1 ToolCallingAgent — expose step-level boundary

**File:** `tau_bench/agents/tool_calling_agent.py`

**Current:** The loop in `solve()` (lines 39–72) inlines: `completion(...)` → `message_to_action(next_message)` → `env.step(action)` → message extend. There is no method that takes `messages` and returns a candidate action without executing.

**Required:** Add a method with the same contract as `ChatReActAgent.generate_next_step`:

- **Signature:** `generate_next_step(self, messages: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Action, float]`
- **Behavior:** Call `completion(messages=messages, tools=self.tools_info, ...)`; get `next_message = res.choices[0].message.model_dump()`; compute `action = message_to_action(next_message)` and `cost = res._hidden_params.get("response_cost") or 0`; return `(next_message, action, cost)`.
- **No mutation of `messages`** inside this method.
- **Preserve existing `solve()`:** Refactor `solve()` so that inside the loop it calls `generate_next_step(messages)` then performs `env.step(action)` and the existing message-extend logic (tool vs user branch). Behavior and outputs (reward, info, messages, total_cost) must remain identical to current implementation.

**Risk:** `message_to_action` can raise if `tool_calls[0]["function"]["arguments"]` is invalid JSON. Current `solve()` has the same risk. No new behavior.

### B.2 FewShotToolCallingAgent — same step-level boundary

**File:** `tau_bench/agents/few_shot_agent.py`

**Required:** Add `generate_next_step(self, messages) -> Tuple[Dict[str, Any], Action, float]` with the same semantics as ToolCallingAgent, using `self.wiki` and `self.few_shot_displays` for system content (already in `messages` built in `solve()`). Refactor `solve()` to use it inside the loop so that behavior is unchanged.

**Note:** Phase 3 wrapped agents in scope are ACT, ReAct, Tool-Calling only. Few-shot is not a required wrapped target; the refactor is for consistency and future use.

### B.3 ChatReActAgent — no signature change; optional append abstraction

**File:** `tau_bench/agents/chat_react_agent.py`

**Current:** Already has `generate_next_step(messages) -> (message, action, cost)`. Solve loop (lines 72–84) extends messages with `[message, {"role": "user", "content": obs}]` and prefixes tool obs with `"API output: "`.

**Required:** No change to public API. Optionally add a method `append_step_to_messages(self, messages, message, action, observation)` that encapsulates the extend logic (and the "API output: " prefix for non-respond actions) so the orchestrator can call it without duplicating agent-specific logic. If not added, the orchestrator will need agent-specific branch for "how to append after step" (see D).

### B.4 Base Agent interface — optional protocol for "action proposer"

**File:** `tau_bench/agents/base.py`

**Current:** Only abstract method is `solve(env, task_index, max_num_steps) -> SolveResult`.

**Required:** No strict change. Optionally introduce a protocol (e.g., `ActionProposer`) with `generate_next_step(messages) -> Tuple[Dict, Action, float]` and `append_step_to_messages(messages, message, action, observation) -> None` so the orchestrator depends on the protocol rather than concrete types. This keeps the orchestrator agent-agnostic. If not done, the orchestrator will accept a union type or a small wrapper that adapts each baseline.

### B.5 SolveResult — ensure total_cost populated for ReAct

**File:** `tau_bench/agents/chat_react_agent.py`

**Current:** `SolveResult(messages=..., reward=..., info=...)` does not pass `total_cost` (lines 89–93), though the type allows it.

**Required:** For baseline comparability and Phase 3 cost tracking, pass `total_cost=total_cost` in the return. Align with ToolCallingAgent and FewShotToolCallingAgent.

---

## C. Shared orchestration layer design

### C.1 Location and layout

- **Package:** `tau_bench/orchestration/` (new).
- **Modules (one .py per logical module, merges noted):**
  - `state.py` — Orchestrator + State Tracker (canonical state schema, loop driver).
  - `intent_constraint.py` — Intent & Constraint Extractor.
  - `memory.py` — Context Memory Manager.
  - `planner.py` — Planner / Decomposer (invokes base agent; produces candidate action + optional checkpoints).
  - `validator.py` — Tool Schema + Argument Validator.
  - `policy_guard.py` — Policy Guard.
  - `executor.py` — Tool Executor (thin wrapper around `env.step`).
  - `recovery.py` — Reflection + Recovery Agent.
  - `escalation.py` — Escalation Gate.

- **Config:** `tau_bench/orchestration/config.py` — Pydantic or dataclass for `use_intent_extractor`, `use_memory_manager`, `use_validator`, `use_policy_guard`, `use_escalation_gate`, `use_recovery`, plus budgets (max_steps, max_recovery_per_checkpoint, etc.).

- **Wrapped agents:** Live in `tau_bench/agents/` as new classes: `OrchestratedActAgent`, `OrchestratedReActAgent`, `OrchestratedToolCallingAgent`. Each holds a reference to the corresponding base agent (or factory) and an `OrchestrationConfig`; implements `Agent.solve()` by delegating to the orchestrator run loop.

### C.2 State schema (canonical state)

Single object passed through the loop; all modules read/write it. Proposed shape (conceptual; implement with Pydantic or TypedDict):

- `env: Env` — reference to current env (reset already called).
- `task_index: int`
- `messages: List[Dict]` — conversation history (same format the base agent expects).
- `goal: Optional[str]` — from Intent Extractor.
- `constraints: List[str]` or dict — from Intent Extractor.
- `plan_checkpoints: List[...]` — from Planner; optional.
- `tool_history: List[Action]` or last N actions — for progress/no-progress.
- `failure_counts: Dict[str, int]` — e.g., validation_failures, recovery_invocations.
- `recovery_count_this_checkpoint: int` — for cap.
- `last_observation: Optional[str]`, `last_action: Optional[Action]`, `last_source: Optional[str]` — from last env.step.
- `done: bool`, `reward: float`, `info: Dict` — from env.
- `total_cost: float`
- `trace: List[Dict]` — structured log events for annotation.

### C.3 Loop sketch (orchestrator)

The orchestrator drives a per-step loop that follows the intended runtime order:

1. Orchestrator holds state.
2. Pre-planning preparation (Memory and/or Intent).
3. Planner calls the base agent proposer.
4. Validator checks the action.
5. Policy Guard reviews.
6. Escalation Gate (only for escalation actions).
7. Executor runs the action.
8. Orchestrator updates state and messages.
9. Reflection/Recovery runs only when a failure condition is present.

In pseudocode:

```text
state = init_state(env, task_index, task, tools_info, wiki, config)

while not state.done and not budget_exhausted(state):
    # Pre-planning preparation: may include memory and/or intent, in any order
    state, messages_for_proposer = pre_planning_preparation(state)

    # Planner / base agent proposer
    message, action, cost = proposer.generate_next_step(messages_for_proposer)
    state.total_cost += (cost or 0.0)

    # Validator
    if config.use_validator:
        validator_out = validator(action, state)
        if not validator_out.ok:
            state = record_failure(state, "validation_error", validator_out)
            if config.use_recovery:
                state = recovery(state, "validation_error", validator_out)
            continue

    # Policy Guard
    if config.use_policy_guard:
        policy_out = policy_guard(action, state)
        if policy_out.block:
            state = record_failure(state, "policy_block", policy_out)
            if config.use_recovery:
                state = recovery(state, "policy_block", policy_out)
            continue
        if policy_out.rewrite:
            action = policy_out.rewritten_action

    # Escalation Gate (conditional)
    if config.use_escalation_gate and is_escalation_action(action):
        esc_out = escalation_gate(action, state)
        if not esc_out.allow:
            state = record_failure(state, "escalation_denied", esc_out)
            if config.use_recovery:
                state = recovery(state, "escalation_denied", esc_out)
            continue

    # Executor and state update
    obs, reward, done, info = executor(action, state.env)  # env.step(action)
    state = update_state_after_step(state, message, action, obs, reward, done, info)

    # Append according to agent-specific message format
    append_step_to_messages(state, message, action, obs)

    # Optional post-step memory maintenance
    if config.use_memory_manager:
        state.memory = memory_manager.compress_if_needed(state.memory, state)

    # Optional Recovery based on progress
    progress = check_progress(state)
    if (not progress.ok) and config.use_recovery:
        state = recovery(state, "no_progress", progress)

return SolveResult(
    reward=state.reward,
    messages=state.messages,
    info=state.info,
    total_cost=state.total_cost,
)
```

`pre_planning_preparation(state)` is a conceptual stage that may run the **Context Memory Manager** and the **Intent & Constraint Extractor** (when enabled). It guarantees only that all pre-planning modules complete **before** the Planner calls the proposer; it does **not** impose or rely on any specific ordering between Memory and Intent internally.

---

## D. Wrapped agent design for ACT / ReAct / Tool-Calling

### D.1 Shared behavior

- All three wrapped agents implement `Agent.solve(env, task_index, max_num_steps) -> SolveResult`.
- Each holds: (1) an instance of the corresponding base agent (or the same constructor args and builds it internally), (2) `OrchestrationConfig`, (3) references to orchestration modules (or the orchestrator that holds them).
- `solve()` does **not** call `base_agent.solve()`. It calls the orchestrator's run loop with:
  - `env`, `task_index`, `max_num_steps`
  - **proposer:** a callable that invokes `base_agent.generate_next_step(messages)` and returns `(message, action, cost)`
  - **append_step:** a callable that, given `(messages, message, action, observation)`, appends the correct messages (agent-specific format).

### D.2 Agent-specific behavior

| Aspect | ACT (OrchestratedActAgent) | ReAct (OrchestratedReActAgent) | Tool-Calling (OrchestratedToolCallingAgent) |
|--------|----------------------------|--------------------------------|--------------------------------------------|
| Base agent | `ChatReActAgent(..., use_reasoning=False)` | `ChatReActAgent(..., use_reasoning=True)` | `ToolCallingAgent(...)` |
| Proposer | `base_agent.generate_next_step(messages)` | Same | Same |
| Initial messages | Same as baseline: system = wiki + tools JSON + ACT_INSTRUCTION; user = first obs | Same as baseline: system = wiki + tools JSON + REACT_INSTRUCTION; user = first obs | Same as baseline: system = wiki; user = first obs |
| Append after step | Append `message`, then user message with content = `"API output: " + obs` if tool else `obs` | Same | Append `next_message`, then if tool: tool message (tool_call_id, name, content=obs); else user message with obs |
| total_cost | Sum cost from proposer each step | Same | Same |

Initial messages must be built exactly as in the baseline so that the first call to `generate_next_step` sees the same prompt. The orchestrator's `init_state` can accept a "message builder" or the wrapped agent can pass pre-built initial messages for the first iteration.

### D.3 Where proposer and append live

- **Option A:** Wrapped agent passes two callables to the orchestrator: `get_proposer()` → callable that closes over `base_agent`; `get_append_step()` → callable that implements the append logic for that agent type. Orchestrator is fully agent-agnostic.
- **Option B:** Orchestrator accepts an "action proposer" object that implements `generate_next_step(messages)` and `append_step_to_messages(messages, message, action, observation)`. Each wrapped agent constructs an adapter that wraps the base agent and exposes these. Base agents that don't have `append_step_to_messages` can be wrapped by a small adapter that encodes the append rules per agent type.

Recommendation: **Option B** with an adapter in the agents package (e.g., `ProposerAdapter` for each of ACT, ReAct, ToolCalling) that wraps the base agent and implements the append logic. Orchestrator then only depends on the adapter interface.

---

## E. Ablation-ready module boundaries

- Each module is called only when the corresponding config flag is True.
- When a module is disabled:
  - **Intent Extractor:** Skip intent/constraint extraction; `state.goal` / `state.constraints` remain empty or from initial state.
  - **Memory Manager:** Do not update or compress memory; `state.messages` are used as-is (or a trivial identity "memory" that just returns current messages).
  - **Validator:** Skip validation; always treat `validator_out.ok = True` (conceptually); no recovery from validation failure.
  - **Policy Guard:** Skip policy check; always allow (no block/rewrite).
  - **Escalation Gate:** Skip gate; escalation actions are executed like any other action.
  - **Recovery:** When recovery is disabled, on validation failure or policy block or no-progress, do not call recovery; instead apply a fixed fallback (e.g., increment failure counter, append an error message to the user, and continue the loop, or break with done=False). Exact fallback should be specified so ablations are comparable.

Config type (conceptual):

```python
class OrchestrationConfig:
    use_intent_extractor: bool = True
    use_memory_manager: bool = True
    use_validator: bool = True
    use_policy_guard: bool = True
    use_escalation_gate: bool = True
    use_recovery: bool = True
    max_steps: int = 30
    max_recovery_per_checkpoint: int = 2
    ...
```

All flags default True for "full" system; ablations set one to False.

---

## F. Execution risks and mitigation

| Risk | Cause | Mitigation |
|------|--------|------------|
| Proposer returns invalid action (e.g., unknown tool name) | Base agent can emit any string (ACT/ReAct) or tool_calls (TC). | Validator (when enabled) rejects before `env.step`. Executor never sees invalid tool names; env would return "Unknown action X". |
| Proposer raises (e.g., JSON decode in message_to_action) | ToolCallingAgent: `json.loads(arguments)` can raise. | Orchestrator catches exceptions from proposer call; treat as validation failure and invoke recovery (or fallback if recovery disabled). Do not let exception propagate out of `solve()`. |
| Message shape mismatch | Orchestrator builds or mutates `messages`; base agent expects a specific format (e.g., tool role for TC). | Append logic is agent-specific and must match baseline exactly. Reuse the same append logic as in baseline `solve()` (or the new `append_step_to_messages`). Never let a shared orchestrator overwrite messages with a generic format. |
| First-step messages | Orchestrator must pass the same initial messages as baseline to `generate_next_step`. | Build initial messages in the wrapped agent (or in a factory the orchestrator calls) using the same recipe as baseline: system content and first user message from env.reset(). |
| done vs last_observation | First iteration has no "last" env.step; observation comes from reset. | In init_state, set `state.last_observation = env.reset(task_index).observation`. Loop uses `last_observation` for intent/memory; after executor, set `last_observation = obs`. |
| Recovery loop unbounded | Recovery could repeatedly suggest bad actions. | Cap `recovery_count_this_checkpoint` (and total recovery count); after cap, apply fallback (e.g., safe respond or terminate) and continue/break. |
| Env.step side effects | Env mutates `self.actions`, `self.data`. | No change from baseline; orchestrator calls env.step exactly once per executed action. |
| total_cost | Must aggregate cost from proposer and optionally from other LLM calls (intent, recovery). | Orchestrator accumulates cost in state.total_cost; return in SolveResult. |

---

## G. Recommended implementation order

1. **Refactors (no orchestration):** Add `generate_next_step` to ToolCallingAgent and FewShotToolCallingAgent; refactor their `solve()` to use it. Fix ChatReActAgent to include `total_cost` in SolveResult. Optionally add `append_step_to_messages` to all three base agents or to adapter wrappers.
2. **State + config:** Define `OrchestrationConfig` and canonical state schema in `tau_bench/orchestration/state.py` (or `config.py` + `state.py`).
3. **Executor:** Implement `executor.py` as a thin wrapper around `env.step` (same signature as env.step; takes state to get env). No ablation; always used.
4. **Validator:** Implement `validator.py` (schema check, tool name in tools_info, argument grounding stub or simple checks). Integrate into a minimal orchestrator loop that: init_state → loop: proposer → validator → executor → append → done check. No recovery yet; on validation failure, break or continue with a fixed response.
5. **Orchestrator loop (minimal):** Implement the full loop in `state.py` / `orchestration/run.py` with validator and executor only; add config flags so validator can be turned off. Wire to a single wrapped agent (e.g., OrchestratedToolCallingAgent) to verify end-to-end.
6. **Policy Guard:** Implement `policy_guard.py`; plug into loop with `use_policy_guard`; add fallback when disabled.
7. **Recovery:** Implement `recovery.py`; plug in on validation failure, policy block, no-progress; add cap and fallback; gate with `use_recovery`.
8. **Intent Extractor:** Implement `intent_constraint.py`; run on user turns; gate with `use_intent_extractor`.
9. **Memory Manager:** Implement `memory.py` (e.g., pinned facts, rolling summary, recent buffer); gate with `use_memory_manager`; ensure get_messages_for_proposer returns format expected by base agent.
10. **Escalation Gate:** Implement `escalation.py`; run when action is escalation tool; gate with `use_escalation_gate`.
11. **Planner checkpoints (optional):** Add short-horizon plan/checkpoint from planner and no-progress detection; wire recovery to it.
12. **All three wrapped agents:** OrchestratedActAgent, OrchestratedReActAgent, OrchestratedToolCallingAgent; register in run.py agent_factory (e.g., `orchestrated-act`, `orchestrated-react`, `orchestrated-tool-calling`).
13. **Checkpoint path and metrics:** Ensure orchestrated strategies get distinct checkpoint filenames and that display_metrics and pass^k logic are unchanged.

---

## Flow chart: high-level runtime

The diagram below shows the **logical runtime flow per step**. Arrows indicate control flow; boxes are modules. The **pre-planning preparation** stage may include both Memory and Intent (if enabled) in any order before the Planner calls the proposer.

```
                    ┌─────────────────────────────────────┐
                    │   Orchestrator + State Tracker      │
                    │   (loop driver, canonical state)    │
                    └─────────────────┬───────────────────┘
                                      │
                                      │  maintains `state`
                                      ▼
                       ┌───────────────────────────────┐
                       │   Pre-planning preparation    │
                       │   (Memory and/or Intent)      │
                       │   - Context Memory Manager    │
                       │   - Intent & Constraint Ext.  │
                       └───────────────┬───────────────┘
                                       │
                                       │ messages_for_proposer
                                       ▼
                            ┌─────────────────────────┐
                            │   Planner / Proposer    │
                            │ (calls base agent's     │
                            │  generate_next_step)    │
                            └─────────────┬───────────┘
                                          │
                                          │ candidate Action
                                          ▼
                             ┌────────────────────────┐
                             │ Tool Schema +          │
                             │ Argument Validator     │
                             └────────────┬───────────┘
                                          │ ok / fail
                                          ▼
                             ┌────────────────────────┐
                             │ Policy Guard           │
                             └────────────┬───────────┘
                                          │ allow/block/rewrite
                                          ▼
                             ┌────────────────────────┐
                             │ Escalation Gate        │
                             │ (only for escalation   │
                             │  actions)              │
                             └────────────┬───────────┘
                                          │
                                          │ approved Action
                                          ▼
                             ┌────────────────────────┐
                             │ Tool Executor          │
                             │   (env.step)           │
                             └────────────┬───────────┘
                                          │ obs, reward, done
                                          ▼
                   ┌────────────────────────────────────────────┐
                   │ Orchestrator state update + message append │
                   └────────────────┬───────────────────────────┘
                                    │
                                    │ failure / progress check
                                    ▼
                         ┌────────────────────────────┐
                         │ Reflection & Recovery      │
                         │ (only when needed)         │
                         └────────────────────────────┘
```

Pre-planning preparation is a **stage**, not a fixed order between Memory and Intent: implementations may run Memory first, Intent first, or both independently, as long as both complete (when enabled) **before** the Planner/Proposer.

---

## Implementation pipeline: module-by-module

**Per-step runtime pipeline (logical order):**  
Orchestrator & State Tracker (holding `state`)  
→ Pre-planning preparation (Context Memory Manager and/or Intent & Constraint Extractor, both optional)  
→ Planner / base agent proposer (ACT / ReAct / Tool-Calling)  
→ Tool Schema + Argument Validator  
→ Policy Guard  
→ Escalation Gate (only for escalation actions)  
→ Tool Executor (`env.step`)  
→ Orchestrator state update + agent-specific message append  
→ Reflection & Recovery (only when a failure condition is present).

The module descriptions below are organized by responsibility and where they intercept the **baseline** (`agent.solve` → `env.step`) loop; they should not be interpreted as imposing any additional ordering beyond the pipeline above.

---

### Runtime control-flow diagram

The diagram below shows **explicit control-flow branches**, loop-back edges, and exit conditions for one episode. Diamonds indicate decisions; arrows show where the loop continues vs exits.

```text
                      ┌───────────────────────────────┐
                      │  Start episode                │
                      │  env_reset(task_index)        │
                      └─────────────┬─────────────────┘
                                    │
                                    ▼
                      ┌───────────────────────────────┐
                      │  Initialize state             │
                      │  (last_observation, messages, │
                      │   reward=0, done=False, ...)  │
                      └─────────────┬─────────────────┘
                                    │
                             [main loop]
                                    │
                                    ▼
                 ┌──────────────────────────────────────┐
                 │  Pre-planning preparation            │
                 │  (Memory and/or Intent, optional)    │
                 └─────────────┬────────────────────────┘
                               │
                               ▼
                 ┌──────────────────────────────────────┐
                 │  Planner / Proposer                  │
                 │  (message, action, cost              │
                 │   = base_agent.generate_next_step)   │
                 └─────────────┬────────────────────────┘
                               │
                               ▼
                 ┌──────────────────────────────────────┐
                 │  Validator: action ok?               │
                 └─────────────┬───────────────┬────────┘
                               │yes            │no
                               │               │
                               ▼               ▼
                 ┌─────────────────────┐   ┌─────────────────────────┐
                 │  Policy Guard       │   │ Record validation fail  │
                 │  allow/block/rewrite│   │ (state, trace, counters)│
                 └──────┬──────┬───────┘   └─────────────┬───────────┘
                        │allow │rewrite                  │
                        │      │                         │
                        │      ▼                         │
                        │  (update action)               │
                        │                                │
                        │block                           │
                        ▼                                ▼
        ┌────────────────────────────────┐   ┌────────────────────────┐
        │ Escalation action?            │   │  Recovery? (if enabled) │
        │ (name in escalation tools?)   │   └───────────┬─────────────┘
        └──────────────┬───────┬────────┘               │yes
                       │no     │yes                     │
                       │       │                        ▼
                       ▼       ▼            ┌──────────────────────────┐
        ┌────────────────────┐ ┌──────────────────────────┐            │
        │  Tool Executor     │ │  Escalation Gate:        │<───────────┘
        │  env.step(action)  │ │  allow / deny            │
        └─────────┬──────────┘ └────────────┬─────────────┘
                  │                        │
                  │                        │deny
                  │                        ▼
                  │           ┌──────────────────────────┐
                  │           │  Record escalation deny  │
                  │           │  Recovery? (if enabled)  │
                  │           └───────────┬──────────────┘
                  │                       │yes
                  │                       │
                  │                       ▼
                  │             (run Recovery, update state,
                  │              then jump to next loop iteration)
                  │
                  ▼
     ┌───────────────────────────────────────────────────┐
     │  Orchestrator state update + message append       │
     │  - update last_observation, reward, done, info    │
     │  - append to messages (agent-specific format)     │
     └─────────────┬─────────────────────────────────────┘
                   │
                   ▼
     ┌───────────────────────────────────────────────────┐
     │  Check progress / failure conditions              │
     │  - no-progress? loops? other triggers?           │
     └─────────────┬─────────────────────────────────────┘
                   │
         no-prog?  │yes                       │no
                   ▼                          │
     ┌───────────────────────────────────┐     │
     │  Recovery? (if enabled)          │     │
     └─────────────┬────────────────────┘     │
                   │yes                       │
                   ▼                          │
         (run Recovery, update state,         │
          then continue main loop)            │
                                              │
                                              ▼
                           ┌─────────────────────────────┐
                           │  Done? or budget exhausted? │
                           └─────────────┬───────────────┘
                                         │yes
                                         ▼
                           ┌─────────────────────────────┐
                           │  Exit episode               │
                           │  - task done (done=True)    │
                           │  - safe termination by      │
                           │    Recovery / policy        │
                           │  - budget / step limit hit  │
                           └─────────────────────────────┘
                                         ▲
                                         │no
                                         │
                                         └───── loop back to
                                               pre-planning
                                               preparation
```

Key exit conditions:
- **Task done**: `env.step` sets `done=True` and reward is computed.
- **Safe termination**: Recovery or policy logic decides to stop (e.g., by emitting a final `respond` and not continuing).
- **Budget exhausted / turn limit**: `budget_exhausted(state)` or `max_num_steps` reached; loop exits even if `done=False`.

Recovery is only invoked when:
- Validator fails,
- Policy Guard blocks,
- Escalation Gate denies, or
- No-progress / other failure condition is detected.

If Recovery is disabled, the orchestrator uses deterministic fallbacks (as defined in the ablation section) and still follows the same high-level control flow.

---

### Orchestrator + State Tracker

| Item | Detail |
|------|--------|
| **Inputs** | `env: Env`, `task_index: int`, `max_num_steps: int`, proposer (callable or adapter), append_step (callable), `OrchestrationConfig`, initial `messages` (or builder), `task`, `tools_info`, `wiki`, `rules` (policy). |
| **Outputs** | `SolveResult(reward, messages, info, total_cost)` and optionally a structured `trace` in `info`. |
| **Intercept** | Replaces the entire baseline loop. Entry: after `run.py` calls `agent.solve(env, task_index)` and the agent is an orchestrated wrapper, the orchestrator runs from `env.reset(task_index)` and then the step loop. No call to `base_agent.solve()`. |
| **Shared vs agent-specific** | Fully shared. Agent-specific parts are the proposer and append_step callables (or adapter) passed in. |
| **Execution risks** | (1) State must be initialized with `last_observation` from `env.reset()`. (2) First iteration must not call executor before proposer; proposer uses initial messages. (3) If proposer raises, catch and treat as failure path (recovery or fallback). |

---

### Planner / Decomposer

| Item | Detail |
|------|--------|
| **Inputs** | `state` (with `messages`, `env`, and any plan fields). Proposer callable (or base agent) from wrapped agent. |
| **Outputs** | `candidate_action: Action`, optional `plan` (e.g., checkpoints for no-progress). Cost added to `state.total_cost`. |
| **Intercept** | Replaces the "model call + parse" part of the baseline loop. In baseline, this is `generate_next_step(messages)` (ReAct/ACT) or the inline completion + message_to_action (ToolCalling). Here, the orchestrator calls the same `generate_next_step(state.messages)` via the proposer. |
| **Shared vs agent-specific** | Invocation is shared; the actual call is to the agent-specific proposer (ACT vs ReAct vs ToolCalling). Planner module is shared; it does not know the agent type. |
| **Execution risks** | (1) `state.messages` (or `messages_for_proposer`) must be in the format the base agent expects (especially for ToolCalling: roles and tool_calls). (2) If `generate_next_step` raises (e.g., JSON error in TC), exception must be caught by orchestrator and handled as validation failure + recovery. |

---

### Tool Schema + Argument Validator

| Item | Detail |
|------|--------|
| **Inputs** | `candidate_action: Action`, `state` (for tools_info, task, optional memory for grounding), `tools_info` from env. |
| **Outputs** | Structured result: `ok: bool`, and if not ok: `reason`, optional `details` (e.g., which argument failed). |
| **Intercept** | Between Planner output and Policy Guard. In baseline, there is no validator; actions go straight to `env.step`. Here, if validator says not ok, skip executor and go to recovery. |
| **Shared vs agent-specific** | Shared. All strategies produce the same `Action` type; validator uses `tools_info` and env's tool names (and optionally `respond` special case). |
| **Execution risks** | (1) For `respond`, validator must not require tool schema; define a separate branch (e.g., require `content` key). (2) Env has `tools_map`; validator should use same source of truth (e.g., `tools_info` from env) so "valid" means "name in tools_map or respond". |

---

### Policy Guard

| Item | Detail |
|------|--------|
| **Inputs** | `candidate_action: Action`, `state` (task, rules/policy, constraints, conversation context). |
| **Outputs** | Decision: `allow` \| `block` \| `rewrite`; if rewrite, `rewritten_action: Action`. |
| **Intercept** | After Validator, before Executor. Baseline has no policy guard; all actions go to env.step. |
| **Shared vs agent-specific** | Shared. Policy and task come from env/state; no agent-type-specific logic. |
| **Execution risks** | (1) For `respond`, policy guard should be able to check required phrases (task.outputs) and block/rewrite. (2) Ensure rewritten action is still valid (validator can be run again on rewrite if desired). |

---

### Escalation Gate

| Item | Detail |
|------|--------|
| **Inputs** | `state`, policy/rules, and indication that `candidate_action` is an escalation action (e.g., name == transfer_to_human or a configurable list). |
| **Outputs** | `allow: bool`; if not allow, optional `fallback_recovery` so orchestrator can invoke recovery instead of executing. |
| **Intercept** | Only when the approved action (after policy guard) is an escalation action; runs before Executor. Baseline executes escalation tools without a gate. |
| **Shared vs agent-specific** | Shared. Escalation tool name(s) can come from env or config (e.g., from tools that are in a "terminate_tools" or "escalation_tools" list). |
| **Execution risks** | (1) Only run when action is actually an escalation tool; do not block other actions. (2) When gate denies, do not call env.step for that action; run recovery/fallback instead. |

---

### Tool Executor

| Item | Detail |
|------|--------|
| **Inputs** | `action: Action`, `env: Env`. |
| **Outputs** | `observation: str`, `reward: float`, `done: bool`, `info: EnvInfo` — same as `EnvResponse`. |
| **Intercept** | Replaces the direct `env.step(action)` call in the baseline loop. Orchestrator calls executor instead of calling env.step directly; executor simply returns `env.step(action)`. |
| **Shared vs agent-specific** | Shared. All strategies use the same `env.step(action)`. |
| **Execution risks** | (1) Must only be called with an action that passed validator and policy guard (and escalation gate if applicable). (2) Env mutates internal state; no change from baseline. |

---

### Reflection + Recovery

| Item | Detail |
|------|--------|
| **Inputs** | `state`, `failure_type: str` (e.g., "validation_error", "policy_block", "no_progress"), `details` (validator_out, policy_out, or progress result). |
| **Outputs** | Updated `state` (e.g., repaired action to retry, or updated messages with error context, or decision to ask user / terminate). Optionally a concrete `Action` to use instead of re-calling proposer. |
| **Intercept** | When validator fails, policy guard blocks, escalation gate denies, or no-progress is detected. In baseline, there is no recovery; the loop just continues with the next user/tool observation. Here, recovery can modify state and then `continue` the loop without executing the failed action. |
| **Shared vs agent-specific** | Shared. Recovery may produce a repaired `Action` or a prompt/message addition; it does not need to know which base agent is used. |
| **Execution risks** | (1) Cap recovery attempts per checkpoint (and globally) to avoid infinite loops. (2) When recovery is disabled, use a deterministic fallback (e.g., append error to messages and continue, or break) so behavior is reproducible. |

---

### Intent & Constraint Extractor

| Item | Detail |
|------|--------|
| **Inputs** | Current observation (when it is a user turn), `state` (messages, task.instruction), policy/rules. |
| **Outputs** | Updated `state` with `goal`, `constraints` (and any structured slots) for use by Planner, Policy Guard, and Memory. |
| **Intercept** | At start of each step, before Planner, only when the observation is from the user (e.g., `state.last_source == "user"` or first step). Do not run on tool outputs. |
| **Shared vs agent-specific** | Shared. Intent is derived from user text and task; no agent-type dependency. |
| **Execution risks** | (1) Distinguish user vs tool observation using `info.source` from the last env response (or from state). (2) First step: observation from reset is a user turn. |

---

### Context Memory Manager

| Item | Detail |
|------|--------|
| **Inputs** | `state.memory` (or equivalent), current observation, action, and state (messages, constraints). |
| **Outputs** | Updated memory (pinned facts, rolling summary, recent buffer). When "get messages for proposer" is called, return a message list that conforms to the base agent's expected format. |
| **Intercept** | After each step: update memory with new observation/action. Before Planner: optionally replace or augment `state.messages` with memory's view (e.g., compressed middle, recent turns). When disabled, identity: messages unchanged. |
| **Shared vs agent-specific** | Shared interface; implementation must produce message lists that are valid for the active base agent (same roles and structure as baseline). So memory's "get_messages" may need a hint (agent_type) or the append logic stays agent-specific and memory only provides a "summary" segment to inject. |
| **Execution risks** | (1) Compressed/summarized messages must not break `generate_next_step` (e.g., ToolCalling expects assistant messages with `tool_calls` and tool messages with `tool_call_id`). (2) Avoid double-compression or losing recent tool outputs. |

---

## Proposed implementation sequence (minimizes execution issues, preserves ablations)

1. **Refactors only** — ToolCallingAgent and FewShotToolCallingAgent: add `generate_next_step`; refactor `solve()` to use it. ChatReActAgent: pass `total_cost` in SolveResult. Verify baseline tests/behavior unchanged.
2. **Orchestration config + state schema** — Define `OrchestrationConfig` and canonical state in `tau_bench/orchestration/`. No loop yet.
3. **Executor module** — Implement; unit test with a dummy env and action.
4. **Validator module** — Implement; unit test with valid/invalid actions and respond.
5. **Minimal orchestrator loop** — Implement loop with: init_state (from env.reset), proposer → validator → executor → agent-specific append → done. No recovery: on validation failure, break or append error and continue. Config: use_validator on/off.
6. **Proposer adapter** — Implement adapter (or callables) for one agent (e.g., ToolCalling) that builds initial messages and provides generate_next_step + append_step. Wire OrchestratedToolCallingAgent to the minimal orchestrator; run one task end-to-end.
7. **Policy Guard module** — Implement; add to loop with use_policy_guard; fallback when disabled.
8. **Recovery module** — Implement; call on validation failure and policy block; add cap and fallback; use_recovery flag.
9. **Escalation Gate module** — Implement; add to loop when action is escalation; use_escalation_gate flag.
10. **Intent Extractor module** — Implement; run on user turns; use_intent_extractor flag.
11. **Memory Manager module** — Implement; update after step, compress when needed; get_messages_for_proposer; use_memory_manager flag. Ensure message format compatibility.
12. **Planner module** — Formalize as a module that takes state and proposer and returns candidate_action (+ optional plan). Already implied by "proposer" call; ensure cost and trace are updated.
13. **All three wrapped agents** — OrchestratedActAgent, OrchestratedReActAgent, OrchestratedToolCallingAgent with their respective proposer/append adapters. Register in run.py.
14. **Integration and ablation tests** — Run full system with all modules on; run with each module off in turn; compare to baseline (same env, same task set) to ensure no regression when orchestration is "all off" or minimal and that ablations are comparable.

This sequence keeps the critical path (proposer → validator → executor → append) working early, then adds safety and recovery, then adds optional modules (intent, memory, escalation), and finally wires all three agent types and validates ablations.

---

## Logging and tracing design (Phase 3)

### Folder structure

- **Root logging directory:** `logs/`
- **Per-job folder:** `logs/<job_id>/`
  - `job_id` is created once per `run(config)` invocation (e.g., timestamp or UUID).
  - Example:

  ```text
  logs/
    482193/
      A_T32_R3.log
      A_T32_R3.trace.jsonl
      A_T32_R3.summary.json
      R_T4_R1.log
      R_T4_R1.trace.jsonl
      R_T4_R1.summary.json
  ```

- **Flat structure inside job folder:** no subfolders per run; each run is a triplet of files identified by a short `run_id`.

### File naming scheme

- **Run identifier:**
  - `<domain_code>_T<task_id>_R<trial>`
  - Domain codes:
    - `A` = airline
    - `R` = retail
  - Examples:
    - `A_T32_R3` → airline, task 32, trial 3
    - `R_T4_R1` → retail, task 4, trial 1

- **Files per run (under `logs/<job_id>/`):**
  - Human-readable sequential log: `<run_id>.log`
  - Structured trace: `<run_id>.trace.jsonl`
  - Summary/metadata: `<run_id>.summary.json`

This naming is short and self-explanatory, making it easy to identify in editor tabs and tooling.

### Linear log design (`.log`)

**Purpose:** Provide a linear, human-readable narrative of the orchestrated run, step by step, without needing to inspect code or JSON.

- **Structure:**
  - **Run header** (once at top):

    ```text
    === RUN START ===
    job_id=482193
    run_id=A_T32_R3
    domain=airline
    task_id=32
    trial=3
    agent=OrchestratedReActAgent
    model=qwen3-14b
    seed=7
    git_commit=abc1234
    config_signature={
      use_validator=true,
      use_policy_guard=true,
      use_recovery=true,
      use_memory_manager=false,
      use_intent_extractor=false,
      use_escalation_gate=true
    }
    ```

  - **Reset / initialization block:**

    ```text
    [STEP 0] RESET
    initial_observation: "..."
    ```

  - **Per-step blocks (`STEP k`, k ≥ 1):**

    For each step, log the main stages in order:

    ```text
    [STEP 1] PRE-PLANNING
    memory_update: updated=true, summary_len=256
    intent_update: skipped (source=tool)

    [STEP 1] PROPOSER
    module=Planner/Proposer
    candidate_action={ name: "get_order_status", kwargs: { order_id: "W2702727" } }
    approx_cost_step=0.025
    total_cost_so_far=0.025

    [STEP 1] VALIDATOR
    result=PASS
    tool_name=get_order_status
    arg_issues=none

    [STEP 1] POLICY_GUARD
    result=ALLOW
    notes="within domain policy"

    [STEP 1] ESCALATION_GATE
    skipped=not_escalation_action

    [STEP 1] EXECUTOR
    tool_called=get_order_status
    tool_args={ order_id: "W2702727" }
    observation="Order W2702727 is pending..."
    reward=0.0
    done=false

    [STEP 1] STATE_UPDATE
    messages_appended=true
    last_observation="Order W2702727 is pending..."
    total_cost=0.025

    [STEP 1] PROGRESS_CHECK
    result=progress_ok
    recovery_triggered=false
    ```

    On failures, include explicit blocks:

    ```text
    [STEP 2] VALIDATOR
    result=FAIL
    reason="unknown tool name"
    action_name="foo_tool"

    [STEP 2] RECOVERY
    triggered_by=validation_error
    strategy="ask_clarifying_question"
    recovery_action={ name: "respond", kwargs: { content: "..." } }
    ```

  - **Run footer:**

    ```text
    === RUN END ===
    final_reward=1.0
    done=true
    exit_reason=task_completed
    steps=18
    total_cost=0.82
    ```

- **Per-entry content:**
  - `step_index`
  - module name (e.g., PRE-PLANNING, PROPOSER, VALIDATOR, POLICY_GUARD, ESCALATION_GATE, EXECUTOR, STATE_UPDATE, PROGRESS_CHECK, RECOVERY)
  - decision/result (pass/fail, allow/block/rewrite, etc.)
  - short action summary (`name`, key args)
  - key state fields (`total_cost`, `reward`, `done`, `exit_reason` at the end)
  - any error details

The `.log` file is designed so that reading it top-to-bottom tells the complete story of the run.

### Structured trace design (`.trace.jsonl`)

**Purpose:** Provide structured, machine-readable events for analysis, clustering, and replay; every event carries enough metadata to compare runs and configs.

- **Format:** One JSON object per line.
- **Per-event core fields:**
  - `timestamp` (ISO 8601 or epoch ms)
  - `job_id`
  - `run_id`
  - `step_index` (0 for reset, 1..N for steps)
  - `module` (e.g., `"reset"`, `"pre_planning"`, `"proposer"`, `"validator"`, `"policy_guard"`, `"escalation_gate"`, `"executor"`, `"state_update"`, `"progress_check"`, `"recovery"`, `"final"`)
  - `event_type` (e.g., `"init"`, `"decision"`, `"action"`, `"observation"`, `"update"`, `"exit"`)
  - `decision` (where applicable; e.g., `"pass"`, `"fail"`, `"allow"`, `"block"`, `"rewrite"`, `"skipped"`, `"allow_escalation"`, `"deny_escalation"`, `"progress_ok"`, `"no_progress"`)
  - `action_name` (for events involving an `Action`)
  - `tool_name` and `tool_args` (for tool-related events; truncated as needed)
  - `observation` (truncated)
  - `reward`
  - `done`
  - `total_cost`
  - `error` (if any)
  - `state_summary` (compact snapshot, e.g., number of past actions, current goal, number of constraints)

- **Run-level metadata on every event:**
  - `agent` (e.g., `"OrchestratedReActAgent"`)
  - `model`
  - `seed`
  - `git_commit`
  - `domain`
  - `task_id`
  - `trial`
  - `config_signature` (booleans for `use_validator`, `use_policy_guard`, `use_recovery`, `use_memory_manager`, `use_intent_extractor`, `use_escalation_gate`)
  - `run_fingerprint_human` (e.g., `"react_qwen3-14b_seed7_val1_pol1_rec1_mem0_int0_esc1"`)
  - `run_fingerprint_hash` (short hash, e.g., `"8f3c2d1a"`)

- **Examples:**

  - Reset event:

    ```json
    {
      "timestamp": "...",
      "job_id": "482193",
      "run_id": "A_T32_R3",
      "step_index": 0,
      "module": "reset",
      "event_type": "init",
      "observation": "Hi, I need help with ...",
      "agent": "OrchestratedReActAgent",
      "model": "qwen3-14b",
      "seed": 7,
      "git_commit": "abc1234",
      "domain": "airline",
      "task_id": 32,
      "trial": 3,
      "config_signature": { "...": true },
      "run_fingerprint_human": "react_qwen3-14b_seed7_val1_pol1_rec1_mem0_int0_esc1",
      "run_fingerprint_hash": "8f3c2d1a"
    }
    ```

  - Validator event:

    ```json
    {
      "timestamp": "...",
      "job_id": "482193",
      "run_id": "A_T32_R3",
      "step_index": 1,
      "module": "validator",
      "event_type": "decision",
      "action_name": "get_order_status",
      "decision": "pass",
      "error": null,
      "reward": 0.0,
      "done": false,
      "total_cost": 0.025,
      "agent": "OrchestratedReActAgent",
      "model": "qwen3-14b",
      "seed": 7,
      "domain": "airline",
      "task_id": 32,
      "trial": 3,
      "config_signature": { "...": true },
      "run_fingerprint_human": "...",
      "run_fingerprint_hash": "8f3c2d1a"
    }
    ```

  - Policy rewrite followed by re-validation will appear as:
    - A `"policy_guard"` event with `"decision": "rewrite"`.
    - A subsequent `"validator"` event evaluating the rewritten action.

### Summary file design (`.summary.json`)

**Purpose:** Capture run-level metadata and outcomes in a single JSON object, with ablation booleans at the top.

- **Contents:**

  ```json
  {
    "run_fingerprint_human": "react_qwen3-14b_seed7_val1_pol1_rec1_mem0_int0_esc1",
    "run_fingerprint_hash": "8f3c2d1a",
    "agent": "OrchestratedReActAgent",
    "model": "qwen3-14b",
    "seed": 7,
    "git_commit": "abc1234",

    "config_signature": {
      "use_validator": true,
      "use_policy_guard": true,
      "use_recovery": true,
      "use_memory_manager": false,
      "use_intent_extractor": false,
      "use_escalation_gate": true
    },

    "ablations": {
      "use_validator": true,
      "use_policy_guard": true,
      "use_recovery": true,
      "use_memory_manager": false,
      "use_intent_extractor": false,
      "use_escalation_gate": true
    },

    "domain": "airline",
    "task_id": 32,
    "trial": 3,

    "steps": 18,
    "total_cost": 0.82,
    "reward": 1.0,
    "done": true,
    "exit_reason": "task_completed",

    "num_validation_failures": 0,
    "num_policy_blocks": 0,
    "num_escalation_denied": 0,
    "num_recovery_invocations": 1
  }
  ```

- The summary is written at the end of a run, using counters accumulated during the loop and metadata known at start.

### Logging hook locations in the runtime loop

Logging is orchestrator-centric and agent-agnostic. Hooks should be added at the following points:

- **Run start:**
  - After `env.reset(task_index)` and `init_state`.
  - Write header in `.log`.
  - Emit `"reset"` event in `.trace.jsonl`.
  - Initialize `.summary.json` metadata (domain, task_id, trial, agent, model, seed, config_signature, fingerprints).

- **After pre-planning preparation:**
  - Immediately after `pre_planning_preparation(state)` returns.
  - `.log`: `[STEP k] PRE-PLANNING` with memory/intent updates.
  - `.trace.jsonl`: event with `module="pre_planning"`, `state_summary`, flags for `intent_ran`, `memory_ran`.

- **After proposer:**
  - After `message, action, cost = proposer.generate_next_step(messages_for_proposer)`.
  - `.log`: `[STEP k] PROPOSER` with candidate action and step cost.
  - `.trace.jsonl`: event with `module="proposer"`, `event_type="action"`, `action_name`, `tool_args` (if any), `cost`, `total_cost`.

- **After validator:**
  - After any validator decision (initial or for rewritten actions).
  - `.log`: `[STEP k] VALIDATOR` with `result=PASS/FAIL`, reason, arg issues.
  - `.trace.jsonl`: event with `module="validator"`, `decision`, `error`.
  - On `FAIL`: also log Recovery (if used) and do not log Executor/StateUpdate for that step.

- **After policy guard:**
  - Only if validator passed.
  - `.log`: `[STEP k] POLICY_GUARD` with `result=ALLOW/BLOCK/REWRITE`.
  - `.trace.jsonl`: `module="policy_guard"`, `decision`.
  - On `BLOCK`: log Recovery as failure handling.
  - On `REWRITE`: log the rewrite and then a new validator event for the rewritten action.

- **After escalation gate (if applicable):**
  - If action is recognized as escalation.
  - `.log`: `[STEP k] ESCALATION_GATE` with `result=ALLOW/DENY` or `skipped`.
  - `.trace.jsonl`: `module="escalation_gate"`, `decision`.
  - On `DENY`: log Recovery and skip Executor for that step.

- **After executor:**
  - When `env.step(action)` is called.
  - `.log`: `[STEP k] EXECUTOR` with:
    - `tool_called` / `respond`
    - `tool_args`
    - `observation` (possibly truncated)
    - `reward`, `done`.
  - `.trace.jsonl`: `module="executor"`, `event_type="observation"`, `action_name`, `tool_args`, `observation`, `reward`, `done`.

- **After state update + message append:**
  - After `update_state_after_step` and `append_step_to_messages`.
  - `.log`: `[STEP k] STATE_UPDATE` with `messages_appended`, `total_cost`, and key state changes.
  - `.trace.jsonl`: `module="state_update"`, `event_type="update"`, `state_summary`.

- **After progress check / Recovery:**
  - After `check_progress(state)` and optional Recovery.
  - `.log`:
    - `[STEP k] PROGRESS_CHECK` with `result=progress_ok` or `no_progress`, `recovery_triggered`.
    - `[STEP k] RECOVERY` with `triggered_by`, `strategy`, `recovery_action` if Recovery ran.
  - `.trace.jsonl`:
    - `module="progress_check"`, `decision`.
    - `module="recovery"` events when Recovery executes.

- **Final termination:**
  - When the loop ends because:
    - `done=True`,
    - budget/step limit exceeded, or
    - safe termination via Recovery/Policy.
  - `.log` footer `=== RUN END ===` with final metrics and exit reason.
  - `.trace.jsonl`: `module="final"`, `event_type="exit"`, `exit_reason`, final reward, steps.
  - `.summary.json`: write the summarized object with all ablations and counters.

These hooks must be applied uniformly for:
- `OrchestratedActAgent`
- `OrchestratedReActAgent`
- `OrchestratedToolCallingAgent`

and must rely only on standardized `Action`, `EnvResponse`, and orchestrator `state`, not on internal message formatting of the base agents.

### Performance considerations

- **I/O overhead:**
  - Logging two files (`.log` and `.trace.jsonl`) per step will increase disk writes.
  - Mitigation:
    - Use buffered writes.
    - Optionally gate detailed logging behind a flag (e.g., `enable_detailed_logging`) for large-scale experiments.

- **Log size:**
  - Long episodes lead to large `.trace.jsonl` and `.log` files.
  - Mitigation:
    - Truncate long fields (`observation`, `tool_args`) to a fixed length.
    - Keep `state_summary` compact and pre-filtered.

- **CPU overhead:**
  - JSON serialization per event has a cost.
  - Mitigation:
    - Avoid dumping the entire state; log only selected fields.
    - Reuse constant metadata (config_signature, fingerprints) via template objects.

- **Latency-sensitive measurements:**
  - If latency later becomes a metric, logging can bias results.
  - Mitigation:
    - Allow disabling detailed logging or supporting a “minimal logging” mode (e.g., only header, footer, and failures).

This logging and tracing design is fully compatible with the orchestration architecture, ablation flags, and all three wrapped agent strategies, and should significantly simplify debugging and post-hoc analysis of Phase 3 runs.

---

## File-level interface design for logging and orchestrator integration

Design-level interfaces and file responsibilities only. No full code.

### 1. Which files / classes own logging

| Responsibility | Owner | Location |
|----------------|--------|----------|
| **Run logger instance** (writes `.log`, `.trace.jsonl`, `.summary.json` for one run) | A single class that holds file handles and write methods | `tau_bench/orchestration/logging.py` — e.g., `OrchestrationRunLogger` (or `Phase3RunLogger`) |
| **Logger factory / initialization** | Creates a run logger for a given `job_id`, `run_id`, and run metadata | Same module: e.g., `create_run_logger(job_id, run_id, run_metadata, log_dir="logs") -> OrchestrationRunLogger` |
| **Schema types for log payloads** | Pydantic models or TypedDicts for event payloads and summary | `tau_bench/orchestration/logging_schemas.py` (or in `logging.py` if kept small) — e.g., `LogRunMetadata`, `TraceEvent`, `SummaryPayload` |
| **Invocation of the logger** | Orchestrator loop only; no other module writes to the run logger | `tau_bench/orchestration/state.py` (or wherever the step loop lives) — the loop calls logger methods at the hook points below |
| **Job id creation and log_dir** | Decided at entry to a batch of runs | `tau_bench/run.py` (or orchestration entry point): create `job_id` once per `run(config)`; pass `log_dir` and `job_id` into the orchestrator so it can create a run logger per (task_index, trial) |

So: **logging module** owns the logger class and the methods that write to disk; **orchestrator** owns the loop and calls those methods; **run entry point** owns job_id and log_dir.

### 2. Where logger initialization happens

- **Job-level:** When `run(config)` starts (in `tau_bench/run.py` or the Phase 3 entry path):
  - Create `job_id` (e.g., timestamp or short UUID).
  - Ensure `log_dir` exists, e.g. `logs/<job_id>/` (or use a single `logs/` and `job_id` as subfolder).
  - Pass `job_id`, `log_dir`, and optionally `config` (for ablation flags) into the code that runs each task/trial.

- **Run-level:** When the orchestrator is about to start **one** episode (one task_id + one trial):
  - Compute `run_id` = `<domain_code>_T<task_id>_R<trial>` (domain from config.env or state).
  - Build a **run metadata** object (agent name, model, seed, git_commit, config_signature, run_fingerprint_human, run_fingerprint_hash).
  - Call **create_run_logger(job_id, run_id, run_metadata, log_dir)** to get an `OrchestrationRunLogger` instance.
  - Pass this instance into the orchestrator for that episode (e.g., set on state, or pass as argument to the loop).
  - If logging is disabled (e.g., config flag), create a no-op logger that implements the same interface but does nothing.

So: **initialization** is at the boundary between “run(config)” and “one episode” — i.e., right before the orchestrator loop for that episode starts.

### 3. What methods write `.log`, `.trace.jsonl`, and `.summary.json`

All methods live on the **run logger** instance (e.g., `OrchestrationRunLogger`).

| Method | Writes | When called |
|--------|--------|-------------|
| `log_run_start(metadata)` | `.log` (header) | Once at start of episode, after init_state. |
| `log_run_end(exit_reason, steps, total_cost, reward, done)` | `.log` (footer) | Once when loop exits (normal or exception path). |
| `log_step_stage(step_index, stage, payload)` | `.log` (one or more lines for a stage) | After each runtime stage (pre_planning, proposer, validator, policy_guard, escalation_gate, executor, state_update, progress_check, recovery). Payload is a small dict or schema. |
| `write_trace_event(event: TraceEvent)` | `.trace.jsonl` (one line) | For every event (run start, each stage, run end). Event carries full schema (timestamp, step_index, module, decision, run metadata, etc.). |
| `write_summary(summary: SummaryPayload)` | `.summary.json` (single JSON object) | Once at end of episode (normal or exception path). |

So: **.log** is written by `log_run_start`, `log_step_stage`, and `log_run_end`. **.trace.jsonl** is written by `write_trace_event` for every event. **.summary.json** is written once by `write_summary`.

### 4. Data schema each method accepts

- **Run metadata (for start and for every trace event):**
  - `job_id`, `run_id`, `domain`, `task_id`, `trial`, `agent`, `model`, `seed`, `git_commit`
  - `config_signature`: dict with keys `use_validator`, `use_policy_guard`, `use_recovery`, `use_memory_manager`, `use_intent_extractor`, `use_escalation_gate` (all bool)
  - `run_fingerprint_human`, `run_fingerprint_hash`

- **log_step_stage(payload):**
  - `step_index: int`
  - `stage: str` (e.g., `"RESET"`, `"PRE_PLANNING"`, `"PROPOSER"`, `"VALIDATOR"`, `"POLICY_GUARD"`, `"ESCALATION_GATE"`, `"EXECUTOR"`, `"STATE_UPDATE"`, `"PROGRESS_CHECK"`, `"RECOVERY"`)
  - `payload: dict` (or a small schema per stage) with keys such as:
    - For RESET: `initial_observation` (truncated)
    - For PROPOSER: `candidate_action` (name, kwargs summary), `cost_step`, `total_cost_so_far`
    - For VALIDATOR: `result` (pass/fail), `reason`, `action_name`, `arg_issues`
    - For POLICY_GUARD: `result` (allow/block/rewrite), `notes`
    - For ESCALATION_GATE: `result` or `skipped`, `reason`
    - For EXECUTOR: `tool_called`/action name, `tool_args`, `observation` (truncated), `reward`, `done`
    - For STATE_UPDATE: `messages_appended`, `total_cost`, optional state snapshot
    - For PROGRESS_CHECK: `result`, `recovery_triggered`
    - For RECOVERY: `triggered_by`, `strategy`, `recovery_action` (optional)

- **TraceEvent (for write_trace_event):**
  - All run metadata fields above (so every line is self-describing).
  - `timestamp`, `step_index`, `module`, `event_type`
  - Optional: `decision`, `action_name`, `tool_name`, `tool_args`, `observation`, `reward`, `done`, `total_cost`, `error`, `state_summary` (compact dict).

- **SummaryPayload (for write_summary):**
  - Same run metadata + `ablations` (same as config_signature, duplicated for visibility).
  - `steps`, `total_cost`, `reward`, `done`, `exit_reason`
  - Optional counters: `num_validation_failures`, `num_policy_blocks`, `num_escalation_denied`, `num_recovery_invocations`.

All of these should be defined as TypedDicts or Pydantic models in `logging_schemas.py` (or equivalent) so the orchestrator and logger share a contract without depending on raw dicts.

### 5. How logging is hooked into the runtime loop

- The **orchestrator** (the code that runs the step loop) receives a **run logger instance** at the start of the episode (or a no-op logger if logging is disabled).
- At each hook point already defined in “Logging hook locations”:
  1. The orchestrator builds the minimal **payload** for that stage (from state, action, env response, validator result, etc.).
  2. It calls **logger.log_step_stage(step_index, stage, payload)** for the human-readable log.
  3. It builds a **TraceEvent** from the same information (plus run metadata, which the logger can attach if stored at init) and calls **logger.write_trace_event(event)**.
- For run start: orchestrator calls **logger.log_run_start(metadata)** and **logger.write_trace_event(reset_event)** after init_state.
- For run end (normal or exception): orchestrator calls **logger.log_run_end(...)** and **logger.write_summary(summary)**. If an exception occurs mid-loop, the orchestrator must catch it, call log_run_end and write_summary with the best available state (e.g., exit_reason="error"), then re-raise or handle.

So: the **loop is the only place** that calls the logger. No module (Validator, Policy Guard, etc.) receives or uses the logger; they only return results. The orchestrator translates those results into log payloads and trace events. This keeps logging agent-agnostic and format-agnostic.

### 6. Exceptions and partial runs: safe flush

- **Buffering:** The run logger should use **buffered writes** for `.log` and `.trace.jsonl` (e.g., write to a StringIO or buffer and flush periodically, or flush on each write if acceptable). `.summary.json` is written once at the end.
- **End-of-run contract:** The orchestrator **always** calls a single **close** or **finish** method on the logger at the end of the episode, whether the loop exited normally, by budget, or by exception. For example:
  - **logger.finish_run(exit_reason, steps, total_cost, reward, done, counters)**
  - This method:
    - Flushes any buffers for `.log` and `.trace.jsonl`.
    - Writes the run-end block to `.log`.
    - Writes the final trace event to `.trace.jsonl`.
    - Builds and writes `.summary.json` (with ablations at top).
    - Closes file handles.
- **Exception handling:** The orchestrator runs the step loop inside a try/except. In the except block it:
  - Determines `exit_reason="error"` and captures partial state (e.g., last step_index, total_cost so far, reward so far).
  - Calls **logger.finish_run(..., exit_reason="error")** so that partial `.log` and `.trace.jsonl` are flushed and `.summary.json` is written with the best available info.
  - Then re-raises or returns a failure result.
- **No logger state in domain modules:** Validator, Policy Guard, Recovery, etc., do not hold references to the logger. So their exceptions do not require the logger to be closed; only the orchestrator’s try/except and finish_run are responsible for safe flush.

### 7. Compatibility with wrapped ACT / ReAct / Tool-Calling agents

- The logger and all schemas use only **orchestrator-level concepts**:
  - `Action` (name, kwargs) — same for all three agents.
  - `EnvResponse` (observation, reward, done, info).
  - Step index, module names, decisions, and state summaries (e.g., goal, constraints, total_cost, num actions).
- They do **not** depend on:
  - The shape of `messages` (e.g., tool_calls vs Thought/Action).
  - The internal format of the proposer’s return value beyond (message, action, cost).
- The **orchestrator** is the only component that talks to the logger. Wrapped agents (OrchestratedActAgent, OrchestratedReActAgent, OrchestratedToolCallingAgent) only provide a proposer and an append_step callable; they do not see the logger. So:
  - Adding or changing a wrapped agent does not require changes to the logging module.
  - The same logger class and same hook points work for all three agents.
- **Run metadata** (agent name, model, config_signature) is set at run start from the **orchestrator’s** context (which knows which wrapped agent is running). The logger only records what it is given; it does not need to branch on agent type.

---

## Concrete file/class API skeleton plan (logging and orchestrator)

Design/interface level only. No full code.

### A. Files to create or modify

| File | Action | Purpose |
|------|--------|---------|
| `tau_bench/orchestration/logging_schemas.py` | **Create** | Define all payload types (RunMetadata, TraceEvent, SummaryPayload, stage payload shapes). No file I/O. |
| `tau_bench/orchestration/logging.py` | **Create** | Define `OrchestrationRunLogger`, `NoOpRunLogger`, `create_run_logger`, and helpers for run_id / file paths. All file opens, buffers, flushes, and closes live here. |
| `tau_bench/orchestration/run.py` (or wherever the step loop lives) | **Modify** | Accept an optional logger (or logger factory) and call logger methods at each hook; call `finish_run` on normal and exception exit. No knowledge of file paths or schemas beyond passing through. |
| `tau_bench/run.py` (or Phase 3 entry) | **Modify** | Create `job_id` when starting a batch; pass `job_id`, `log_dir`, and `enable_logging` into the per-episode runner; per episode, compute `run_id`, build metadata, call `create_run_logger` or no-op factory and pass logger into orchestrator. |

No other files create or hold the logger. Orchestrator code does not import schema types for anything except constructing payloads to pass into the logger.

### B. Classes and function signatures

**In `logging_schemas.py` (all data-only; no I/O):**

- **RunMetadata** (TypedDict or Pydantic):  
  `job_id`, `run_id`, `domain`, `task_id`, `trial`, `agent`, `model`, `seed`, `git_commit`, `config_signature` (dict of ablation bools), `run_fingerprint_human`, `run_fingerprint_hash`.

- **TraceEvent** (TypedDict or Pydantic):  
  All RunMetadata fields plus: `timestamp`, `step_index`, `module`, `event_type`; optional: `decision`, `action_name`, `tool_name`, `tool_args`, `observation`, `reward`, `done`, `total_cost`, `error`, `state_summary`.

- **SummaryPayload** (TypedDict or Pydantic):  
  RunMetadata-like fields plus `ablations` (same as config_signature), `steps`, `total_cost`, `reward`, `done`, `exit_reason`; optional: `num_validation_failures`, `num_policy_blocks`, `num_escalation_denied`, `num_recovery_invocations`.

- **StagePayload** (TypedDict or plain dict contract):  
  Stage-specific key-value map (e.g. `initial_observation`, `candidate_action`, `result`, `observation`, etc.). Document per-stage keys; implementation can use a single dict or small per-stage types.

**In `logging.py`:**

- **Protocol or ABC: RunLoggerProtocol** (optional but recommended):  
  - `log_run_start(metadata: RunMetadata) -> None`  
  - `log_run_end(exit_reason: str, steps: int, total_cost: float, reward: float, done: bool) -> None`  
  - `log_step_stage(step_index: int, stage: str, payload: dict) -> None`  
  - `write_trace_event(event: TraceEvent) -> None`  
  - `write_summary(summary: SummaryPayload) -> None`  
  - `finish_run(exit_reason: str, steps: int, total_cost: float, reward: float, done: bool, counters: dict | None) -> None`  

  Ensures orchestrator and factory depend on the protocol, not a concrete class.

- **OrchestrationRunLogger**:  
  Implements the protocol. Constructor: `__init__(self, log_dir: str, job_id: str, run_id: str, metadata: RunMetadata)`.  
  - **Responsibility of each method:**  
    - `log_run_start(metadata)`: Write the `=== RUN START ===` block and metadata lines to the `.log` file (buffer). Do not open files in other methods if files are opened in `__init__`; otherwise open `.log` and `.trace.jsonl` on first write (lazy open) and keep handles.  
    - `log_run_end(exit_reason, steps, total_cost, reward, done)`: Write the `=== RUN END ===` block to the `.log` buffer. Does not close; `finish_run` does.  
    - `log_step_stage(step_index, stage, payload)`: Append one or more lines for `[STEP k] STAGE` and payload to the `.log` buffer.  
    - `write_trace_event(event)`: Serialize `event` to JSON, append newline, write to `.trace.jsonl` buffer.  
    - `write_summary(summary)`: Not called by orchestrator directly; `finish_run` builds and writes summary. (Or: orchestrator can call `write_summary` once before `finish_run`; then `finish_run` only flushes and closes. Design choice: keep single end-of-run contract in `finish_run` so orchestrator only calls `finish_run` at the end.)  
    - `finish_run(exit_reason, steps, total_cost, reward, done, counters)`: See section D and E.

- **NoOpRunLogger**:  
  Implements the same protocol. Every method is a no-op (return immediately). No file handles, no state. Used when logging is disabled.

- **create_run_logger(**  
  `log_dir: str`,  
  `job_id: str`,  
  `run_id: str`,  
  `metadata: RunMetadata`,  
  `enabled: bool = True`  
  `) -> RunLoggerProtocol`:  
  If `enabled` is False, return a `NoOpRunLogger()` instance. Otherwise, ensure `log_dir/job_id` exists, then return `OrchestrationRunLogger(log_dir, job_id, run_id, metadata)`.

- **run_id_from(domain: str, task_id: int, trial: int) -> str**:  
  Return `f"{domain_code}_T{task_id}_R{trial}"` where `domain_code` is `"A"` for `domain == "airline"` else `"R"` for `"retail"`. Used by entry point to build `run_id` before creating the logger.

- **job_id_new() -> str** (optional):  
  Return a new job id (e.g. timestamp `YYYYMMDD_HHMMSS` or short UUID). Used by `run.py` when starting a batch. Can live in run.py instead if preferred.

### C. Lifecycle of logger object

1. **Creation:** Entry point (or the code that runs one episode) has `job_id`, `log_dir`, `domain`, `task_id`, `trial`, and run metadata. It calls `run_id = run_id_from(domain, task_id, trial)` then `logger = create_run_logger(log_dir, job_id, run_id, metadata, enabled=config.enable_logging)`.
2. **Run start:** Orchestrator calls `logger.log_run_start(metadata)` and `logger.write_trace_event(reset_event)` (first trace event).
3. **Per step:** Orchestrator calls `logger.log_step_stage(...)` and `logger.write_trace_event(...)` at each hook. No explicit flush between steps (buffered).
4. **Run end:** Orchestrator always calls `logger.finish_run(exit_reason, steps, total_cost, reward, done, counters)` once when the episode ends—whether by normal exit, budget exhaustion, safe termination, or exception. After that, the orchestrator does not use the logger again for that episode.
5. **Disposal:** No explicit `close` in the orchestrator. `finish_run` closes handles; the logger object can then be discarded. No context manager required if `finish_run` is guaranteed to be called (e.g. in a try/finally or try/except that always calls `finish_run`).

### D. File handle / flush strategy

- **OrchestrationRunLogger:**
  - **Open:** In `__init__`, open two files under `log_dir/job_id/`:  
    - `<run_id>.log` (text, append or write mode)  
    - `<run_id>.trace.jsonl` (text, append or write mode)  
  - **Buffer:** Use a small in-memory buffer (e.g. 4–8 KB) per file, or line-buffer (flush on newline). Alternatively, unbuffered or line-buffered for simplicity so that partial runs are visible without explicit flush (at the cost of more syscalls).  
  - **Writes:** `log_run_start`, `log_run_end`, `log_step_stage` write to the `.log` handle. `write_trace_event` writes one JSON line to the `.trace.jsonl` handle.  
  - **flush:** At the end of `finish_run`, flush both file handles before writing the summary file.  
  - **Close:** In `finish_run`, after writing `.summary.json`, close the `.log` and `.trace.jsonl` handles. Optionally close before writing summary so that summary write is independent of the stream handles.  
  - **Summary file:** `.summary.json` is opened, written once (full payload), closed inside `finish_run`. No buffering needed for a single write.

- **File names:**  
  - Base path: `os.path.join(log_dir, job_id)`.  
  - Files: `os.path.join(base, f"{run_id}.log")`, `f"{run_id}.trace.jsonl"`, `f"{run_id}.summary.json"`.  
  - `run_id` is produced by `run_id_from(domain, task_id, trial)`; no other component generates it.

### E. Failure and exception handling path

- Orchestrator runs the step loop inside `try:` and, in `except:`, captures:
  - `exit_reason = "error"`
  - `steps` = last completed step index (or number of steps started)
  - `total_cost`, `reward`, `done` = best available from state (or 0, 0, False)
  - `counters` = partial counters if available

- Then it calls `logger.finish_run(exit_reason="error", steps=..., total_cost=..., reward=..., done=..., counters=...)`.

- **finish_run** (success, safe_termination, budget_exhausted, error):
  - **Success:** `exit_reason="task_completed"`. Write run-end to `.log`, emit final trace event to `.trace.jsonl`, build SummaryPayload (with ablations at top), write `.summary.json`, flush and close handles.
  - **Safe termination:** `exit_reason="safe_termination"`. Same as success; only the label differs.
  - **Budget exhausted:** `exit_reason="budget_exhausted"`. Same write sequence; summary reflects `done=False` and exit_reason.
  - **Exception / partial run:** `exit_reason="error"`. Same write sequence; steps/cost/reward/counters may be partial. Ensures any buffered content is flushed so the `.log` and `.trace.jsonl` contain everything written so far, then write run-end and final event and summary. If an exception occurs inside `finish_run` (e.g. disk full), log it (e.g. to stderr or a fallback) and optionally re-raise; do not leave file handles open (use try/finally to close).

- Orchestrator must not swallow the exception after calling `finish_run` if the intention is to propagate failure (e.g. re-raise after finish_run in except block).

### F. No-op logger design

- **NoOpRunLogger** implements the same protocol as **OrchestrationRunLogger** (same method names and signatures).
- Every method body is empty (or `pass`). No attributes needed (or minimal, e.g. `enabled: bool = False` for debugging).
- **create_run_logger(..., enabled=False)** returns an instance of **NoOpRunLogger**; the orchestrator does not branch on “enabled” and always calls the same methods. So the orchestrator code is identical whether logging is on or off; only the object passed in differs.

### G. First and last trace events (shape)

- **First trace event (run start):**
  - `step_index=0`, `module="reset"`, `event_type="init"`.
  - Include full RunMetadata (job_id, run_id, domain, task_id, trial, agent, model, seed, git_commit, config_signature, run_fingerprint_human, run_fingerprint_hash).
  - Include `observation` = initial observation (truncated).
  - No `action_name`, `reward`, `done` required for init; they can be omitted or null.

- **Last trace event (run end):**
  - `step_index` = last step index (same as `steps` in summary).
  - `module="final"`, `event_type="exit"`.
  - Include `exit_reason`, `reward`, `done`, `steps`, `total_cost`.
  - Include same RunMetadata so the line is self-contained. No `observation` or `action_name` required.

Both events are produced by the orchestrator (or by the logger from parameters passed by the orchestrator); the logger only serializes and writes.

### H. Minimal dependencies / risks and ambiguities

- **Minimal dependencies:**  
  - Orchestrator imports only: the logger protocol (or the concrete class) and `create_run_logger`. It does not import schema types if the logger accepts dicts; if it accepts TypedDict/Pydantic, orchestrator imports the minimal set (RunMetadata, TraceEvent, SummaryPayload) only for constructing payloads.  
  - Logging module imports only: standard library (os, io, json, datetime), and logging_schemas. It does not import env, agents, or tau_bench.types except if needed for type hints (e.g. Action) in schemas; prefer keeping schemas in terms of dicts/str/float so that logging_schemas and logging do not depend on tau_bench domains.

- **Risks / ambiguities:**  
  - **Double flush:** If the orchestrator calls `log_run_end` and then `finish_run`, ensure run-end is written only once (e.g. run-end is written inside `finish_run` only, and `log_run_end` is not used; or `log_run_end` only writes to buffer and `finish_run` flushes and writes summary. Clarify: run-end block is written in `finish_run` so a single method owns “end of run” and flush/close.)  
  - **Lazy vs eager open:** Opening files in `__init__` avoids lazy-open complexity and makes it clear when files are created; if an episode is abandoned before any log call, files would still exist (empty or with only header). Prefer open in `__init__` for simplicity.  
  - **Counters:** Orchestrator must maintain counters (e.g. num_validation_failures) and pass them into `finish_run` so summary can be complete. Decide where counters live (e.g. on state object) so the orchestrator can pass them without the logger depending on state type.
