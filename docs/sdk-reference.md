# SDK Reference

## Installation

```bash
pip install agentpulse-ai
```

## AgentPulse Client

### `AgentPulse(api_key, endpoint, flush_interval, batch_size, enabled)`

Main client. Initializing sets the global client used by decorators.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str \| None` | `None` | Project API key |
| `endpoint` | `str` | `http://localhost:3000` | Collector URL |
| `flush_interval` | `float` | `2.0` | Seconds between batch flushes |
| `batch_size` | `int` | `50` | Max items per flush |
| `enabled` | `bool` | `True` | Set `False` to disable all tracing |

```python
from agentpulse import AgentPulse

ap = AgentPulse(endpoint="http://localhost:3000", api_key="ap_dev_default")
```

### `ap.start_trace(agent_name, metadata) -> Trace`

Manually create a trace.

### `ap.end_trace(trace, status, error)`

End a trace and flush it to the collector.

### `ap.span(name, kind) -> ContextManager[Span]`

Context manager for creating a span within the current trace.

```python
with ap.span("my-step") as span:
    result = do_work()
    span.set_output(result)
```

### `ap.tool(name) -> ContextManager[Span]`

Context manager for a tool span (shorthand for `span` with `kind=TOOL`).

### `ap.patch_openai(client=None)`

Patch an OpenAI client instance (or the module globally if no client is passed) to auto-trace all completion calls.

```python
from openai import OpenAI
client = OpenAI()
ap.patch_openai(client)
```

### `ap.patch_anthropic(client=None)`

Same as `patch_openai` but for Anthropic clients.

### `ap.flush()`

Force flush all pending traces and spans.

### `ap.shutdown()`

Flush and close the transport. Call this before your process exits.

## Decorators

### `@trace`

Traces a function as an agent run. Creates a new trace if none is active, or a child span if called within an existing trace.

```python
from agentpulse import trace

@trace
def my_agent():
    pass

@trace(name="custom-name", metadata={"version": "2"})
def another_agent():
    pass
```

Works with both sync and async functions.

### `@tool`

Traces a function as a tool call. Creates a span with `kind=TOOL`.

```python
from agentpulse import tool

@tool
def search(query: str) -> str:
    return results

@tool(name="web-search")
def search_web(query: str) -> str:
    return results
```

## Models

### `SpanKind`

Enum: `LLM`, `TOOL`, `CUSTOM`

### `TraceStatus`

Enum: `RUNNING`, `SUCCESS`, `ERROR`

### `Span`

Dataclass representing a unit of work within a trace.

Key fields: `id`, `trace_id`, `parent_span_id`, `name`, `kind`, `model`, `tokens_in`, `tokens_out`, `cost_usd`, `started_at`, `ended_at`, `error`

Methods:
- `span.set_input(data)` — attach input data
- `span.set_output(data)` — attach output data
- `span.end(error=None)` — mark the span as complete

### `Trace`

Dataclass representing a full agent execution.

Key fields: `id`, `agent_name`, `status`, `metadata`, `spans`, `started_at`, `ended_at`, `error`

### `calculate_cost(model, tokens_in, tokens_out) -> float`

Calculate the USD cost for a given model and token counts. Supports GPT-4, GPT-4o, GPT-3.5, Claude 3 Opus/Sonnet/Haiku, and more.

### `get_client() -> AgentPulse | None`

Returns the current global AgentPulse client, or `None` if not initialized.
