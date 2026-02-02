# Quick Start

## Install the SDK

```bash
pip install agentpulse
```

For OpenAI auto-instrumentation:

```bash
pip install agentpulse[openai]
```

For Anthropic:

```bash
pip install agentpulse[anthropic]
```

## Start the Collector

The simplest way is with Docker Compose:

```bash
git clone https://github.com/your-org/agentpulse.git
cd agentpulse
docker-compose up -d
```

This starts the collector on port 3000 and the dashboard on port 5173.

## Initialize the Client

```python
from agentpulse import AgentPulse

ap = AgentPulse(
    endpoint="http://localhost:3000",
    api_key="ap_dev_default",
)
```

## Trace an Agent

Use the `@trace` decorator on your top-level agent function:

```python
from agentpulse import trace, tool

@tool
def search(query: str) -> str:
    return f"Results for {query}"

@trace(name="my-agent")
def run(topic: str) -> str:
    return search(topic)

run("AI safety")
ap.shutdown()
```

## Auto-Instrument LLM Calls

Patch OpenAI to automatically capture every API call:

```python
from openai import OpenAI
from agentpulse import AgentPulse

ap = AgentPulse(api_key="ap_dev_default")
client = OpenAI()
ap.patch_openai(client)

# All completions calls are now traced
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
```

## View Traces

Open [http://localhost:5173](http://localhost:5173) to see the dashboard with your traces, costs, and token usage.

## Next Steps

- [Self-Hosting Guide](self-hosting.md) — configuration and deployment options
- [SDK Reference](sdk-reference.md) — full API documentation
- [Examples](../examples/) — runnable code samples
