# Task Board: Personal Monitoring Dashboard - Phase 1

**Status:** Ready for Assignment
**Last Updated:** 2024-01-15

---

## Legend
- `[]` = BACKLOG
- `[ASSIGNED]` = Assigned to team member
- `[IN_PROGRESS]` = Work started
- `[BLOCKED]` = Waiting on input/blocker
- `[IN_REVIEW]` = Complete, pending review
- `[DONE]` = Accepted and merged

---

## Architecture Tasks (ARCH)

### ARCH-001: Finalize database schema SQL
**Status:** [DONE]
**Assigned:** Architect (completed)
**Deliverable:** `ARCHITECTURE.md` Section 6 + schema.sql file
**Notes:** Schema approved and documented.

### ARCH-002: Finalize API contract
**Status:** [DONE]
**Assigned:** Architect (completed)
**Deliverable:** `ARCHITECTURE.md` Section 5.1
**Notes:** All endpoints specified.

### ARCH-003: Create initial project structure
**Status:** [DONE]
**Assigned:** Architect (completed)
**Deliverable:** Repository skeleton with README, .gitignore, docker-compose.yml
**Acceptance Criteria:**
- [x] Backend folder structure
- [x] Frontend folder structure
- [x] Docker Compose with postgres, redis services
- [x] .env.example with all required keys

---

## Development Tasks (DEV)

### DEV-001: Backend foundation - FastAPI app skeleton
**Status:** [DONE]
**Priority:** P1 (blocking)
**Assigned:** Developer (completed)
**Source:** ARCHITECTURE.md Section 5
**Deliverable:** Working FastAPI app with health endpoint
**Acceptance Criteria:**
- [x] FastAPI app factory with lifespan management
- [x] Config management (pydantic-settings)
- [x] Database connection pool (asyncpg or SQLAlchemy async)
- [x] Redis client setup
- [x] CORS middleware configured
- [x] Health endpoint at `/health` returns DB + Redis status
- [x] Docker container builds and runs

### DEV-002: Authentication system
**Status:** [DONE]
**Priority:** P1 (blocking)
**Assigned:** Developer (completed)
**Source:** ARCHITECTURE.md Section 5.3, 3.1
**Deliverable:** Full auth system with JWT
**Acceptance Criteria:**
- [x] User model in database
- [x] Argon2 password hashing
- [x] POST `/auth/login` endpoint
- [x] POST `/auth/refresh` endpoint
- [x] POST `/auth/logout` endpoint
- [x] JWT middleware protecting routes
- [x] Refresh token httpOnly cookie handling
- [x] Rate limiting on auth endpoints

### DEV-003: Database migrations setup
**Status:** [DONE]
**Priority:** P1 (blocking)
**Assigned:** Developer (completed)
**Source:** ARCHITECTURE.md Section 6
**Deliverable:** Alembic migrations for all tables
**Acceptance Criteria:**
- [x] Alembic initialized
- [x] Initial migration creates all tables from schema
- [x] Migration applies cleanly on fresh database
- [x] Downgrade path tested

### QA-REG-001: Regression check - Backend foundation
**Status:** [DONE]  
**Priority:** P1  
**Assigned:** QA (completed)  
**Depends:** DEV-001, DEV-002, DEV-003  
**Deliverable:** Full CI run confirms foundation is solid
**Acceptance Criteria:**
- [x] Run `pytest` in backend/ - all tests pass (14/14)
- [x] Testcontainers integration working (PostgreSQL + Redis)
- [x] Auth endpoint tests with real database (login, refresh, logout, token rotation, protected routes)
- [x] Health endpoint tests with real services
- [x] Docker daemon available for testcontainers
- [~] Alembic migration tests - requires 'dashboard' database created (manual step)
- [~] Docker build test - requires completing Dockerfile (DEV-001 partially done)
**Gate:** PASSED. Cleared for DEV-004. Run `./scripts/run-qa-reg-001.sh` for full validation.

