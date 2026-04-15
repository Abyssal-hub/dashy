# Personal Monitoring Dashboard

A personal, extensible monitoring dashboard for tracking portfolios, global financial events, and custom metrics.

## Quick Start

```bash
cd personal-monitoring-dashboard

# Start everything with one command
./launch.sh

# Or use docker-compose directly
docker-compose up --build
```

The launch script will:
- Check for available ports
- Build and start all services (Postgres, Redis, Backend)
- Run database migrations automatically
- Wait for services to be healthy
- Show you the URLs to access the dashboard

**Access the app:**
- Dashboard: http://localhost:8000/dashboard.html
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

**Other commands:**
```bash
./launch.sh stop    # Stop all services
./launch.sh logs    # View service logs
./launch.sh status  # Check service status
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
