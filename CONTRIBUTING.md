# Contributing to AgentPulse

Thanks for your interest in contributing to AgentPulse.

## Development Setup

### Prerequisites

- Python 3.10+
- Bun 1.0+ (for collector)
- Node.js 22+ (for dashboard)
- Docker and Docker Compose (optional, for full stack)

### Clone and Install

```bash
git clone https://github.com/your-org/agentpulse.git
cd agentpulse
```

#### Python SDK

```bash
cd packages/sdk-python
pip install -e ".[dev]"
```

#### Collector

```bash
cd packages/collector
bun install
bun run dev
```

#### Dashboard

```bash
cd packages/dashboard
npm install
npm run dev
```

### Running the Full Stack

```bash
docker-compose up
```

## Running Tests

### SDK

```bash
cd packages/sdk-python
pytest
```

### Linting

```bash
pip install ruff
ruff check packages/sdk-python
ruff format --check packages/sdk-python
```

## Project Structure

```
packages/
  sdk-python/    Python SDK (pip install agentpulse)
  collector/     Trace ingestion API (Bun + Hono + SQLite)
  dashboard/     Web UI (SvelteKit)
examples/        Usage examples
docs/            Documentation
```

## Making Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b my-feature`
3. Make your changes
4. Run tests and linting
5. Commit with a descriptive message
6. Open a pull request

## Code Style

- Python: follow ruff defaults, type hints encouraged
- TypeScript: strict mode, no `any` where avoidable
- Keep dependencies minimal — the SDK must remain zero-dependency

## Reporting Issues

Open an issue on GitHub with:
- What you expected
- What happened
- Steps to reproduce
- Python/Node version and OS

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
