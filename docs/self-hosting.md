# Self-Hosting Guide

AgentPulse is designed to be self-hosted. The stack consists of two services:

| Service | Description | Default Port |
|---------|-------------|--------------|
| Collector | Trace ingestion API (Bun + Hono) | 3000 |
| Dashboard | Web UI (SvelteKit) | 5173 |

Data is stored in a SQLite database file.

## Docker Compose (Recommended)

```bash
git clone https://github.com/your-org/agentpulse.git
cd agentpulse
docker-compose up -d
```

### Environment Variables

Create a `.env` file in the project root (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3000` | Collector port |
| `DASHBOARD_PORT` | `5173` | Dashboard port |
| `DB_PATH` | `./data/agentpulse.db` | SQLite database path |
| `AP_DEFAULT_API_KEY` | `ap_dev_default` | Default project API key |

### Data Persistence

The Docker Compose file creates a named volume `agentpulse-data` for the SQLite database. Data persists across container restarts.

To back up the database:

```bash
docker cp $(docker-compose ps -q collector):/app/data/agentpulse.db ./backup.db
```

## Running Without Docker

### Collector

Requires [Bun](https://bun.sh/) 1.0+:

```bash
cd packages/collector
bun install
bun run src/index.ts
```

### Dashboard

Requires Node.js 22+:

```bash
cd packages/dashboard
npm install
npm run build
node build/index.js
```

### With PM2

Use the included `ecosystem.config.js`:

```bash
npm install -g pm2
pm2 start ecosystem.config.js
```

## API Key Management

On first start, the collector creates a default project with the API key `ap_dev_default`. Use this key in your SDK configuration:

```python
ap = AgentPulse(
    endpoint="http://localhost:3000",
    api_key="ap_dev_default",
)
```

For production, change the default key via the `AP_DEFAULT_API_KEY` environment variable.

## Health Check

Verify the collector is running:

```bash
curl http://localhost:3000/v1/health
```

Expected response:

```json
{"status": "ok", "service": "agentpulse-collector"}
```
