# AgentPulse - AI Agent Observability Platform

## Overview
AgentPulse is a lightweight, framework-agnostic observability tool for AI agents. It tracks what agents do, how much they cost, and helps developers debug issues.

**Key differentiators:**
- Works with ANY agent framework (not tied to LangChain)
- Self-host option (privacy-first)
- Cost-focused (the thing developers actually worry about)
- Simple setup (one-line integration)

## Architecture

```
SDK (Python/TS) → Collector API → SQLite/Postgres → Dashboard
```

## MVP Scope (4 weeks)

### Week 1: Python SDK + Collector

**Python SDK (`agentpulse` package):**
- `AgentPulse` client class with `api_key` or `endpoint` for self-host
- `@trace(name="agent-name")` decorator for agent functions
- `@tool(name="tool-name")` decorator for tool functions
- Context manager: `with ap.span("custom-span"):`
- Auto-patching for OpenAI and Anthropic clients
- Async support
- Zero required dependencies (optional `openai`/`anthropic` for auto-patch)

**Collector Service (Hono + Bun):**
- `POST /v1/traces` - ingest trace data
- `POST /v1/spans` - ingest span data  
- `GET /v1/health` - health check
- API key validation via header `X-AgentPulse-Key`
- SQLite storage (file-based for self-host)

### Week 2: Dashboard Core

**Tech: SvelteKit**

**Pages:**
- `/` - Dashboard overview (stats cards, recent traces)
- `/traces` - Trace list with filters
- `/traces/[id]` - Trace detail (tree view of spans)
- `/settings` - API keys, project config

**Components:**
- Trace timeline visualization
- Span tree (expandable/collapsible)
- Cost breakdown chart
- Latency histogram

### Week 3: Cost Intelligence

**Cost calculation:**
- Map model names to $/1k tokens (input/output separate)
- Support: OpenAI (gpt-4, gpt-4o, gpt-3.5), Anthropic (claude-3, claude-3.5, opus, sonnet, haiku), OpenRouter models
- Store cost per span, aggregate to trace level

**Features:**
- Cost per trace, per agent, per day
- Daily/weekly cost trends chart
- Budget alerts (webhook + email)
- Cost anomaly detection (spike alerts)

### Week 4: Polish + Deploy

**Self-host package:**
- Docker Compose with collector + dashboard + SQLite
- Single `docker-compose up` to run
- Environment config via `.env`

**Cloud hosting:**
- Deploy to Fly.io
- Turso for managed SQLite
- Landing page at agentpulse.dev (or similar)

**TypeScript SDK:**
- Mirror Python SDK functionality
- ESM + CommonJS builds
- Zero dependencies

## Data Model

```sql
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  api_key TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE traces (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  agent_name TEXT,
  status TEXT DEFAULT 'running', -- running/success/error
  started_at TIMESTAMP NOT NULL,
  ended_at TIMESTAMP,
  total_tokens_in INTEGER DEFAULT 0,
  total_tokens_out INTEGER DEFAULT 0,
  total_cost_usd REAL DEFAULT 0,
  metadata JSON,
  error TEXT,
  FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE spans (
  id TEXT PRIMARY KEY,
  trace_id TEXT NOT NULL,
  parent_span_id TEXT,
  name TEXT NOT NULL,
  kind TEXT NOT NULL, -- llm/tool/custom
  started_at TIMESTAMP NOT NULL,
  ended_at TIMESTAMP,
  input JSON,
  output JSON,
  model TEXT,
  tokens_in INTEGER,
  tokens_out INTEGER,
  cost_usd REAL,
  error TEXT,
  FOREIGN KEY (trace_id) REFERENCES traces(id),
  FOREIGN KEY (parent_span_id) REFERENCES spans(id)
);

CREATE TABLE alerts (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  name TEXT NOT NULL,
  type TEXT NOT NULL, -- cost_threshold/error_rate/latency
  threshold REAL NOT NULL,
  window_minutes INTEGER DEFAULT 60,
  webhook_url TEXT,
  email TEXT,
  enabled BOOLEAN DEFAULT true,
  last_triggered_at TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_traces_project ON traces(project_id);
CREATE INDEX idx_traces_started ON traces(started_at);
CREATE INDEX idx_spans_trace ON spans(trace_id);
CREATE INDEX idx_spans_started ON spans(started_at);
```

