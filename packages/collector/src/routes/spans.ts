import { Hono } from "hono";
import { getDb } from "../db/schema";
import { authMiddleware } from "../services/auth";

const spans = new Hono();

// Ingest spans (batch)
spans.post("/", authMiddleware, async (c) => {
  const body = await c.req.json();
  const items = Array.isArray(body) ? body : [body];
  const db = getDb();

  const insert = db.prepare(`
    INSERT OR REPLACE INTO spans
      (id, trace_id, parent_span_id, name, kind, started_at, ended_at,
       input, output, model, tokens_in, tokens_out, cost_usd, error)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const insertMany = db.transaction(() => {
    for (const s of items) {
      insert.run(
        s.id,
        s.trace_id,
        s.parent_span_id || null,
        s.name,
        s.kind,
        s.started_at,
        s.ended_at || null,
        s.input ? JSON.stringify(s.input) : null,
        s.output ? JSON.stringify(s.output) : null,
        s.model || null,
        s.tokens_in || null,
        s.tokens_out || null,
        s.cost_usd || null,
        s.error || null
      );
    }
  });

  insertMany();
  return c.json({ ingested: items.length }, 201);
});

export default spans;
