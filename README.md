[![PyPI](https://img.shields.io/pypi/v/agentpulse)](https://pypi.org/project/agentpulse-ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

# AgentPulse

Lightweight, framework-agnostic observability for AI agents. Track costs, tokens, traces, and latency across OpenAI, Anthropic, and any custom tooling — with a self-hostable dashboard.

## Quick Start

```bash
pip install agentpulse-ai
```

```python
from agentpulse import AgentPulse, trace, tool

ap = AgentPulse(endpoint="http://localhost:3000", api_key="ap_dev_default")

@tool
def search(query: str) -> str:
    return f"Results for {query}"

@trace(name="research-agent")
def run_agent(topic: str):
    result = search(topic)
    return result

run_agent("quantum computing")
ap.shutdown()
```

Traces, spans, token counts, and costs are sent to the collector and visible in the dashboard.

## Features

- **Decorator-based tracing** — `@trace` and `@tool` decorators with zero boilerplate
- **Auto-patching for LLMs** — automatic instrumentation for OpenAI and Anthropic clients
- **Cost tracking** — per-call and aggregate cost calculation for 9+ models
- **Span tree visualization** — hierarchical trace view in the dashboard
- **Self-hostable** — single `docker-compose up` with SQLite storage
- **Zero dependencies** — the SDK uses only the Python standard library
- **Async support** — works with both sync and async code
- **Batch transport** — low-overhead background flushing

## Auto-Instrumentation

Patch OpenAI or Anthropic clients to automatically capture every LLM call:

```python
from openai import OpenAI
from agentpulse import AgentPulse

ap = AgentPulse(api_key="ap_dev_default")
client = OpenAI()
ap.patch_openai(client)

# All chat completion calls are now traced automatically
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
```

## Self-Hosting

Clone the repository and start the stack:

```bash
git clone https://github.com/your-org/agentpulse.git
cd agentpulse
docker-compose up -d
```

This starts:
- **Collector** on port 3000 — ingests traces and spans
- **Dashboard** on port 5173 — web UI for exploring traces and costs

See [docs/self-hosting.md](docs/self-hosting.md) for configuration options.

## Architecture

```
SDK (Python) → Collector API → SQLite → Dashboard
```

| Component | Tech | Port |
|-----------|------|------|
| SDK | Python 3.10+ | — |
| Collector | Bun + Hono | 3000 |
| Dashboard | SvelteKit | 5173 |

## Documentation

- [Quick Start](docs/quickstart.md)
- [Self-Hosting Guide](docs/self-hosting.md)
- [SDK Reference](docs/sdk-reference.md)
- [Examples](examples/)
- [Contributing](CONTRIBUTING.md)

## Community

Join us on Discord: https://discord.gg/tdnP9NWURy

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT](LICENSE)