## SDK Usage Examples

### Python

```python
from agentpulse import AgentPulse, trace, tool
import openai

# Initialize (cloud)
ap = AgentPulse(api_key="ap_xxxxx")

# Or self-hosted
ap = AgentPulse(endpoint="http://localhost:3000")

# Auto-patch OpenAI (optional)
ap.patch_openai()

@trace(name="research-agent")
async def research(topic: str):
    # LLM calls auto-tracked
    response = await openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Research: {topic}"}]
    )
    
    # Track tool usage
    with ap.tool("web_search") as t:
        results = await search_web(topic)
        t.set_output({"results": len(results)})
    
    return response.choices[0].message.content

# Run it - traces appear in dashboard
await research("quantum computing")
```

### TypeScript

```typescript
import { AgentPulse, trace, tool } from 'agentpulse';
import OpenAI from 'openai';

const ap = new AgentPulse({ apiKey: 'ap_xxxxx' });
const openai = ap.patchOpenAI(new OpenAI());

const research = trace('research-agent', async (topic: string) => {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [{ role: 'user', content: `Research: ${topic}` }]
  });
  
  const results = await ap.tool('web_search', async () => {
    return await searchWeb(topic);
  });
  
  return response.choices[0].message.content;
});

await research('quantum computing');
```

## File Structure

```
agentpulse/
├── packages/
│   ├── sdk-python/
│   │   ├── agentpulse/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   ├── decorators.py
│   │   │   ├── context.py
│   │   │   ├── patches/
│   │   │   │   ├── openai.py
│   │   │   │   └── anthropic.py
│   │   │   └── models.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── sdk-typescript/
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── client.ts
│   │   │   ├── decorators.ts
│   │   │   └── patches/
│   │   │       └── openai.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── collector/
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── routes/
│   │   │   ├── db/
│   │   │   └── services/
│   │   ├── package.json
│   │   └── Dockerfile
│   │
│   └── dashboard/
│       ├── src/
│       │   ├── routes/
│       │   ├── lib/
│       │   └── components/
│       ├── package.json
│       └── Dockerfile
│
├── docker-compose.yml
├── README.md
└── LICENSE (MIT)
```

## Model Cost Reference (USD per 1K tokens)

```json
{
  "gpt-4o": { "input": 0.0025, "output": 0.01 },
  "gpt-4o-mini": { "input": 0.00015, "output": 0.0006 },
  "gpt-4-turbo": { "input": 0.01, "output": 0.03 },
  "gpt-3.5-turbo": { "input": 0.0005, "output": 0.0015 },
  "claude-3-5-sonnet-20241022": { "input": 0.003, "output": 0.015 },
  "claude-3-5-haiku-20241022": { "input": 0.0008, "output": 0.004 },
  "claude-3-opus-20240229": { "input": 0.015, "output": 0.075 },
  "claude-3-sonnet-20240229": { "input": 0.003, "output": 0.015 },
  "claude-3-haiku-20240307": { "input": 0.00025, "output": 0.00125 }
}
```

## Priority Order

1. **Python SDK** - most AI devs use Python
2. **Collector** - needed to receive data
3. **Dashboard** - needed to view data
4. **Cost calculation** - key differentiator
5. **Docker setup** - self-host story
6. **TypeScript SDK** - expand reach
7. **Alerts** - nice to have for MVP

## Success Criteria

- [ ] Can install SDK with `pip install agentpulse`
- [ ] One decorator traces an entire agent run
- [ ] Dashboard shows trace tree with timing
- [ ] Cost displayed per trace and aggregated
- [ ] Self-host works with `docker-compose up`
- [ ] < 5ms overhead per traced call