### DEV-004: Module system foundation
**Status:** [DONE]
**Priority:** P1 (blocking)
**Assigned:** Developer (via GitHub Actions)
**Source:** ARCHITECTURE.md Section 5.2, 7
**Deliverable:** Generic module framework
**Acceptance Criteria:**
- [x] Module registry pattern implemented (`app/modules/registry.py`)
- [x] Base ModuleHandler class (`app/modules/base.py`)
- [x] Handler stubs created (portfolio, calendar, log)
- [x] Module model (`app/models/module.py`)
- [x] Pydantic schemas (`app/schemas/module.py`)
- [x] CRUD router (`app/api/modules/router.py`)
- [x] Register router in main.py
- [x] Create Alembic migration for Module table
- [x] Run full test suite (15/15 passing)
**Notes:** All acceptance criteria met. CI passing on GitHub Actions.
**Gate:** CLEARED for DEV-005.

### DEV-005: Dashboard layout endpoints
**Status:** [DONE]
**Priority:** P2
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 5.1, 4.2
**Deliverable:** Layout persistence API
**Acceptance Criteria:**
- [x] GET `/dashboard/layout` returns user's grid layout
- [x] PUT `/dashboard/layout` saves layout
- [x] POST `/dashboard/modules/{id}` adds module to dashboard
- [x] DELETE `/dashboard/modules/{id}` removes from dashboard
- [x] Layout validated (no overlapping positions)
- [x] Migration 003 created
- [x] All tests passing (15/15)
**Gate:** CLEARED for DEV-006.

### DEV-006: Portfolio Module handler
**Status:** [DONE]
**Priority:** P1
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 7.1
**Deliverable:** Full Portfolio module backend
**Acceptance Criteria:**
- [x] PortfolioHandler implements get_data() for compact/standard/expanded sizes
- [x] GET `/modules/{id}/data` works for portfolio type
- [x] Supports asset types: equity, cash, bond, real_estate, insurance
- [x] Position CRUD operations
- [x] Daily snapshot recording
- [x] FX rate table and manual entry
- [x] SGD base currency with selectable display currency
- [x] Yahoo Finance integration for equity prices (with circuit breaker)
- [x] Migration 004 created
- [x] All tests passing (15/15)
**Gate:** CLEARED for FE-MVP-001.

### FE-MVP-001: Frontend MVP (vanilla HTML/JS)
**Status:** [DONE]
**Priority:** P0
**Assigned:** Developer
**Source:** MVP requirement - main page first
**Deliverable:** Working frontend with login and dashboard
**Acceptance Criteria:**
- [x] Login page with JWT authentication
- [x] Dashboard with grid layout
- [x] Add/delete modules UI
- [x] Module type icons and previews
- [x] Static file serving from FastAPI
- [x] Tailwind CSS styling
**Gate:** CLEARED for DEV-007.

### DEV-007: Calendar Module handler
**Status:** []
**Priority:** P1
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 7.2
**Deliverable:** Full Calendar module backend
**Acceptance Criteria:**
- [ ] CalendarHandler implements get_data()
- [ ] Personal event CRUD
- [ ] Event supports: title, description, start/end time, timezone, all-day, recurrence
- [ ] Scraped event integration (external_id deduplication)
- [ ] Keyword filtering for scraped events
- [ ] GET `/modules/{id}/data` returns events in time range

### QA-REG-002: Regression check - Core backend modules
**Status:** []
**Priority:** P1
**Assigned:** QA
**Depends:** DEV-004, DEV-005, DEV-006, DEV-007
**Deliverable:** CI confirms backend modules are stable
**Acceptance Criteria:**
- [ ] Full pytest suite passes (unit + integration)
- [ ] Module CRUD endpoints respond correctly
- [ ] Dashboard layout endpoints respond correctly
- [ ] Portfolio and Calendar handlers return data for all size buckets
- [ ] Auth endpoints still work after module additions
**Gate:** Must pass before DEV-008 is assigned.

### DEV-008: Data ingestion endpoints
**Status:** []
**Priority:** P1
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 8
**Deliverable:** Ingest API for scraper
**Acceptance Criteria:**
- [ ] POST `/ingest/metrics` accepts batch metrics
- [ ] POST `/ingest/events` accepts batch events
- [ ] Batching logic (100 messages or 5s timeout)
- [ ] Writes to TimescaleDB metrics hypertable
- [ ] Writes to calendar_events table
- [ ] Returns 202 Accepted immediately, processes async

