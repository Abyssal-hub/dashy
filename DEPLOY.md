# Deployment Guide

Quick start for running Dashy locally on Linux.

## Prerequisites

- Docker and Docker Compose installed
- Ports 8000, 5432, 6379 available (or configure in .env)

## Quick Start

```bash
# 1. Clone/navigate to project
cd personal-monitoring-dashboard

# 2. Start the application
./start.sh
```

This will:
- Create `.env` from `.env.example` if needed
- Build Docker images
- Start PostgreSQL, Redis, and Backend
- Run database migrations
- Show you the URLs

## Access the Application

| Service | URL |
|---------|-----|
| Frontend (Login) | http://localhost:8000 |
| Dashboard | http://localhost:8000/dashboard |
| API Documentation | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

## Configuration

Edit `.env` to customize:

```bash
# Database password (CHANGE THIS!)
POSTGRES_PASSWORD=your-secure-password

# JWT secret key (CHANGE THIS!)
SECRET_KEY=your-32-character-secret-key

# Ports
BACKEND_PORT=8000
POSTGRES_PORT=5432
REDIS_PORT=6379
```

**Important:** After changing `.env`, restart with:
```bash
./stop.sh
./start.sh
```

## Management Commands

```bash
# View logs
./logs.sh

# Stop everything
./stop.sh

# View backend logs only
docker-compose logs -f backend

# View database logs
docker-compose logs -f postgres

# Restart just the backend
docker-compose restart backend

# Reset database (WARNING: deletes all data!)
docker-compose down -v
./start.sh
```

## Creating a User

Since registration UI is not implemented yet, create a user via API:

```bash
# Create user with curl
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "your-password"}'
```

Then login at http://localhost:8000

## Troubleshooting

**Port already in use:**
```bash
# Change ports in .env
BACKEND_PORT=8080
POSTGRES_PORT=5433
```

**Database migrations failed:**
```bash
# Reset and retry
docker-compose down -v
./start.sh
```

**Check service status:**
```bash
docker-compose ps
```

**View logs for errors:**
```bash
docker-compose logs backend
docker-compose logs postgres
```
