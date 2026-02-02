"""Auto-patching for OpenAI client to track LLM calls."""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..client import AgentPulse

from ..context import get_current_span, restore_span, set_current_span
from ..models import SpanKind, calculate_cost

logger = logging.getLogger("agentpulse")


def patch_openai(ap: AgentPulse, client: Optional[Any] = None) -> Optional[Any]:
    """Patch OpenAI client(s) for automatic span creation.

    If `client` is provided, wraps that specific instance and returns it.
    If `client` is None, monkey-patches the openai module globally.
    """
    try:
        import openai
    except ImportError:
        logger.warning("AgentPulse: openai package not installed, skipping patch")
        return client

    if client is not None:
        _patch_client_instance(ap, client)
        return client

    # Global patch: wrap the default clients
    _patch_module(ap, openai)
    return None


def _patch_client_instance(ap: AgentPulse, client: Any) -> None:
    """Patch a specific OpenAI client instance."""
    if hasattr(client, "chat") and hasattr(client.chat, "completions"):
        _wrap_completions(ap, client.chat.completions)
    if hasattr(client, "completions"):
        _wrap_completions(ap, client.completions)


def _patch_module(ap: AgentPulse, openai_module: Any) -> None:
    """Monkey-patch the openai module to wrap new client instances."""
    original_init = openai_module.OpenAI.__init__
    original_async_init = openai_module.AsyncOpenAI.__init__

    @functools.wraps(original_init)
    def patched_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        _patch_client_instance(ap, self)

    @functools.wraps(original_async_init)
    def patched_async_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_async_init(self, *args, **kwargs)
        _patch_client_instance(ap, self)

    openai_module.OpenAI.__init__ = patched_init
    openai_module.AsyncOpenAI.__init__ = patched_async_init


def _wrap_completions(ap: AgentPulse, completions: Any) -> None:
    """Wrap the create method on a completions resource."""
    if not hasattr(completions, "create"):
        return

    original_create = completions.create
    is_async = asyncio.iscoroutinefunction(original_create)

    if is_async:
        @functools.wraps(original_create)
        async def traced_create(*args: Any, **kwargs: Any) -> Any:
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages")
            span = ap.start_span(
                name=f"openai.{model}",
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
                name=f"openai.{model}",
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

    completions.create = traced_create


def _extract_usage(span: Any, response: Any) -> None:
    """Extract token usage and cost from an OpenAI response."""
    usage = getattr(response, "usage", None)
    if usage:
        span.tokens_in = getattr(usage, "prompt_tokens", 0)
        span.tokens_out = getattr(usage, "completion_tokens", 0)
        if span.model:
            span.cost_usd = calculate_cost(span.model, span.tokens_in, span.tokens_out)

    # Extract output text
    choices = getattr(response, "choices", None)
    if choices and len(choices) > 0:
        message = getattr(choices[0], "message", None)
        if message:
            span.set_output(getattr(message, "content", None))

    span.end()


def _safe_serialize_messages(messages: Any) -> Any:
    """Safely serialize messages for storage, truncating large content."""
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
