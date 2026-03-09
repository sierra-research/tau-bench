# Copyright Sierra
# Phase 3 run logger: .log, .trace.jsonl, .summary.json. Orchestrator is the only caller.

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from tau_bench.orchestration.logging_schemas import RunMetadata, StagePayload, SummaryPayload, TraceEvent

TRUNCATE_LEN = 512
OBS_SUMMARY_LEN = 200

# Benchmark success: reward in [1-ε, 1+ε] (same as display_metrics)
def _task_success(reward: float) -> bool:
    return (1 - 1e-6) <= reward <= (1 + 1e-6)


def _truncate(s: str, max_len: int = TRUNCATE_LEN) -> str:
    if not isinstance(s, str):
        return str(s)
    return s[:max_len] + "..." if len(s) > max_len else s


def run_id_from(domain: str, task_id: int, trial: int) -> str:
    """Build run id: A_T32_R3 or R_T4_R1."""
    code = "A" if domain == "airline" else "R"
    return f"{code}_T{task_id}_R{trial}"


def job_id_new() -> str:
    """New job id for a batch (e.g. timestamp)."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class OrchestrationRunLogger:
    """Writes one run's .log, .trace.jsonl, .summary.json. Files opened in __init__, closed in finish_run."""

    def __init__(self, log_dir: str, job_id: str, run_id: str, metadata: RunMetadata) -> None:
        self._job_id = job_id
        self._run_id = run_id
        self._metadata = dict(metadata)
        self._step_count = 0
        self._counters: Dict[str, int] = {}
        base = os.path.join(log_dir, job_id, "runs")
        os.makedirs(base, exist_ok=True)
        self._log_path = os.path.join(base, f"{run_id}.log")
        self._trace_path = os.path.join(base, f"{run_id}.trace.jsonl")
        self._summary_path = os.path.join(base, f"{run_id}.summary.json")
        self._log_file = open(self._log_path, "w", encoding="utf-8")
        self._trace_file = open(self._trace_path, "w", encoding="utf-8")
        self._finished = False

    def _base_event(self, step_index: int, module: str, event_type: str) -> TraceEvent:
        out = dict(self._metadata)
        out["step_index"] = step_index
        out["module"] = module
        out["event_type"] = event_type
        out["timestamp"] = datetime.utcnow().isoformat() + "Z"
        return out

    def log_run_start(self, metadata: Optional[RunMetadata] = None) -> None:
        if metadata:
            self._metadata.update(metadata)
        m = self._metadata
        self._log_file.write("=== RUN START ===\n")
        self._log_file.write(f"job_id={self._job_id}\n")
        self._log_file.write(f"run_id={self._run_id}\n")
        for k in ("domain", "task_id", "trial", "agent", "model", "seed", "git_commit"):
            if k in m:
                self._log_file.write(f"{k}={m[k]}\n")
        if "config_signature" in m:
            self._log_file.write(f"config_signature={json.dumps(m['config_signature'])}\n")
        self._log_file.flush()

    def log_run_end(
        self,
        exit_reason: str,
        steps: int,
        total_cost: float,
        reward: float,
        done: bool,
        task_success: Optional[bool] = None,
    ) -> None:
        if task_success is None:
            task_success = _task_success(reward)
        self._log_file.write("=== RUN END ===\n")
        self._log_file.write(f"runtime_exit_reason={exit_reason}\n")
        self._log_file.write(f"reward={reward}\n")
        self._log_file.write(f"done={done}\n")
        self._log_file.write(f"task_success={task_success}\n")
        self._log_file.write(f"steps={steps}\n")
        self._log_file.write(f"total_cost={total_cost}\n")
        self._log_file.flush()

    def log_step_stage(self, step_index: int, stage: str, payload: StagePayload) -> None:
        self._log_file.write(f"[STEP {step_index}] {stage}\n")
        for k, v in payload.items():
            if isinstance(v, str) and len(v) > TRUNCATE_LEN:
                v = _truncate(v)
            self._log_file.write(f"  {k}={v}\n")
        self._log_file.flush()

    def write_trace_event(self, event: TraceEvent) -> None:
        # Ensure metadata and timestamp present
        e = dict(self._metadata)
        e.update(event)
        if "timestamp" not in e:
            e["timestamp"] = datetime.utcnow().isoformat() + "Z"
        self._trace_file.write(json.dumps(e, default=str) + "\n")
        self._trace_file.flush()

    def write_summary(self, summary: SummaryPayload) -> None:
        with open(self._summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

    def finish_run(
        self,
        exit_reason: str,
        steps: int,
        total_cost: float,
        reward: float,
        done: bool,
        counters: Optional[Dict[str, int]] = None,
    ) -> None:
        if self._finished:
            return
        self._finished = True
        try:
            task_success = _task_success(reward)
            self.log_run_end(exit_reason, steps, total_cost, reward, done, task_success=task_success)
            final_event = self._base_event(steps, "final", "exit")
            final_event["runtime_exit_reason"] = exit_reason
            final_event["reward"] = reward
            final_event["done"] = done
            final_event["task_success"] = task_success
            final_event["steps"] = steps
            final_event["total_cost"] = total_cost
            self.write_trace_event(final_event)
            summary: SummaryPayload = dict(self._metadata)
            summary.setdefault("ablations", summary.get("config_signature", {}))
            summary["steps"] = steps
            summary["total_cost"] = total_cost
            summary["reward"] = reward
            summary["done"] = done
            summary["runtime_exit_reason"] = exit_reason
            summary["task_success"] = task_success
            if counters:
                summary.update(counters)
            self.write_summary(summary)
        finally:
            self._log_file.close()
            self._trace_file.close()


class NoOpRunLogger:
    """No-op logger when logging is disabled. Same interface as OrchestrationRunLogger."""

    def log_run_start(self, metadata: Optional[RunMetadata] = None) -> None:
        pass

    def log_run_end(
        self,
        exit_reason: str,
        steps: int,
        total_cost: float,
        reward: float,
        done: bool,
        task_success: Optional[bool] = None,
    ) -> None:
        pass

    def log_step_stage(self, step_index: int, stage: str, payload: StagePayload) -> None:
        pass

    def write_trace_event(self, event: TraceEvent) -> None:
        pass

    def write_summary(self, summary: SummaryPayload) -> None:
        pass

    def finish_run(
        self,
        exit_reason: str,
        steps: int,
        total_cost: float,
        reward: float,
        done: bool,
        counters: Optional[Dict[str, int]] = None,
    ) -> None:
        pass


def observation_summary(obs: str, max_len: int = OBS_SUMMARY_LEN) -> str:
    """Concise observation for trace/log; caller can use _truncate for longer payloads."""
    if not isinstance(obs, str):
        return str(obs)[:max_len]
    return obs[:max_len] + ("..." if len(obs) > max_len else "")


def create_run_logger(
    log_dir: str,
    job_id: str,
    run_id: str,
    metadata: RunMetadata,
    enabled: bool = True,
) -> Any:  # RunLoggerProtocol
    """Return a run logger (or no-op if enabled=False)."""
    if not enabled:
        return NoOpRunLogger()
    return OrchestrationRunLogger(log_dir, job_id, run_id, metadata)
