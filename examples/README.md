# AgentPulse Examples

## Prerequisites

Install the SDK:

```bash
pip install agentpulse
```

Start the collector and dashboard:

```bash
docker-compose up -d
```

## Examples

### basic.py

Traces an agent with tool calls, no LLM required. Shows how `@trace` and `@tool` decorators work.

```bash
python examples/basic.py
```

### openai_example.py

Auto-instruments OpenAI calls with `patch_openai`. Captures tokens, cost, and model info automatically.

```bash
export OPENAI_API_KEY=sk-...
python examples/openai_example.py
```

After running any example, open [http://localhost:5173](http://localhost:5173) to see traces in the dashboard.
