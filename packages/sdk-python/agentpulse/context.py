"""Trace context management using contextvars for async safety."""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .models import Span, Trace

_current_trace: ContextVar[Optional[Trace]] = ContextVar("agentpulse_trace", default=None)
_current_span: ContextVar[Optional[Span]] = ContextVar("agentpulse_span", default=None)


def get_current_trace() -> Optional[Trace]:
    return _current_trace.get()


def set_current_trace(trace: Optional[Trace]) -> Token[Optional[Trace]]:
    return _current_trace.set(trace)


def restore_trace(token: Token[Optional[Trace]]) -> None:
    _current_trace.reset(token)


def get_current_span() -> Optional[Span]:
    return _current_span.get()


def set_current_span(span: Optional[Span]) -> Token[Optional[Span]]:
    return _current_span.set(span)


def restore_span(token: Token[Optional[Span]]) -> None:
    _current_span.reset(token)
