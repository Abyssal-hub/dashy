# CLAUDE.md — Personal Monitoring Dashboard

## Project Context
- **Name:** Personal Monitoring Dashboard
- **Type:** Full-stack web application
- **Repository:** work/personal-monitoring-dashboard/

## Architecture (from ARCHITECTURE.md)
- **Backend:** FastAPI with SQLAlchemy ORM
- **Database:** PostgreSQL with Alembic migrations
- **Frontend:** Vanilla JS dashboard with module system
- **Auth:** JWT tokens with refresh token rotation
- **API:** RESTful, module-specific data endpoints

## Module System
Three module types with dedicated handlers:
- **Portfolio** — Asset tracking, allocation, performance
- **Calendar** — Event tracking with impact analysis
- **Log** — Structured logging with severity levels

## API Contract
- `GET /api/modules/{id}/data` — Returns module-specific data
- Response format: `{ module_type, data: {...} }`
- Frontend MUST extract `response.data` before accessing fields

## Development Rules
1. **Frontend follows Architecture Blueprint** — Read ARCHITECTURE.md Section 4 before any frontend work
2. **E2E tests required for frontend changes** — QA drafts tests before implementation
3. **No hardcoded data** — All module renderers fetch from API
4. **CSP-friendly** — No inline scripts, use addEventListener

## Roles (from ROLE.md)
- **Architect** — Plans features, maintains ARCHITECTURE.md
- **Developer** — Implements per spec, never modifies tests
- **QA** — Writes tests, validates, files defects
- **UI/UX** — Designs flows, reviews E2E scenarios

## Definition of Done
1. Code implemented per ARCHITECTURE.md
2. Unit tests pass (Developer)
3. Integration tests pass (QA)
4. E2E user journey tests pass (QA + UI/UX)
5. No hardcoded placeholder data
6. Cross-user isolation verified
7. Error states show friendly messages

## Known Issues
- DEF-020: Log module stuck on "Loading..." — FIXED
- DEF-021: Portfolio/Calendar show fake data — FIXED
- Both fixes: Extract `response.data` before accessing nested fields
