# Copyright Sierra

from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

RESPOND_ACTION_NAME = "respond"
RESPOND_ACTION_FIELD_NAME = "content"


class Action(BaseModel):
    name: str
    kwargs: Dict[str, Any]


class Task(BaseModel):
    user_id: str
    actions: List[Action]
    instruction: str
    outputs: List[str]


class RewardOutputInfo(BaseModel):
    r_outputs: float
    outputs: Dict[str, bool]


class RewardActionInfo(BaseModel):
    r_actions: float
    gt_data_hash: str


class RewardResult(BaseModel):
    reward: float
    info: Union[RewardOutputInfo, RewardActionInfo]
    actions: List[Action]


class TimingSpan(BaseModel):
    """A single timed sub-step. Shared by the live and replay-graft drivers."""

    kind: str  # one of tau_bench.timing.SpanKind
    name: str  # tool name, or "agent" / "user"
    step_index: int
    seq: int
    wall_offset_ms: float
    duration_ms: float
    source: str = "live"  # "live" or "replay"


class StepTiming(BaseModel):
    """Per-step rollup of the sub-step spans belonging to one agent step."""

    step_index: int
    agent_llm_ms: float = 0.0
    tool_ms: float = 0.0
    user_llm_ms: float = 0.0
    step_ms: float = 0.0
    spans: List[TimingSpan] = []


class TimingReport(BaseModel):
    """Full timing telemetry for a single solved task."""

    source: str  # "live" or "replay"
    total_ms: float
    agent_llm_ms: float
    tool_ms: float
    user_llm_ms: float
    n_steps: int
    steps: List[StepTiming] = []
    spans: List[TimingSpan] = []


class SolveResult(BaseModel):
    reward: float
    messages: List[Dict[str, Any]]
    info: Dict[str, Any]
    total_cost: Optional[float] = None
    timing: Optional[TimingReport] = None


class EnvInfo(BaseModel):
    task: Task
    source: Optional[str] = None
    user_cost: Optional[float] = None
    reward_info: Optional[RewardResult] = None


class EnvResponse(BaseModel):
    observation: str
    reward: float
    done: bool
    info: EnvInfo


class EnvResetResponse(BaseModel):
    observation: str
    info: EnvInfo


class EnvRunResult(BaseModel):
    task_id: int
    reward: float
    info: Dict[str, Any]
    traj: List[Dict[str, Any]]
    trial: int
    timing: Optional[TimingReport] = None


class RunConfig(BaseModel):
    model_provider: str
    user_model_provider: str
    model: str
    user_model: str = "gpt-4o"
    num_trials: int = 1
    env: str = "retail"
    agent_strategy: str = "tool-calling"
    temperature: float = 0.0
    task_split: str = "test"
    start_index: int = 0
    end_index: int = -1
    task_ids: Optional[List[int]] = None
    log_dir: str = "results"
    max_concurrency: int = 1
    seed: int = 10
    shuffle: int = 0
    user_strategy: str = "llm"
    few_shot_displays_path: Optional[str] = None
    enable_timing: bool = False
