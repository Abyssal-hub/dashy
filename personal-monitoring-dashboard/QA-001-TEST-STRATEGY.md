# QA-001: Test Strategy

**Project:** Personal Monitoring Dashboard  
**Date:** 2024-01-15  
**Author:** QA Engineer  
**Status:** IN_REVIEW  

---

## 1. Executive Summary

This document defines the testing strategy for Phase 1 of the Personal Monitoring Dashboard. It covers the test pyramid, critical paths, module-specific done criteria, tooling choices, and risk priorities. The strategy aligns with the architecture defined in `ARCHITECTURE.md` and the workflow in `WORKFLOW.md`.

---

## 2. Test Pyramid

Following the industry golden standard referenced in `ARCHITECTURE.md` Section 13, the project adopts a **70 / 20 / 10** split:

| Level | Target Coverage | Purpose | Owner |
|-------|-----------------|---------|-------|
| **Unit Tests** | 70% | FastAPI handlers/services, Pydantic models, utility functions, frontend pure logic | Developer |
| **Integration Tests** | 20% | API endpoints with real DB/Redis, scraper-to-queue-to-consumer pipeline, auth flows | QA (with Developer support) |
| **E2E Tests** | 10% | Critical user journeys via Playwright (login → dashboard → module interaction) | QA |

### 2.1 Unit Tests
- **Backend:** pytest + pytest-asyncio. Target all handler classes (`PortfolioHandler`, `CalendarHandler`, etc.), circuit breaker state machine, alert evaluation logic, and Pydantic validators.
- **Frontend:** Vitest (Next.js default). Target Zustand store logic, utility functions, and data transformers. UI component tests for `ModuleCard`, `GridLayout`, and `LogViewer`.

### 2.2 Integration Tests
- **Backend API:** pytest + TestClient against a Dockerized PostgreSQL + Redis stack. Spin up per-test-session containers via `pytest-docker` or `testcontainers`.
- **Data Pipeline:** Push fake metrics/events to Redis, verify consumer writes to TimescaleDB, then read back through `/modules/{id}/data`.
- **Auth Flow:** Test full JWT lifecycle — login, access token expiry, refresh rotation, logout revocation — against real database.

### 2.3 E2E Tests
- **Tool:** Playwright
- **Scope:**
  1. Authentication journey (login → dashboard → logout)
  2. Portfolio module journey (create module → add position → verify total → change display currency)
  3. Calendar module journey (create event → verify appearance → filter scraped events)
  4. Dashboard layout journey (drag card → refresh → verify persistence)
- **Environment:** Full `docker-compose up` stack on CI runner.

---

## 3. Critical Paths for Testing

These are the flows where a failure has the highest impact on user trust, data integrity, or system stability.

### 3.1 Authentication & Security (P1)
- Valid/invalid login attempts
- JWT access token expiry and refresh rotation
- Refresh token revocation on logout
- Protected endpoint rejection of invalid/missing tokens
- Rate limiting on `/auth/*` (5 req/min)
- Argon2 password hashing

### 3.2 Data Pipeline (P1)
- Scraper worker pushes to Redis `metrics_queue`
- Redis consumer drains queue and batches inserts to TimescaleDB
- Circuit breaker opens after 3 failures in 5 min, recovers after 10 min
- Graceful shutdown finishes current batch on `SIGTERM`
- Data retention policies enforced (90-day raw metric deletion, 7-day log deletion)

### 3.3 Portfolio Module (P1)
- Position CRUD updates total value correctly
- FX rate conversion accuracy (SGD base ↔ display currency)
- Missing FX rate surfaces a warning
- Daily snapshot is recorded automatically
- All asset types behave correctly (equity, cash, bond, real_estate, insurance)
- Yahoo Finance circuit breaker fails open with stale-data indicator

### 3.4 Calendar Module (P1)
- Personal event CRUD with timezone normalization (UTC storage, local display)
- Scraped event deduplication via `external_id`
- Keyword filtering for scraped events
- Recurring event support (iCal RRULE)
- No data loss on timezone edge cases (DST transitions)

### 3.5 Dashboard Layout (P1)
- Drag/resize persists after refresh
- Layout validation prevents overlapping positions
- Add/remove module updates grid immediately and survives reload
- Responsive breakpoints render correctly (4/3/2/1 columns)
- Size bucket mapping (`compact`/`standard`/`expanded`) triggers correct data refetch

### 3.6 Alert System (P2)
- Threshold crossing triggers alert and writes to `alert_history`
- Email notification sent via Resend
- 15-minute cooldown prevents duplicate spam
- Acknowledged alert disappears from active list
- Scheduled sweep catches stale states missed by event-driven trigger

### 3.7 Module Registry & Extensibility (P2)
- Handler registry resolves correct class per `module_type`
- `GET /modules/{id}/data` delegates properly with size parameter
- Creating a module seeds correct default settings
- Deleting a module cascades to dashboard layout and alert rules

---

## 4. Done Criteria by Module Type

