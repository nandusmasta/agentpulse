"""AgentPulse client - the main entry point for the SDK."""

from __future__ import annotations

import atexit
import logging
from contextlib import contextmanager
from typing import Any, Generator, Optional

from .context import (
    get_current_span,
    get_current_trace,
    restore_span,
    set_current_span,
)
from .models import Span, SpanKind, Trace, TraceStatus
from .transport import Transport

logger = logging.getLogger("agentpulse")

_global_client: Optional[AgentPulse] = None


def get_client() -> Optional[AgentPulse]:
    return _global_client


class AgentPulse:
    """AgentPulse observability client.

    Usage:
        # Cloud
        ap = AgentPulse(api_key="ap_xxxxx")

        # Self-hosted
        ap = AgentPulse(endpoint="http://localhost:3000")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: str = "http://localhost:3000",
        flush_interval: float = 2.0,
        batch_size: int = 50,
        enabled: bool = True,
    ) -> None:
        global _global_client

        self.api_key = api_key
        self.endpoint = endpoint
        self.enabled = enabled
        self._transport: Optional[Transport] = None

        if enabled:
            self._transport = Transport(
                endpoint=endpoint,
                api_key=api_key,
                flush_interval=flush_interval,
                batch_size=batch_size,
            )
            atexit.register(self.shutdown)

        _global_client = self

    def start_trace(
        self,
        agent_name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Trace:
        trace = Trace(agent_name=agent_name, metadata=metadata)
        return trace

    def end_trace(
        self,
        trace: Trace,
        status: TraceStatus = TraceStatus.SUCCESS,
        error: Optional[str] = None,
    ) -> None:
        trace.end(status=status, error=error)
        if self._transport and self.enabled:
            self._transport.send_trace(trace.to_dict())
            for span in trace.spans:
                self._transport.send_span(span.to_dict())

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.CUSTOM,
        input_data: Optional[Any] = None,
    ) -> Span:
        trace = get_current_trace()
        if not trace:
            logger.debug("AgentPulse: no active trace for span '%s'", name)
            # Create an orphan span with empty trace_id
            span = Span(name=name, kind=kind, trace_id="")
            if input_data is not None:
                span.set_input(input_data)
            return span

        parent = get_current_span()
        span = Span(
            name=name,
            kind=kind,
            trace_id=trace.id,
            parent_span_id=parent.id if parent else None,
        )
        if input_data is not None:
            span.set_input(input_data)
        trace.spans.append(span)
        return span

    @contextmanager
    def span(self, name: str, kind: SpanKind = SpanKind.CUSTOM) -> Generator[Span, None, None]:
        """Context manager for creating a custom span."""
        span = self.start_span(name, kind)
        token = set_current_span(span)
        try:
            yield span
        except Exception as exc:
            span.end(error=str(exc))
            raise
        else:
            span.end()
        finally:
            restore_span(token)

    @contextmanager
    def tool(self, name: str) -> Generator[Span, None, None]:
        """Context manager for tracking tool usage."""
        with self.span(name, kind=SpanKind.TOOL) as span:
            yield span

    def patch_openai(self, client: Optional[Any] = None) -> Optional[Any]:
        """Patch OpenAI client for automatic LLM call tracking.

        If a client instance is passed, patches and returns that instance.
        If no client is passed, patches the openai module globally.
        """
        from .patches.openai import patch_openai
        return patch_openai(self, client)

    def patch_anthropic(self, client: Optional[Any] = None) -> Optional[Any]:
        """Patch Anthropic client for automatic LLM call tracking."""
        from .patches.anthropic import patch_anthropic
        return patch_anthropic(self, client)

    def flush(self) -> None:
        if self._transport:
            self._transport.flush()

    def shutdown(self) -> None:
        if self._transport:
            self._transport.close()
