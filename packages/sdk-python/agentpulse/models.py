"""Data models for AgentPulse telemetry."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class SpanKind(str, Enum):
    LLM = "llm"
    TOOL = "tool"
    CUSTOM = "custom"


class TraceStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class Span:
    name: str
    kind: SpanKind
    trace_id: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    parent_span_id: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    input: Optional[Any] = None
    output: Optional[Any] = None
    model: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_usd: Optional[float] = None
    error: Optional[str] = None

    def end(self, error: Optional[str] = None) -> None:
        self.ended_at = time.time()
        if error:
            self.error = error

    def set_output(self, output: Any) -> None:
        self.output = output

    def set_input(self, input_data: Any) -> None:
        self.input = input_data

    def to_dict(self) -> dict[str, Any]:
        kind_value = self.kind.value if isinstance(self.kind, SpanKind) else str(self.kind)
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "kind": kind_value,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "input": self.input,
            "output": self.output,
            "model": self.model,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "cost_usd": self.cost_usd,
            "error": self.error,
        }


@dataclass
class Trace:
    agent_name: Optional[str] = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: TraceStatus = TraceStatus.RUNNING
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0
    metadata: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    spans: list[Span] = field(default_factory=list)

    def end(self, status: TraceStatus = TraceStatus.SUCCESS, error: Optional[str] = None) -> None:
        self.ended_at = time.time()
        self.status = status
        if error:
            self.error = error
        for span in self.spans:
            self.total_tokens_in += span.tokens_in or 0
            self.total_tokens_out += span.tokens_out or 0
            self.total_cost_usd += span.cost_usd or 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "total_cost_usd": self.total_cost_usd,
            "metadata": self.metadata,
            "error": self.error,
        }


# Model pricing in USD per 1K tokens
MODEL_COSTS: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-20241022": {"input": 0.0008, "output": 0.004},
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
}


def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Calculate cost for a model call. Returns 0.0 if model is unknown."""
    # Try exact match first, then prefix match
    costs = MODEL_COSTS.get(model)
    if not costs:
        for key, value in MODEL_COSTS.items():
            if model.startswith(key) or key.startswith(model):
                costs = value
                break
    if not costs:
        return 0.0
    return (tokens_in * costs["input"] + tokens_out * costs["output"]) / 1000
