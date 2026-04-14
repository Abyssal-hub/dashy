# Personal Monitoring Dashboard

A personal, extensible monitoring dashboard for tracking portfolios, global financial events, and custom metrics.

## Quick Start

```bash
cd personal-monitoring-dashboard

# Start all services
docker-compose up --build

# Backend will be available at http://localhost:8000
# Frontend (when ready) at http://localhost:3000
```

## Project Structure

```
.
├── backend/          # FastAPI + asyncpg + Redis
├── frontend/         # Next.js 14 + TypeScript + Tailwind
├── docs/             # Architecture, workflow, decisions
├── scripts/          # Helper scripts
├── docker-compose.yml
└── README.md
```

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical blueprint
- [WORKFLOW.md](WORKFLOW.md) - Team workflow
- [TASKS.md](TASKS.md) - Task board
- [QA-001-TEST-STRATEGY.md](QA-001-TEST-STRATEGY.md) - Testing strategy

## Services

| Service | Port | Description |
|---------|------|-------------|
| Backend | 8000 | FastAPI REST API |
| Postgres | 5432 | PostgreSQL + TimescaleDB |
| Redis | 6379 | Queue + Cache |

## Status

**Phase 1: Foundation (MVP v1.0 Complete)** ✅

The MVP version includes:
- JWT authentication (login/register via API)
- Dashboard with grid layout
- Portfolio, Calendar, and Log module types (placeholder views)
- Add/delete modules
- Static file serving with vanilla HTML/JS

See [MVP-UX-FLOWS.md](docs/MVP-UX-FLOWS.md) for complete user journey documentation.
