import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";
import health from "./routes/health";
import spans from "./routes/spans";
import stats from "./routes/stats";
import traces from "./routes/traces";

const app = new Hono();

// Middleware
app.use("*", logger());
app.use(
  "*",
  cors({
    origin: "*",
    allowHeaders: ["Content-Type", "X-AgentPulse-Key"],
    allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  })
);

// Routes
app.route("/v1/health", health);
app.route("/v1/traces", traces);
app.route("/v1/spans", spans);
app.route("/v1/stats", stats);

// Root
app.get("/", (c) =>
  c.json({
    name: "AgentPulse Collector",
    version: "0.1.0",
    docs: "/v1/health",
  })
);

const port = parseInt(process.env.PORT || "3000", 10);
console.log(`AgentPulse Collector running on http://localhost:${port}`);

export default {
  port,
  fetch: app.fetch,
};
