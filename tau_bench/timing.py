# Copyright Sierra

"""Shared timing telemetry core for tau-bench.

This module is the single source of truth for *how* timing is recorded and
aggregated. It is consumed by two drivers that MUST produce identical
telemetry (same schema, same span kinds, same step aggregation):

  * the live run loop  -> records wall-clock latency of real LLM/tool calls
  * the replay-graft loop -> records timing while replaying a recorded
    trajectory (shadow-timed LLM calls, real tool execution)

The only fields that legitimately differ between the two are ``source``
("live" vs "replay") and the measured durations. Everything structural
(span kinds, names, step grouping) is produced by this shared code, so a
report cannot tell you which driver made it except via ``source``.

When no recorder is attached, all instrumentation is a no-op and upstream
behavior is bit-identical.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Callable, Iterator, List, Optional

from tau_bench.types import StepTiming, TimingReport, TimingSpan


class SpanKind:
    """Canonical sub-step span kinds. Shared by both drivers."""

    AGENT_LLM = "agent_llm"  # one agent completion() call
    TOOL_EXEC = "tool_exec"  # one env tool .invoke()
    USER_LLM = "user_llm"  # one user-simulator completion() call


class TimingRecorder:
    """Collects timing spans and aggregates them into a TimingReport.

    The driver sets the current step via ``begin_step`` and wraps each timed
    operation in ``span``. Env / user code records spans against whatever the
    current step is, so they don't need to know step numbers.
    """

    def __init__(
        self,
        source: str = "live",
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.source = source
        self._clock = clock
        self._t0: Optional[float] = None
        self._seq = 0
        self.current_step = -1
        self.spans: List[TimingSpan] = []
        # Disables tool spans while Env.calculate_reward replays GT actions,
        # so reward-replay tool invokes are never counted as trajectory time.
        self.suspended = False

    def start(self) -> None:
        if self._t0 is None:
            self._t0 = self._clock()

    def begin_step(self, step_index: int) -> None:
        self.start()
        self.current_step = step_index

    @contextmanager
    def span(self, kind: str, name: str) -> Iterator[None]:
        if self.suspended:
            yield
            return
        self.start()
        assert self._t0 is not None
        t_start = self._clock()
        try:
            yield
        finally:
            t_end = self._clock()
            self.spans.append(
                TimingSpan(
                    kind=kind,
                    name=name,
                    step_index=self.current_step,
                    seq=self._seq,
                    wall_offset_ms=(t_start - self._t0) * 1000.0,
                    duration_ms=(t_end - t_start) * 1000.0,
                    source=self.source,
                )
            )
            self._seq += 1

    @contextmanager
    def suspend(self) -> Iterator[None]:
        """Temporarily stop recording (used during reward replay)."""
        prev = self.suspended
        self.suspended = True
        try:
            yield
        finally:
            self.suspended = prev

    def report(self) -> TimingReport:
        return build_report(self.spans, self.source)


def build_report(spans: List[TimingSpan], source: str) -> TimingReport:
    """Aggregate flat spans into per-step rollups and grand totals.

    This is intentionally a free function so both drivers (and tests) reduce
    spans the exact same way.
    """
    by_step: dict[int, List[TimingSpan]] = {}
    for s in spans:
        by_step.setdefault(s.step_index, []).append(s)

    steps: List[StepTiming] = []
    for step_index in sorted(by_step):
        step_spans = sorted(by_step[step_index], key=lambda s: s.seq)
        agent_ms = sum(s.duration_ms for s in step_spans if s.kind == SpanKind.AGENT_LLM)
        tool_ms = sum(s.duration_ms for s in step_spans if s.kind == SpanKind.TOOL_EXEC)
        user_ms = sum(s.duration_ms for s in step_spans if s.kind == SpanKind.USER_LLM)
        first_start = min(s.wall_offset_ms for s in step_spans)
        last_end = max(s.wall_offset_ms + s.duration_ms for s in step_spans)
        steps.append(
            StepTiming(
                step_index=step_index,
                agent_llm_ms=agent_ms,
                tool_ms=tool_ms,
                user_llm_ms=user_ms,
                step_ms=last_end - first_start,
                spans=step_spans,
            )
        )

    total_agent = sum(st.agent_llm_ms for st in steps)
    total_tool = sum(st.tool_ms for st in steps)
    total_user = sum(st.user_llm_ms for st in steps)
    if spans:
        total_ms = max(s.wall_offset_ms + s.duration_ms for s in spans) - min(
            s.wall_offset_ms for s in spans
        )
    else:
        total_ms = 0.0
    return TimingReport(
        source=source,
        total_ms=total_ms,
        agent_llm_ms=total_agent,
        tool_ms=total_tool,
        user_llm_ms=total_user,
        n_steps=len(steps),
        steps=steps,
        spans=sorted(spans, key=lambda s: s.seq),
    )