### 4.1 Backend API Module
A backend module (auth, dashboard, modules, ingest, alerts, logs) is **done** when:
- [ ] Unit tests cover all handler/service functions (≥80% line coverage for business logic)
- [ ] Integration tests verify all endpoints with real database and return correct HTTP status codes
- [ ] Pydantic input validation edge cases tested (empty strings, out-of-range numbers, missing required fields)
- [ ] Error responses include clear, structured messages
- [ ] SQL injection resistance verified (parameterized queries only)
- [ ] No hardcoded secrets in code or tests

### 4.2 Frontend Component / Page
A frontend deliverable is **done** when:
- [ ] Unit tests pass for store logic and data utilities
- [ ] Component renders correctly in all size buckets (`compact`, `standard`, `expanded`)
- [ ] Loading, empty, and error states are visually distinct and tested
- [ ] User interactions (click, drag, right-click menu) behave per `ARCHITECTURE.md` Section 4.3
- [ ] Data freshness indicators display correct color (green <15 min, yellow 15–60 min, red >60 min)
- [ ] React Error Boundary prevents single card crash from destroying dashboard

### 4.3 Data Pipeline (Scraper + Redis + Consumer + DB)
The pipeline is **done** when:
- [ ] Integration test: scraper pushes message to Redis queue
- [ ] Integration test: consumer accumulates batch (100 msg or 5s timeout) and bulk-inserts to TimescaleDB
- [ ] Circuit breaker transitions `CLOSED` → `OPEN` → `HALF-OPEN` → `CLOSED` under simulated failures
- [ ] Graceful shutdown test: in-flight batch completes before process exits
- [ ] Data retention jobs delete expired data without affecting other tables

### 4.4 Database Schema / Migration
A schema change is **done** when:
- [ ] Migration applies cleanly on fresh database (`alembic upgrade head`)
- [ ] Downgrade path tested (`alembic downgrade -1`)
- [ ] Migration is idempotent (re-running does not corrupt data)
- [ ] Seed data for `module_types` inserts correctly
- [ ] Foreign key constraints and cascade behaviors verified

### 4.5 Module-Specific Handler (Portfolio, Calendar, Log)
A module handler is **done** when:
- [ ] Unit tests cover `get_data()` for all size buckets
- [ ] Handler correctly reads module-specific config from `settings` JSONB
- [ ] Handler returns data within 500 ms p95 for standard-size requests
- [ ] Handler degrades gracefully when upstream data is stale or missing
- [ ] Handler logs errors without exposing internal stack traces to the client

---

## 5. Testing Tools & Environment

| Layer | Tool | Notes |
|-------|------|-------|
| Backend Unit/Integration | pytest, pytest-asyncio, httpx, asyncpg | Run against Docker Compose test stack |
| Frontend Unit | Vitest, React Testing Library | Bundled with Next.js 14 |
| E2E | Playwright | Tests run against full `docker-compose up` |
| Database Test Fixtures | testcontainers-python or manual Docker Compose | Postgres 15 + TimescaleDB + Redis 7 |
| Mock External APIs | pytest-httpx, responses | Mock Yahoo Finance, CoinGecko, Resend |
| CI/CD | GitHub Actions | Lint → Unit Tests → Integration Tests → E2E |
| Code Quality | Black, Ruff, mypy, pre-commit | Referenced in `ARCHITECTURE.md` Section 13 |

---

## 6. Risk-Based Testing Priorities

| Risk Area | Testing Response | Priority |
|-----------|------------------|----------|
| Yahoo Finance API instability | Circuit breaker integration tests + manual fallback verification | P1 |
| Forex Factory HTML redesign | Scraper error-handling tests (graceful failure, no crash) | P2 |
| Incorrect portfolio valuation | FX conversion accuracy tests + boundary tests for missing rates | P1 |
| Authentication bypass | Security-focused integration tests on all protected routes | P1 |
| Data loss in TimescaleDB hypertable | Backup/restore smoke test + retention policy verification | P2 |
| Redis SPOF (local only) | Consumer reconnect tests + queue durability checks | P2 |
| Frontend grid crash | Error boundary tests + layout persistence tests | P1 |
| Alert spam/fatigue | Cooldown logic unit tests + E2E notification verification | P2 |

---

## 7. Test Schedule (Phase 1)

| Week | QA Focus |
|------|----------|
| Week 1 | Review architecture, finalize this strategy, set up test infrastructure |
| Week 2 | Begin backend integration test skeleton (auth, module CRUD) |
| Week 3 | Portfolio module validation (QA-005) |
| Week 4 | Calendar module validation + data pipeline integration (QA-004, QA-006) |
| Week 5 | Alert system + layout interaction tests (QA-007, QA-008) |
| Week 6 | E2E smoke tests, bug triage, defect retesting |
| Week 7 | Performance baseline (QA-010), final sign-off |

---

## 8. Sign-Off

This test strategy is ready for Architect review. Upon approval, QA will proceed with test infrastructure setup and execution of QA-002 through QA-010.

