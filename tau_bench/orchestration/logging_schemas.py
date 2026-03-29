# Copyright Sierra
# Phase 3 orchestration logging schemas (data-only, no I/O).

from typing import Any, Dict

# Run-level metadata (job_id, run_id, domain, agent, config_signature, fingerprints).
# Used at run start and included in every trace event.
ConfigSignature = Dict[str, bool]

RunMetadata = Dict[str, Any]  # job_id, run_id, domain, task_id, trial, agent, model, seed,
# git_commit, config_signature, run_fingerprint_human, run_fingerprint_hash

# One line in .trace.jsonl: RunMetadata + event fields.
TraceEvent = Dict[str, Any]  # RunMetadata + timestamp, step_index, module, event_type,
# optional: decision, action_name, tool_name, tool_args, observation, reward, done, total_cost, error, state_summary

# Single JSON object written to .summary.json (ablations at top).
SummaryPayload = Dict[str, Any]  # RunMetadata-like + ablations, steps, total_cost, reward, done, exit_reason,
# optional: num_validation_failures, num_policy_blocks, num_escalation_denied, num_recovery_invocations

# Stage payload for log_step_stage(step_index, stage, payload). Keys depend on stage.
StagePayload = Dict[str, Any]