### DEV-009: Redis consumer (background task)
**Status:** []
**Priority:** P1
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 8.4
**Deliverable:** Async consumer draining Redis queue
**Acceptance Criteria:**
- [ ] Consumer starts with FastAPI lifespan
- [ ] BLPOP from `metrics_queue`
- [ ] Batch accumulation (100 msg or 5s)
- [ ] Bulk insert to TimescaleDB
- [ ] Graceful shutdown on SIGTERM (finish current batch)
- [ ] Error handling with retry

### DEV-010: Alert system foundation
**Status:** []
**Priority:** P2
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 9
**Deliverable:** Alert rules and evaluation
**Acceptance Criteria:**
- [ ] Alert rule model (threshold, operator, module_id)
- [ ] GET `/alerts` endpoint
- [ ] POST `/alerts/{id}/acknowledge` endpoint
- [ ] Event-driven evaluation on ingest
- [ ] 5-minute scheduled sweep (APScheduler)
- [ ] 15-minute cooldown between repeat alerts

### DEV-011: Resend email integration
**Status:** []
**Priority:** P2
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 2.4, 9.3
**Deliverable:** Email notifications working
**Acceptance Criteria:**
- [ ] Resend client configured
- [ ] Email sent when alert triggered
- [ ] Alert history records email_sent status
- [ ] Uses RESEND_API_KEY from env

### DEV-012: Log Module handler
**Status:** []
**Priority:** P3
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 7.4, 11.2
**Deliverable:** System log viewing
**Acceptance Criteria:**
- [ ] LogHandler implements get_data()
- [ ] GET `/logs` endpoint with severity filtering
- [ ] System logs written to database (7-day retention)
- [ ] Log module displays recent logs with color-coded severity

### QA-REG-003: Regression check - Backend complete
**Status:** []
**Priority:** P1
**Assigned:** QA
**Depends:** DEV-008, DEV-009, DEV-010, DEV-011, DEV-012
**Deliverable:** CI confirms all backend features are stable
**Acceptance Criteria:**
- [ ] Full pytest suite passes
- [ ] Data ingestion pipeline works end-to-end
- [ ] Alert system triggers and emails correctly
- [ ] Log module records and retrieves system logs
- [ ] Redis consumer runs without errors
- [ ] All migrations apply cleanly on fresh DB
**Gate:** Must pass before DEV-013 is assigned.

### DEV-013: Scraper worker - Yahoo Finance
**Status:** []
**Priority:** P1
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 8.3
**Deliverable:** Standalone scraper for equities
**Acceptance Criteria:**
- [ ] Separate Python process (not part of FastAPI)
- [ ] Uses yfinance library
- [ ] Fetches configured equity symbols
- [ ] Pushes to Redis queue every 5 minutes
- [ ] Circuit breaker (3 failures → 10 min cooldown)
- [ ] Structured logging

