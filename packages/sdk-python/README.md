# AgentPulse

Lightweight, framework-agnostic observability for AI agents. Track costs, tokens, traces, and latency across OpenAI, Anthropic, and any custom tooling.

## Install

```bash
pip install agentpulse-ai
```

## Quick Start

```python
from agentpulse import AgentPulse, trace, tool

ap = AgentPulse(endpoint="http://localhost:3000", api_key="ap_dev_default")

@tool
def search(query: str) -> str:
    return f"Results for {query}"

@trace(name="research-agent")
def run_agent(topic: str) -> str:
    return search(topic)

run_agent("quantum computing")
ap.shutdown()
```

## Documentation

See the [full documentation](https://github.com/nandusmasta/agentpulse/tree/main/docs).
