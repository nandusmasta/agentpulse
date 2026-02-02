"""Auto-patching for Anthropic client to track LLM calls."""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..client import AgentPulse

from ..context import restore_span, set_current_span
from ..models import SpanKind, calculate_cost

logger = logging.getLogger("agentpulse")


def patch_anthropic(ap: AgentPulse, client: Optional[Any] = None) -> Optional[Any]:
    """Patch Anthropic client(s) for automatic span creation."""
    try:
        import anthropic
    except ImportError:
        logger.warning("AgentPulse: anthropic package not installed, skipping patch")
        return client

    if client is not None:
        _patch_client_instance(ap, client)
        return client

    _patch_module(ap, anthropic)
    return None


def _patch_client_instance(ap: AgentPulse, client: Any) -> None:
    if hasattr(client, "messages"):
        _wrap_messages(ap, client.messages)


def _patch_module(ap: AgentPulse, anthropic_module: Any) -> None:
    original_init = anthropic_module.Anthropic.__init__
    original_async_init = anthropic_module.AsyncAnthropic.__init__

    @functools.wraps(original_init)
    def patched_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        _patch_client_instance(ap, self)

    @functools.wraps(original_async_init)
    def patched_async_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_async_init(self, *args, **kwargs)
        _patch_client_instance(ap, self)

    anthropic_module.Anthropic.__init__ = patched_init
    anthropic_module.AsyncAnthropic.__init__ = patched_async_init


def _wrap_messages(ap: AgentPulse, messages_resource: Any) -> None:
    if not hasattr(messages_resource, "create"):
        return

    original_create = messages_resource.create
    is_async = asyncio.iscoroutinefunction(original_create)

    if is_async:
        @functools.wraps(original_create)
        async def traced_create(*args: Any, **kwargs: Any) -> Any:
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages")
            span = ap.start_span(
                name=f"anthropic.{model}",
                kind=SpanKind.LLM,
                input_data=_safe_serialize_messages(messages),
            )
            span.model = model
            span_token = set_current_span(span)
            try:
                response = await original_create(*args, **kwargs)
                _extract_usage(span, response)
                return response
            except Exception as exc:
                span.end(error=str(exc))
                raise
            finally:
                restore_span(span_token)
    else:
        @functools.wraps(original_create)
        def traced_create(*args: Any, **kwargs: Any) -> Any:
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages")
            span = ap.start_span(
                name=f"anthropic.{model}",
                kind=SpanKind.LLM,
                input_data=_safe_serialize_messages(messages),
            )
            span.model = model
            span_token = set_current_span(span)
            try:
                response = original_create(*args, **kwargs)
                _extract_usage(span, response)
                return response
            except Exception as exc:
                span.end(error=str(exc))
                raise
            finally:
                restore_span(span_token)

    messages_resource.create = traced_create


def _extract_usage(span: Any, response: Any) -> None:
    usage = getattr(response, "usage", None)
    if usage:
        span.tokens_in = getattr(usage, "input_tokens", 0)
        span.tokens_out = getattr(usage, "output_tokens", 0)
        if span.model:
            span.cost_usd = calculate_cost(span.model, span.tokens_in, span.tokens_out)

    # Extract output text
    content = getattr(response, "content", None)
    if content and isinstance(content, list) and len(content) > 0:
        first_block = content[0]
        text = getattr(first_block, "text", None)
        if text:
            span.set_output(text[:1000] if len(text) > 1000 else text)

    span.end()


def _safe_serialize_messages(messages: Any) -> Any:
    if messages is None:
        return None
    if not isinstance(messages, list):
        return str(messages)[:1000]

    result = []
    for msg in messages:
        if isinstance(msg, dict):
            serialized = {**msg}
            if "content" in serialized and isinstance(serialized["content"], str):
                if len(serialized["content"]) > 500:
                    serialized["content"] = serialized["content"][:500] + "...[truncated]"
            result.append(serialized)
        else:
            result.append(str(msg)[:500])
    return result
