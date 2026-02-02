"""Decorators for tracing agent functions and tools."""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import Any, Callable, Optional, TypeVar, overload

from .context import (
    get_current_span,
    get_current_trace,
    restore_span,
    restore_trace,
    set_current_span,
    set_current_trace,
)
from .models import Span, SpanKind, Trace, TraceStatus

logger = logging.getLogger("agentpulse")

F = TypeVar("F", bound=Callable[..., Any])


@overload
def trace(fn: F) -> F: ...


@overload
def trace(*, name: Optional[str] = None, metadata: Optional[dict[str, Any]] = None) -> Callable[[F], F]: ...


@overload
def trace(name: str) -> Callable[[F], F]: ...


def trace(
    fn: Optional[F] = None,
    *,
    name: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Any:
    """Decorator to trace an agent function.

    Creates a new trace (if none active) or a child span.

    Usage:
        @trace
        def my_agent(): ...

        @trace(name="research-agent")
        async def research(topic): ...
    """
    # Handle @trace("name") syntax — first positional arg is a string
    if fn is not None and isinstance(fn, str):
        return trace(name=fn)

    def decorator(func: F) -> F:
        trace_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await _run_traced(func, trace_name, metadata, args, kwargs, is_async=True)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return _run_traced(func, trace_name, metadata, args, kwargs, is_async=False)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper  # type: ignore[return-value]

    if fn is not None and callable(fn):
        return decorator(fn)
    return decorator


def _run_traced(
    func: Callable[..., Any],
    trace_name: str,
    metadata: Optional[dict[str, Any]],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    *,
    is_async: bool,
) -> Any:
    from .client import get_client

    client = get_client()
    existing_trace = get_current_trace()

    if existing_trace:
        # Nested: create a child span instead of a new trace
        span = Span(
            name=trace_name,
            kind=SpanKind.CUSTOM,
            trace_id=existing_trace.id,
            parent_span_id=(get_current_span() or Span(name="", kind=SpanKind.CUSTOM, trace_id="")).id
            if get_current_span()
            else None,
        )
        existing_trace.spans.append(span)
        span_token = set_current_span(span)

        if is_async:
            return _async_span_exec(func, span, span_token, args, kwargs)
        return _sync_span_exec(func, span, span_token, args, kwargs)

    # Top-level: create a new trace
    trace_obj = Trace(agent_name=trace_name, metadata=metadata)
    trace_token = set_current_trace(trace_obj)
    span_token = set_current_span(None)

    if is_async:
        return _async_trace_exec(func, trace_obj, trace_token, span_token, client, args, kwargs)
    return _sync_trace_exec(func, trace_obj, trace_token, span_token, client, args, kwargs)


def _sync_span_exec(
    func: Callable[..., Any],
    span: Span,
    span_token: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    try:
        result = func(*args, **kwargs)
        span.end()
        return result
    except Exception as exc:
        span.end(error=str(exc))
        raise
    finally:
        restore_span(span_token)


async def _async_span_exec(
    func: Callable[..., Any],
    span: Span,
    span_token: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    try:
        result = await func(*args, **kwargs)
        span.end()
        return result
    except Exception as exc:
        span.end(error=str(exc))
        raise
    finally:
        restore_span(span_token)


def _sync_trace_exec(
    func: Callable[..., Any],
    trace_obj: Trace,
    trace_token: Any,
    span_token: Any,
    client: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    try:
        result = func(*args, **kwargs)
        if client:
            client.end_trace(trace_obj, TraceStatus.SUCCESS)
        else:
            trace_obj.end(TraceStatus.SUCCESS)
        return result
    except Exception as exc:
        if client:
            client.end_trace(trace_obj, TraceStatus.ERROR, error=str(exc))
        else:
            trace_obj.end(TraceStatus.ERROR, error=str(exc))
        raise
    finally:
        restore_trace(trace_token)
        restore_span(span_token)


async def _async_trace_exec(
    func: Callable[..., Any],
    trace_obj: Trace,
    trace_token: Any,
    span_token: Any,
    client: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    try:
        result = await func(*args, **kwargs)
        if client:
            client.end_trace(trace_obj, TraceStatus.SUCCESS)
        else:
            trace_obj.end(TraceStatus.SUCCESS)
        return result
    except Exception as exc:
        if client:
            client.end_trace(trace_obj, TraceStatus.ERROR, error=str(exc))
        else:
            trace_obj.end(TraceStatus.ERROR, error=str(exc))
        raise
    finally:
        restore_trace(trace_token)
        restore_span(span_token)


@overload
def tool(fn: F) -> F: ...


@overload
def tool(*, name: Optional[str] = None) -> Callable[[F], F]: ...


@overload
def tool(name: str) -> Callable[[F], F]: ...


def tool(
    fn: Optional[F] = None,
    *,
    name: Optional[str] = None,
) -> Any:
    """Decorator to trace a tool function.

    Usage:
        @tool
        def search(query): ...

        @tool(name="web-search")
        async def search(query): ...
    """
    if fn is not None and isinstance(fn, str):
        return tool(name=fn)

    def decorator(func: F) -> F:
        tool_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            from .client import get_client
            client = get_client()
            if not client:
                return await func(*args, **kwargs)
            span = client.start_span(tool_name, SpanKind.TOOL)
            span_token = set_current_span(span)
            try:
                result = await func(*args, **kwargs)
                span.end()
                return result
            except Exception as exc:
                span.end(error=str(exc))
                raise
            finally:
                restore_span(span_token)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            from .client import get_client
            client = get_client()
            if not client:
                return func(*args, **kwargs)
            span = client.start_span(tool_name, SpanKind.TOOL)
            span_token = set_current_span(span)
            try:
                result = func(*args, **kwargs)
                span.end()
                return result
            except Exception as exc:
                span.end(error=str(exc))
                raise
            finally:
                restore_span(span_token)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper  # type: ignore[return-value]

    if fn is not None and callable(fn):
        return decorator(fn)
    return decorator
