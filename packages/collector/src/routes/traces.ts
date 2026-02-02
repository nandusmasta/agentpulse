import { Hono } from "hono";
import { getDb } from "../db/schema";
import { authMiddleware } from "../services/auth";

const traces = new Hono();

// Ingest traces (batch)
traces.post("/", authMiddleware, async (c) => {
  const projectId = c.get("projectId");
  const body = await c.req.json();
  const items = Array.isArray(body) ? body : [body];
  const db = getDb();

  const insert = db.prepare(`
    INSERT OR REPLACE INTO traces
      (id, project_id, agent_name, status, started_at, ended_at,
       total_tokens_in, total_tokens_out, total_cost_usd, metadata, error)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const insertMany = db.transaction(() => {
    for (const t of items) {
      insert.run(
        t.id,
        projectId,
        t.agent_name || null,
        t.status || "running",
        t.started_at,
        t.ended_at || null,
        t.total_tokens_in || 0,
        t.total_tokens_out || 0,
        t.total_cost_usd || 0,
        t.metadata ? JSON.stringify(t.metadata) : null,
        t.error || null
      );
    }
  });

  insertMany();
  return c.json({ ingested: items.length }, 201);
});

// List traces
traces.get("/", authMiddleware, async (c) => {
  const projectId = c.get("projectId");
  const db = getDb();

  const limit = parseInt(c.req.query("limit") || "50", 10);
  const offset = parseInt(c.req.query("offset") || "0", 10);
  const status = c.req.query("status");
  const agent = c.req.query("agent");

  let query = "SELECT * FROM traces WHERE project_id = ?";
  const params: any[] = [projectId];

  if (status) {
    query += " AND status = ?";
    params.push(status);
  }
  if (agent) {
    query += " AND agent_name = ?";
    params.push(agent);
  }

  query += " ORDER BY started_at DESC LIMIT ? OFFSET ?";
  params.push(limit, offset);

  const rows = db.prepare(query).all(...params);

  // Get total count
  let countQuery = "SELECT COUNT(*) as total FROM traces WHERE project_id = ?";
  const countParams: any[] = [projectId];
  if (status) {
    countQuery += " AND status = ?";
    countParams.push(status);
  }
  if (agent) {
    countQuery += " AND agent_name = ?";
    countParams.push(agent);
  }
  const { total } = db.prepare(countQuery).get(...countParams) as {
    total: number;
  };

  return c.json({ data: rows, total, limit, offset });
});

// Get single trace with spans
traces.get("/:id", authMiddleware, async (c) => {
  const projectId = c.get("projectId");
  const traceId = c.req.param("id");
  const db = getDb();

  const trace = db
    .prepare("SELECT * FROM traces WHERE id = ? AND project_id = ?")
    .get(traceId, projectId);

  if (!trace) {
    return c.json({ error: "Trace not found" }, 404);
  }

  const spans = db
    .prepare("SELECT * FROM spans WHERE trace_id = ? ORDER BY started_at ASC")
    .all(traceId);

  return c.json({ ...(trace as any), spans });
});

export default traces;
