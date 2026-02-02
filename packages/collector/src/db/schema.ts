import { Database } from "bun:sqlite";
import { existsSync, mkdirSync } from "fs";
import { dirname } from "path";

const DB_PATH = process.env.DB_PATH || "./data/agentpulse.db";

let db: Database;

export function getDb(): Database {
  if (!db) {
    const dir = dirname(DB_PATH);
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
    db = new Database(DB_PATH, { create: true });
    db.exec("PRAGMA journal_mode = WAL");
    db.exec("PRAGMA foreign_keys = ON");
    migrate(db);
  }
  return db;
}

function migrate(db: Database): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS projects (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      api_key TEXT UNIQUE NOT NULL,
      created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS traces (
      id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL,
      agent_name TEXT,
      status TEXT DEFAULT 'running',
      started_at REAL NOT NULL,
      ended_at REAL,
      total_tokens_in INTEGER DEFAULT 0,
      total_tokens_out INTEGER DEFAULT 0,
      total_cost_usd REAL DEFAULT 0,
      metadata TEXT,
      error TEXT,
      FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    CREATE TABLE IF NOT EXISTS spans (
      id TEXT PRIMARY KEY,
      trace_id TEXT NOT NULL,
      parent_span_id TEXT,
      name TEXT NOT NULL,
      kind TEXT NOT NULL,
      started_at REAL NOT NULL,
      ended_at REAL,
      input TEXT,
      output TEXT,
      model TEXT,
      tokens_in INTEGER,
      tokens_out INTEGER,
      cost_usd REAL,
      error TEXT,
      FOREIGN KEY (trace_id) REFERENCES traces(id),
      FOREIGN KEY (parent_span_id) REFERENCES spans(id)
    );

    CREATE INDEX IF NOT EXISTS idx_traces_project ON traces(project_id);
    CREATE INDEX IF NOT EXISTS idx_traces_started ON traces(started_at);
    CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id);
    CREATE INDEX IF NOT EXISTS idx_spans_started ON spans(started_at);
  `);

  // Seed a default project if none exist
  const count = db.prepare("SELECT COUNT(*) as n FROM projects").get() as {
    n: number;
  };
  if (count.n === 0) {
    db.prepare(
      "INSERT INTO projects (id, name, api_key) VALUES (?, ?, ?)"
    ).run("default", "Default Project", "ap_dev_default");
  }
}
