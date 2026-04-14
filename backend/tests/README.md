# Backend API Tests

Integration tests for the Personal Monitoring Dashboard backend API.

## Requirements

- Python 3.12+
- Docker (for testcontainers)
- Running Docker daemon

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run integration tests only (requires Docker)
```bash
pytest -m integration
```

### Run auth tests only
```bash
pytest -m auth
```

### Run with verbose output
```bash
pytest -v
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures and configuration
├── test_health.py        # Health endpoint tests
└── test_auth.py          # Auth endpoint tests (QA-002)
```

## Fixtures

### Database Fixtures
- `postgres_container`: Dockerized PostgreSQL (session-scoped)
- `redis_container`: Dockerized Redis (session-scoped)
- `db_engine`: SQLAlchemy async engine with tables created
- `db_session`: Database session for test operations

### App Fixtures
- `test_settings`: Settings configured for test containers
- `test_app`: FastAPI app with test configuration
- `async_client`: HTTP client for API testing

### Auth Fixtures
- `test_user`: Test user fixture (placeholder until DEV-002)
- `authenticated_client`: Client with valid access token

## Skipped Tests

Auth tests are currently skipped (`pytest.mark.skip`) because DEV-002 (Authentication system) is not yet implemented. Once auth endpoints are available, remove the skip markers to run the tests.

## Test Markers

- `integration`: Tests requiring Docker containers
- `auth`: Authentication-related tests
- `slow`: Long-running tests
