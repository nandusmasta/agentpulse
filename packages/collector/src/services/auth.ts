import type { Context, Next } from "hono";
import { getDb } from "../db/schema";

/**
 * Middleware: validates X-AgentPulse-Key header against the projects table.
 * Sets c.set("projectId", ...) on success.
 */
export async function authMiddleware(c: Context, next: Next) {
  const apiKey = c.req.header("X-AgentPulse-Key");
  if (!apiKey) {
    return c.json({ error: "Missing X-AgentPulse-Key header" }, 401);
  }

  const db = getDb();
  const project = db
    .prepare("SELECT id FROM projects WHERE api_key = ?")
    .get(apiKey) as { id: string } | null;

  if (!project) {
    return c.json({ error: "Invalid API key" }, 401);
  }

  c.set("projectId", project.id);
  await next();
}
