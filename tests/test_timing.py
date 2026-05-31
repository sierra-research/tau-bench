# Copyright Sierra

"""Schema-invariant tests for the shared timing core.

These guard the core guarantee behind the two timing drivers: a live report
and a replay-graft report produced from the same sequence of spans must be
structurally indistinguishable -- identical span kinds, names, step grouping,
and aggregation. The ONLY field allowed to differ is ``source``.
"""

import itertools

from tau_bench.timing import SpanKind, TimingRecorder, build_report
from tau_bench.types import TimingReport


class FakeClock:
    """Deterministic monotonic clock: each call advances by a fixed step."""

    def __init__(self, step: float = 0.1):
        self._t = 0.0
        self._step = step

    def __call__(self) -> float:
        t = self._t
        self._t += self._step
        return t


def _record_canonical_trajectory(source: str) -> TimingReport:
    """Drive the SAME canonical op sequence through a recorder.

    Sequence mirrors a tiny tau-bench task:
      step -1: user (initial)
      step 0 : agent -> tool
      step 1 : agent -> user (respond)
    """
    rec = TimingRecorder(source=source, clock=FakeClock(step=0.05))
    rec.begin_step(-1)
    with rec.span(SpanKind.USER_LLM, "user"):
        pass
    rec.begin_step(0)
    with rec.span(SpanKind.AGENT_LLM, "agent"):
        pass
    with rec.span(SpanKind.TOOL_EXEC, "find_user_id_by_email"):
        pass
    rec.begin_step(1)
    with rec.span(SpanKind.AGENT_LLM, "agent"):
        pass
    with rec.span(SpanKind.USER_LLM, "user"):
        pass
    return rec.report()


def _structural_signature(report: TimingReport):
    """Everything about a report EXCEPT the measured durations and source."""
    return {
        "n_steps": report.n_steps,
        "steps": [
            (
                st.step_index,
                tuple((s.kind, s.name, s.step_index, s.seq) for s in st.spans),
            )
            for st in report.steps
        ],
        "spans": [(s.kind, s.name, s.step_index, s.seq) for s in report.spans],
    }


def test_live_and_replay_reports_are_structurally_identical():
    live = _record_canonical_trajectory("live")
    replay = _record_canonical_trajectory("replay")
    # Only the source label may differ.
    assert live.source == "live"
    assert replay.source == "replay"
    assert _structural_signature(live) == _structural_signature(replay)


def test_report_schema_fields():
    report = _record_canonical_trajectory("live")
    # Step rollups + grand totals are present and self-consistent.
    assert report.n_steps == 3  # steps -1, 0, 1
    assert report.agent_llm_ms == sum(st.agent_llm_ms for st in report.steps)
    assert report.tool_ms == sum(st.tool_ms for st in report.steps)
    assert report.user_llm_ms == sum(st.user_llm_ms for st in report.steps)
    # Every span carries the report's source.
    assert all(s.source == report.source for s in report.spans)
    # Spans are globally ordered by seq.
    seqs = [s.seq for s in report.spans]
    assert seqs == sorted(seqs)


def test_spans_grouped_by_step():
    report = _record_canonical_trajectory("replay")
    by_step = {st.step_index: st for st in report.steps}
    assert set(by_step) == {-1, 0, 1}
    # step 0 has exactly one agent_llm and one tool_exec span.
    kinds_step0 = sorted(s.kind for s in by_step[0].spans)
    assert kinds_step0 == [SpanKind.AGENT_LLM, SpanKind.TOOL_EXEC]


def test_suspend_drops_spans():
    rec = TimingRecorder(source="replay", clock=FakeClock())
    rec.begin_step(0)
    with rec.suspend():
        with rec.span(SpanKind.TOOL_EXEC, "reward_replay_tool"):
            pass
    with rec.span(SpanKind.AGENT_LLM, "agent"):
        pass
    report = rec.report()
    assert all(s.name != "reward_replay_tool" for s in report.spans)
    assert len(report.spans) == 1


def test_empty_recorder_is_safe():
    report = build_report([], "live")
    assert report.n_steps == 0
    assert report.total_ms == 0.0
    assert report.spans == []
