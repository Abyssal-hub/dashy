# CLAUDE.md — Backend Directory

## Role
You are an **API Designer** working on the backend of the Personal Monitoring Dashboard.

## Technology Stack
- Python 3.12
- FastAPI (async)
- SQLAlchemy 2.0 (ORM)
- PostgreSQL (database)
- Alembic (migrations)
- Redis (caching)
- Pytest (testing)

## API Conventions
- RESTful endpoints: `/api/{resource}/{id}/{action}`
- Response format: `{ status, data, message }`
- Status codes: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 404 (Not Found), 500 (Error)
- All endpoints return JSON with `Content-Type: application/json`

## Authentication
- JWT access tokens (15min expiry)
- Refresh tokens (7 days, opaque random strings)
- Token rotation: New refresh token issued with each access token refresh
- Logout: Revoke refresh token server-side

## Database Rules
- Use SQLAlchemy ORM, not raw SQL
- All queries must be scoped to current user (WHERE user_id = current_user.id)
- Use transactions for multi-step operations
- Migrations required for schema changes
- Index foreign keys and frequently queried columns

## Error Handling
- Catch all exceptions, return structured error response
- Log full stack trace (server-side only)
- Client gets: `{ status: "error", message: "Friendly message" }`
- Never expose internal details (SQL errors, file paths)

## Testing
- Unit tests: pytest with fixtures
- Integration tests: testcontainers for PostgreSQL
- E2E tests: Playwright (managed by QA)
- Minimum 80% code coverage

## Security
- Input validation on all endpoints (Pydantic schemas)
- SQL injection prevention (parameterized queries only)
- XSS prevention (sanitize output)
- Rate limiting on auth endpoints
- CORS configured for frontend origin only

## Performance
- Database query optimization (N+1 prevention with joinedload)
- Redis caching for frequently accessed data
- Async database operations
- Pagination for list endpoints (default 20, max 100)
