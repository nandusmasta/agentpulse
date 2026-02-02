import { Hono } from "hono";
import { getDb } from "../db/schema";
import { authMiddleware } from "../services/auth";

const stats = new Hono();

stats.get("/", authMiddleware, async (c) => {
  const projectId = c.get("projectId");
  const db = getDb();

  const totals = db
    .prepare(
      `SELECT
        COUNT(*) as total_traces,
        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
        SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
        SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_count,
        SUM(total_tokens_in) as total_tokens_in,
        SUM(total_tokens_out) as total_tokens_out,
        SUM(total_cost_usd) as total_cost_usd,
        AVG(ended_at - started_at) as avg_duration_s
      FROM traces
      WHERE project_id = ?`
    )
    .get(projectId);

  const dailyCosts = db
    .prepare(
      `SELECT
        date(started_at, 'unixepoch') as day,
        SUM(total_cost_usd) as cost,
        COUNT(*) as traces
      FROM traces
      WHERE project_id = ?
        AND started_at > unixepoch('now', '-7 days')
      GROUP BY day
      ORDER BY day ASC`
    )
    .all(projectId);

  const topAgents = db
    .prepare(
      `SELECT
        agent_name,
        COUNT(*) as trace_count,
        SUM(total_cost_usd) as total_cost,
        AVG(ended_at - started_at) as avg_duration
      FROM traces
      WHERE project_id = ? AND agent_name IS NOT NULL
      GROUP BY agent_name
      ORDER BY total_cost DESC
      LIMIT 10`
    )
    .all(projectId);

  return c.json({
    totals,
    daily_costs: dailyCosts,
    top_agents: topAgents,
  });
});

export default stats;
