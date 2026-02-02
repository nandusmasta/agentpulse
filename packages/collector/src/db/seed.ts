/**
 * Seed script: creates sample data for development.
 * Run with: bun run src/db/seed.ts
 */
import { getDb } from "./schema";

const db = getDb();

// Ensure default project
const project = db
  .prepare("SELECT id FROM projects WHERE api_key = ?")
  .get("ap_dev_default") as { id: string } | null;

const projectId = project?.id || "default";

// Insert sample traces
const now = Date.now() / 1000;

const traces = [
  {
    id: "trace_sample_1",
    agent_name: "research-agent",
    status: "success",
    started_at: now - 120,
    ended_at: now - 115,
    total_tokens_in: 1500,
    total_tokens_out: 800,
    total_cost_usd: 0.012,
  },
  {
    id: "trace_sample_2",
    agent_name: "coding-agent",
    status: "success",
    started_at: now - 60,
    ended_at: now - 50,
    total_tokens_in: 3200,
    total_tokens_out: 1500,
    total_cost_usd: 0.023,
  },
  {
    id: "trace_sample_3",
    agent_name: "research-agent",
    status: "error",
    started_at: now - 30,
    ended_at: now - 28,
    total_tokens_in: 500,
    total_tokens_out: 0,
    total_cost_usd: 0.001,
  },
];

const insertTrace = db.prepare(`
  INSERT OR IGNORE INTO traces (id, project_id, agent_name, status, started_at, ended_at, total_tokens_in, total_tokens_out, total_cost_usd)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

for (const t of traces) {
  insertTrace.run(
    t.id,
    projectId,
    t.agent_name,
    t.status,
    t.started_at,
    t.ended_at,
    t.total_tokens_in,
    t.total_tokens_out,
    t.total_cost_usd
  );
}

// Insert sample spans
const spans = [
  {
    id: "span_1_1",
    trace_id: "trace_sample_1",
    name: "openai.gpt-4o",
    kind: "llm",
    started_at: now - 120,
    ended_at: now - 118,
    model: "gpt-4o",
    tokens_in: 1000,
    tokens_out: 500,
    cost_usd: 0.0075,
  },
  {
    id: "span_1_2",
    trace_id: "trace_sample_1",
    parent_span_id: null,
    name: "web_search",
    kind: "tool",
    started_at: now - 118,
    ended_at: now - 116,
    model: null,
    tokens_in: null,
    tokens_out: null,
    cost_usd: null,
  },
  {
    id: "span_1_3",
    trace_id: "trace_sample_1",
    name: "openai.gpt-4o",
    kind: "llm",
    started_at: now - 116,
    ended_at: now - 115,
    model: "gpt-4o",
    tokens_in: 500,
    tokens_out: 300,
    cost_usd: 0.0045,
  },
  {
    id: "span_2_1",
    trace_id: "trace_sample_2",
    name: "openai.gpt-4o",
    kind: "llm",
    started_at: now - 60,
    ended_at: now - 55,
    model: "gpt-4o",
    tokens_in: 3200,
    tokens_out: 1500,
    cost_usd: 0.023,
  },
];

const insertSpan = db.prepare(`
  INSERT OR IGNORE INTO spans (id, trace_id, parent_span_id, name, kind, started_at, ended_at, model, tokens_in, tokens_out, cost_usd)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

for (const s of spans) {
  insertSpan.run(
    s.id,
    s.trace_id,
    null,
    s.name,
    s.kind,
    s.started_at,
    s.ended_at,
    s.model,
    s.tokens_in,
    s.tokens_out,
    s.cost_usd
  );
}

console.log("Seeded database with sample data.");