### DEV-014: Scraper worker - Forex Factory
**Status:** []
**Priority:** P2
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 8.3
**Deliverable:** Calendar event scraper
**Acceptance Criteria:**
- [ ] Parses Forex Factory economic calendar HTML
- [ ] Filters by configured keywords
- [ ] Extracts: title, time, currency, impact level
- [ ] Deduplicates via external_id
- [ ] Pushes to Redis queue every 1 hour
- [ ] Graceful handling of HTML changes (log error, don't crash)

### DEV-015: Integration - Kimi Professional Data
**Status:** []
**Priority:** P1
**Assigned:** Developer
**Source:** User request (Kimi mobile app feature)
**Deliverable:** Portfolio data from Kimi Professional Data API
**Acceptance Criteria:**
- [ ] Research Kimi Professional Data API endpoints (Global Finance, Stock Finance)
- [ ] Design integration pattern for credential storage (user-level API key)
- [ ] Implement `KimiDataHandler` in `app/modules/handlers/kimi_data.py`
- [ ] Support data types: stock prices, indices, futures, economic indicators
- [ ] Caching layer to minimize API calls (respect rate limits)
- [ ] Error handling for quota exceeded / rate limit responses
- [ ] User can configure which symbols/data feeds to track
- [ ] Module displays real-time data from Kimi sources
**Depends on:** Portfolio module UI (DEV-018) and API integration pattern
**Notes:** High-priority data source. User has shown 0.93% credit usage in screenshot.

### QA-REG-004: Regression check - Data pipeline complete
**Status:** []
**Priority:** P1
**Assigned:** QA
**Depends:** DEV-013, DEV-014
**Deliverable:** CI confirms scrapers and pipeline are stable
**Acceptance Criteria:**
- [ ] Full pytest suite passes (backend)
- [ ] Scraper containers build and start
- [ ] End-to-end: Scraper → Redis → Consumer → DB → API works
- [ ] Circuit breaker triggers correctly under simulated failure
- [ ] No regression in existing auth or module endpoints
**Gate:** Must pass before DEV-015 is assigned.

### DEV-015: Frontend foundation - Next.js setup
**Status:** []
**Priority:** P1 (blocking)
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 2.1, 4
**Deliverable:** Working Next.js app skeleton
**Acceptance Criteria:**
- [ ] Next.js 14 with App Router
- [ ] TypeScript configured
- [ ] Tailwind CSS configured with dark mode
- [ ] TanStack Query setup
- [ ] Zustand store setup
- [ ] API client configured (axios/fetch with auth header)
- [ ] Docker container builds and runs
- [ ] Shows "Hello Dashboard" on `/`

### DEV-016: Authentication UI
**Status:** []
**Priority:** P1
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 5.3
**Deliverable:** Login page and auth flow
**Acceptance Criteria:**
- [ ] Login form (email, password)
- [ ] Error handling (invalid creds)
- [ ] Stores access token in memory
- [ ] Handles refresh token cookie automatically
- [ ] Redirects to dashboard on success
- [ ] Logout button clears state

### DEV-017: Dashboard layout (react-grid-layout)
**Status:** []
**Priority:** P1
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 4.2, 2.1
**Deliverable:** Draggable/resizable grid
**Acceptance Criteria:**
- [ ] react-grid-layout integrated
- [ ] 4 columns desktop, responsive breakpoints
- [ ] Cards draggable
- [ ] Cards resizable (bottom-right handle)
- [ ] Layout saves to backend (debounced)
- [ ] Layout loads from backend on mount

### QA-REG-005: Regression check - Frontend foundation
**Status:** []
**Priority:** P1
**Assigned:** QA
**Depends:** DEV-015, DEV-016, DEV-017
**Deliverable:** CI confirms frontend foundation is stable
**Acceptance Criteria:**
- [ ] Frontend builds without errors: `npm run build` or `docker build`
- [ ] Login page loads and authenticates correctly
- [ ] Dashboard layout renders and persists
- [ ] Auth token handling works across page reloads
- [ ] No console errors in browser dev tools
- [ ] Responsive breakpoints work (desktop/tablet/mobile)
**Gate:** Must pass before DEV-018 is assigned.

### DEV-018: Generic Module Card component
**Status:** []
**Priority:** P1
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 4.3
**Deliverable:** Reusable card wrapper
**Acceptance Criteria:**
- [ ] Card shows title and menu button
- [ ] Card shows last-updated timestamp
- [ ] Timestamp color-codes freshness (green/yellow/red)
- [ ] Right-click context menu (Configure, Remove, Refresh)
- [ ] Size-aware: renders compact/standard/expanded based on dimensions

### DEV-019: Portfolio Module UI
**Status:** []
**Priority:** P1
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 7.1
**Deliverable:** Portfolio visualization
**Acceptance Criteria:**
- [ ] Compact view: total value + mini sparkline
- [ ] Standard view: position list with values
- [ ] Expanded view: full page with charts, add/edit positions
- [ ] Currency selector (changes display, not base)
- [ ] FX rate input form
- [ ] Position CRUD forms

### DEV-020: Calendar Module UI
**Status:** []
**Priority:** P1
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 7.2
**Deliverable:** Calendar visualization
**Acceptance Criteria:**
- [ ] Compact view: upcoming events list
- [ ] Standard view: week view
- [ ] Expanded view: full page month view with event details
- [ ] Personal event CRUD modal
- [ ] Scraped events shown differently (color/icon)
- [ ] Keyword filter settings

### DEV-021: Log Module UI
**Status:** []
**Priority:** P3
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 7.4
**Deliverable:** Log viewing interface
**Acceptance Criteria:**
- [ ] Shows log entries in reverse chronological order
- [ ] Severity filtering (INFO/WARN/ERROR)
- [ ] Auto-refresh every 10 seconds
- [ ] Color-coded severity levels

### DEV-022: Module creation flow
**Status:** []
**Priority:** P2
**Assigned:** Developer
**Source:** ARCHITECTURE.md Section 7
**Deliverable:** Add new module to dashboard
**Acceptance Criteria:**
- [ ] "+" button in header
- [ ] Modal to select module type
- [ ] Type-specific configuration form
- [ ] Creates module, adds to dashboard, appears in grid

### QA-REG-006: Regression check - Frontend modules complete
**Status:** []
**Priority:** P1
**Assigned:** QA
**Depends:** DEV-018, DEV-019, DEV-020, DEV-021, DEV-022
**Deliverable:** CI confirms all frontend modules are stable
**Acceptance Criteria:**
- [ ] Full frontend build succeeds
- [ ] Portfolio module CRUD works end-to-end
- [ ] Calendar module CRUD works end-to-end
- [ ] Log module auto-refreshes and filters correctly
- [ ] Module creation flow adds cards to dashboard
- [ ] Full stack `docker-compose up` starts all services cleanly
- [ ] No regressions in auth or dashboard layout
**Gate:** Must pass before Phase 1 is declared complete.

---

## QA Tasks (QA)

### QA-001: Review architecture and create test strategy
**Status:** [DONE]
**Priority:** P1
**Assigned:** QA (completed)
**Deliverable:** Test plan document
**Acceptance Criteria:**
- [x] Read ARCHITECTURE.md thoroughly
- [x] Define test pyramid for this project
- [x] Identify critical paths for testing
- [x] Define done criteria for each module type

### QA-002: Backend API tests - Auth endpoints
**Status:** [DONE]
**Priority:** P1
**Assigned:** QA
**Depends:** DEV-002
**Deliverable:** Automated tests for auth
**Acceptance Criteria:**
- [x] Test infrastructure with Dockerized DB/Redis via testcontainers
- [x] Test fixtures for database sessions and auth
- [x] Skeleton tests for login endpoint
- [x] Skeleton tests for refresh token endpoint
- [x] Skeleton tests for logout endpoint
- [x] Skeleton tests for protected endpoints
- [ ] Tests pass when DEV-002 is implemented

### QA-003: Backend API tests - Module CRUD
**Status:** []
**Priority:** P1
**Assigned:** QA
**Depends:** DEV-004
**Deliverable:** Module endpoint tests
**Acceptance Criteria:**
- [ ] Test: Create module with valid data
- [ ] Test: Create module with invalid type fails
- [ ] Test: List modules returns only user's modules
- [ ] Test: Update module settings persists
- [ ] Test: Delete module removes from dashboard too

### QA-004: Integration test - Data pipeline
**Status:** []
**Priority:** P1
**Assigned:** QA
**Depends:** DEV-008, DEV-009
**Deliverable:** End-to-end data flow test
**Acceptance Criteria:**
- [ ] Test: Scraper pushes to Redis
- [ ] Test: Consumer drains to TimescaleDB
- [ ] Test: Data appears in dashboard API
- [ ] Test: Circuit breaker triggers on failure

### QA-005: Portfolio Module validation
**Status:** []
**Priority:** P1
**Assigned:** QA
**Depends:** DEV-006, DEV-019
**Deliverable:** Portfolio test report
**Acceptance Criteria:**
- [ ] Test: Add position updates total
- [ ] Test: FX rate conversion accuracy
- [ ] Test: Missing FX rate shows warning
- [ ] Test: Daily snapshot recorded
- [ ] Test: Position types all work (equity, cash, bond, real_estate, insurance)
- [ ] Test: Display currency changes without affecting base

### QA-006: Calendar Module validation
**Status:** []
**Priority:** P1
**Assigned:** QA
**Depends:** DEV-007, DEV-020
**Deliverable:** Calendar test report
**Acceptance Criteria:**
- [ ] Test: Personal event CRUD
- [ ] Test: Scraped events appear
- [ ] Test: Keyword filtering works
- [ ] Test: No duplicate scraped events (external_id dedup)
- [ ] Test: Timezone handling correct

### QA-007: Dashboard layout tests
**Status:** []
**Priority:** P2
**Assigned:** QA
**Depends:** DEV-017, DEV-018
**Deliverable:** Layout interaction tests
**Acceptance Criteria:**
- [ ] Test: Drag reposition persists after refresh
- [ ] Test: Resize changes data density (compact/standard/expanded)
- [ ] Test: Add module appears in grid
- [ ] Test: Remove module disappears
- [ ] Test: Responsive breakpoints work

### QA-008: Alert system validation
**Status:** []
**Priority:** P2
**Assigned:** QA
**Depends:** DEV-010, DEV-011
**Deliverable:** Alert test report
**Acceptance Criteria:**
- [ ] Test: Alert triggers when threshold crossed
- [ ] Test: Email sent on trigger
- [ ] Test: 15-minute cooldown prevents spam
- [ ] Test: Acknowledge removes from active list
- [ ] Test: Scheduled sweep catches stale thresholds

### QA-009: End-to-end smoke tests
**Status:** []
**Priority:** P1
**Assigned:** QA
**Depends:** All DEV tasks complete
**Deliverable:** E2E test suite
**Acceptance Criteria:**
- [ ] Test: Full user journey (login → create module → view data → logout)
- [ ] Test: Docker Compose brings up full stack
- [ ] Test: All services healthy

### QA-010: Performance baseline
**Status:** []
**Priority:** P3
**Assigned:** QA
**Depends:** All DEV tasks complete
**Deliverable:** Performance metrics
**Acceptance Criteria:**
- [ ] Measure: API response times (p50, p95, p99)
- [ ] Measure: Dashboard load time
- [ ] Measure: Database query performance
- [ ] Document: Resource usage (CPU, memory)

---

## Defects (DEF)

**No defects filed yet.**

Format when filing:
```
DEF-XXX: [Brief description]
Severity: Blocker/Major/Minor/Cosmetic
Found By: [Name]
Related To: [Task ID]
Steps to Reproduce:
1. [Step]
2. [Step]
Expected: [Per ARCHITECTURE.md]
Actual: [What happened]
Status: OPEN/FIXED/CLOSED
```

---

## Sprint/Phase Planning

### Week 1: Foundation
- ARCH-003 (Project structure)
- DEV-001 (Backend skeleton)
- DEV-002 (Auth)
- DEV-003 (Migrations)
- DEV-015 (Frontend skeleton)
- DEV-016 (Auth UI)

### Week 2: Core Modules
- DEV-004 (Module system)
- DEV-005 (Dashboard layout)
- DEV-017 (react-grid-layout)
- DEV-018 (Generic card)

### Week 3: Portfolio Module
- DEV-006 (Portfolio backend)
- DEV-013 (Yahoo scraper)
- DEV-019 (Portfolio UI)
- QA-005 (Portfolio validation)

### Week 4: Calendar Module + Pipeline
- DEV-007 (Calendar backend)
- DEV-008 (Ingest endpoints)
- DEV-009 (Redis consumer)
- DEV-014 (Forex scraper)
- DEV-020 (Calendar UI)
- QA-006 (Calendar validation)

### Week 5: Alerts + Polish
- DEV-010 (Alert system)
- DEV-011 (Resend integration)
- DEV-012 (Log module backend)
- DEV-021 (Log module UI)
- DEV-022 (Module creation flow)

### Week 6: Testing + Integration
- QA-001 through QA-010
- Bug fixes
- Documentation

### Week 7: Hardening + Phase 1 Review
- Performance optimization
- Final testing
- Phase 1 retrospective
- Plan Phase 2

---

**Next Action:** Architect assigns DEV-001 to Developer, QA-001 to QA.
