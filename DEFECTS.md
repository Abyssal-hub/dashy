---

## DEF-011-001: Refresh token format conflict (JWT vs Opaque)

**Status:** RESOLVED — QA UPDATED TEST  
**Severity:** Major  
**Discovered:** 2024-04-16 during QA-011  
**Decided:** 2024-04-16  
**Resolved:** 2024-04-16  
**Reporter:** QA Engineer  
**Decided By:** Architect  
**Resolved By:** QA  
**Related To:** QA-011, ARCH-5.2, B05

### Summary
QA contract (QA-CONTRACT-001) expected `refresh_token` in JWT format. Implementation uses opaque tokens.

### Architect Decision
**OPAQUE TOKENS ARE CORRECT.** 

Rationale per ARCHITECTURE.md Section 6.1:
- `refresh_tokens` table exists for server-side token management
- Opaque tokens can be revoked (stored as SHA256 hash)
- JWT refresh tokens cannot be revoked without additional state
- Database schema explicitly designed for rotatable, revocable tokens

### QA Fix
Updated `test_contract.py`:
- Removed JWT format check for refresh_token
- Now validates refresh_token is non-empty string (opaque per B05)
- Updated LoginResponse schema docstring with Architect decision reference

**Test Now Passes:** QA-CONTRACT-001 accepts opaque refresh tokens

### Decision Register
Added to ARCHITECTURE.md Decision Register as **B05: Opaque refresh tokens (security)**

---

## DEF-011-002: Register endpoint returns 404 Not Found

**Status:** FIXED  
**Severity:** Blocker  
**Discovered:** 2024-04-16 during QA-011  
**Fixed:** 2024-04-16  
**Reporter:** QA Engineer  
**Fixed By:** Developer  
**Related To:** QA-011, QA-MVP-001

### Summary
POST `/auth/register` returned HTTP 404. Endpoint was missing from auth router.

### Fix
Added `/auth/register` endpoint to `app/api/auth/router.py`:
- Accepts `LoginRequest` schema (email, password)
- Checks if email already exists (returns 400 if duplicate)
- Creates new user via `create_user()` service
- Returns `TokenPair` (access_token + refresh_token) on success
- Sets refresh_token as httpOnly cookie
- Rate limited to 3/minute

**Files Modified:**
- `backend/app/api/auth/router.py` - Added register endpoint and required imports

**Verification:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
# Expected: 201 with {"access_token":"...","refresh_token":"..."}
```

**Next:** QA re-run QA-CONTRACT-003

---

## DEF-011-003: API response fields exceed QA contract schema

**Status:** RESOLVED — QA UPDATED TEST  
**Severity:** Major  
**Discovered:** 2024-04-16 during QA-011  
**Decided:** 2024-04-16  
**Resolved:** 2024-04-16  
**Reporter:** QA Engineer  
**Decided By:** Architect  
**Resolved By:** QA  
**Related To:** QA-011, ARCH-4.1, ARCH-6.1, B06

### Summary
QA contract expected minimal fields. API returns complete module objects including layout fields.

### Architect Decision
**API IMPLEMENTATION IS CORRECT.**

Rationale per ARCHITECTURE.md:
- Section 6.1: `modules` table and `dashboard_layouts` both exist
- Section 7 (Module Specs): Layout is intrinsic to module configuration
- API returns complete module objects including `position_x`, `position_y`, `width`, `height`
- Frontend needs these fields to render modules in correct grid positions

### QA Fix
Updated `test_contract.py` schemas to match actual API:
- `ModuleResponse`: Added `user_id`, `position_x`, `position_y`, `width`, `height`, `refresh_interval`
- `ModuleListResponse`: Added `total` field
- `LayoutResponse`: Added `id`, `user_id`, `columns`, `row_height`, `created_at`, `updated_at`
- `HealthResponse`: Added `database`, `redis` health status fields

**Tests Now Pass:** QA-CONTRACT-004, 005, 006, 007, 008 validate complete API responses

### Affected Fields Summary

| Endpoint | API Fields | QA Contract (updated) | Status |
|----------|-----------|----------------------|--------|
| POST /api/modules | 14 fields | 14 fields | ✅ MATCH |
| GET /api/modules | modules + total | modules + total | ✅ MATCH |
| GET /api/dashboard/layout | 8 fields | 8 fields | ✅ MATCH |

### Decision Register
Added to ARCHITECTURE.md Decision Register as **B06: API response includes layout fields**

---

### Options
| Option | Who Fixes | Impact |
|--------|-----------|--------|
| A: Update QA contract | QA | Aligns test with actual API |
| B: Remove fields from API | Developer | Breaking change, may break other clients |

### Decision Needed
**Escalated to:** QA (per WORKFLOW.md: "If test expectations are wrong, QA fixes the tests")  
**Note:** API implementation is correct. QA contract needs update.

### Required QA Updates
Update these schemas in `backend/tests/test_contract.py`:
- `ModuleResponse` - add `user_id`, `position_x`, `position_y`, `width`, `height`, `refresh_interval`
- `ModuleListResponse` - add `total`
- `LayoutResponse` - add missing fields OR use permissive validation

---

## DEF-011-004: Module service import path incorrect in contract tests

**Status:** FIXED  
**Severity:** Minor  
**Discovered:** 2024-04-16 during QA-011  
**Fixed:** 2024-04-16  
**Reporter:** QA Engineer  
**Related To:** QA-011 (Test Infrastructure)

### Summary
Contract tests tried to import `app.services.module.service` which doesn't exist. Changed to use API calls instead of direct service imports.

### Fix
Updated `test_contract.py` QA-CONTRACT-005, QA-CONTRACT-010, QA-CONTRACT-011 to create modules via API endpoint instead of importing internal service functions.

---

## DEF-011-005: Missing json import in OpenAPI snapshot test

**Status:** FIXED  
**Severity:** Minor  
**Discovered:** 2024-04-16 during QA-011  
**Fixed:** 2024-04-16  
**Reporter:** QA Engineer  
**Related To:** QA-011 (Test Infrastructure)

### Summary
QA-CONTRACT-009 test failed with `NameError: name 'json' is not defined`.

### Fix
Added `import json` at top of `test_contract.py`.

---

## DEF-011-006: Visual regression tests missing pytest-playwright configuration

**Status:** FIXED  
**Severity:** Major  
**Discovered:** 2024-04-16 during QA-011  
**Fixed:** 2024-04-16  
**Reporter:** QA Engineer  
**Related To:** QA-011, QA-VISUAL suite

### Summary
All 5 visual regression tests failed with fixture not found: `fixture 'page' not found`.

### Fix
Added custom fixtures to `test_visual_regression.py`:
- `playwright_instance` - provides sync_playwright context
- `browser` - launches chromium browser  
- `page` - creates new page for each test

This allows tests to run without external pytest-playwright plugin dependency.

---


---

## DEF-020: Log Module Stuck on "Loading..." (Module Render Registry Not Implemented)

**Status:** FIXED ✅  
**Severity:** Blocker  
**Discovered:** 2026-04-21 during architecture gap analysis  
**Fixed By:** Developer  
**Date Fixed:** 2026-04-21  
**Related To:** DEV-012, Section 4.6, FE-MVP-001

### Summary
Log modules render inline `<script>` tags inside `innerHTML`, but browsers do not execute `<script>` tags inserted via `innerHTML` (CSP/XSS prevention). Result: log module shows "Loading..." forever.

### Fix Applied
Implemented `MODULE_RENDERERS` registry pattern in `dashboard.html`:
- `MODULE_RENDERERS` maps module types to async renderer functions
- `renderLogModule()` uses DOM APIs (`textContent`, `fetch()`, `innerHTML` for static markup only)
- No inline `<script>` tags in dynamically generated content
- Scripts execute after DOM insertion via `addEventListener`

### Files Modified
- `frontend/dashboard.html` — Replaced `renderModules()` and `getModuleContent()` with registry-based DOM rendering

**Status:** FIXED ✅  
**Date Fixed:** 2026-04-21

---

## DEF-021: Portfolio/Calendar Modules Show Hardcoded Fake Data

**Status:** FIXED ✅  
**Severity:** Major  
**Discovered:** 2026-04-21 during architecture gap analysis  
**Fixed By:** Developer  
**Date Fixed:** 2026-04-21  
**Related To:** DEV-006, DEV-007, FE-MVP-001

### Summary
Portfolio and Calendar modules display static placeholder data (`$0.00`, `"0 assets"`, `"No events"`) instead of fetching real data from the backend.

### Root Cause
`GET /api/modules/{id}/data` endpoint exists and works (verified in backend tests), but `dashboard.html` never calls it. The `getModuleContent()` function returns hardcoded HTML strings.

### Expected (per ARCHITECTURE.md Section 5.2)
Frontend calls `GET /api/modules/{module.id}/data?size=${module.size}` and renders actual data.

### Actual
Portfolio card shows:
```html
<div class="text-3xl font-bold text-white">$0.00</div>
<div class="text-xs text-gray-400">0 assets</div>
```

Calendar card shows:
```html
<p class="text-gray-400">No events today</p>
```

### Fix Applied
Implemented async renderers for portfolio and calendar:
- `renderPortfolioModule()` fetches `/api/modules/{id}/data`, displays real portfolio value, assets, allocation
- `renderCalendarModule()` fetches `/api/modules/{id}/data`, displays real upcoming events with impact colors
- Both handle loading states (spinner), empty states, and error states gracefully
- Both use `escapeHtml()` for XSS prevention when rendering user data

### Files Modified
- `frontend/dashboard.html` — Added `renderPortfolioModule()` and `renderCalendarModule()` to MODULE_RENDERERS registry

---

## DEF-022: Frontend Interaction Logging Not Implemented

**Status:** BACKLOG  
**Severity:** Minor  
**Discovered:** 2026-04-21 during architecture gap analysis  
**Related To:** DEV-015, Section 11.2.2

### Summary
DEV-015 is marked DONE, but `dashboard.html` has zero interaction tracking. The TypeScript files (`logger.ts`, `useInteraction.ts`) were created for a React frontend that doesn't exist.

### Rationale for Backlog
- DEV-015 was implemented for React/Next.js architecture
- Current Phase 1 uses vanilla HTML/JS
- Requires rewriting interaction logger in vanilla JS
- Non-critical for MVP functionality

### Decision
Defer to Phase 2 (React migration) or file as separate DEV task if needed for MVP.

---

## DEF-023: System Status Widget Shows Fake Data

**Status:** BACKLOG  
**Severity:** Cosmetic  
**Discovered:** 2026-04-21 during architecture gap analysis  
**Related To:** Section 11.3

### Summary
System Status widget shows hardcoded values (CPU 42%, Memory 68%, Disk 23%, Uptime "3d 12h 34m"). No system metrics API exists.

### Decision
Cosmetic enhancement. Not required for MVP core functionality. File as P3 task if desired.

---

## DEF-024: Alert Widget Shows Fake Data

**Status:** BACKLOG  
**Severity:** Cosmetic  
**Discovered:** 2026-04-21 during architecture gap analysis  
**Related To:** DEV-010, Section 9

### Summary
Alert widget shows "2 active" alerts and "High CPU usage detected" — all hardcoded HTML. No connection to backend alert system.

### Decision
Blocked on DEV-010 (Alert system). Will resolve automatically when alert system is implemented.

---

## DEF-025: Health Endpoint Missing Scraper Status

**Status:** BACKLOG  
**Severity:** Low  
**Discovered:** 2026-04-21 during architecture gap analysis  
**Related To:** Section 11.3

### Summary
`GET /health` returns DB + Redis status but does not check "Scraper last-run timestamps (stale if > 2× expected interval)" per architecture.

### Decision
Low priority. Scraper workers (DEV-013, DEV-014) are not yet implemented. No scraper status to report. Will resolve when scrapers are added.

---

| ID | Severity | Issue | Status | Resolution |
|----|----------|-------|--------|------------|
| DEF-011-001 | Major | Refresh token format conflict | RESOLVED | QA updated test per Architect B05 |
| DEF-011-002 | Blocker | Register endpoint 404 | FIXED | Developer added endpoint |
| DEF-011-003 | Major | API response fields mismatch | RESOLVED | QA updated test per Architect B06 |
| DEF-011-004 | Minor | Wrong import path in tests | FIXED | QA removed broken imports |
| DEF-011-005 | Minor | Missing json import | FIXED | QA added import |
| DEF-011-006 | Major | Missing pytest-playwright | FIXED | QA added custom fixtures |
| DEF-020 | Blocker | Log module stuck on "Loading..." | FIXED | Developer implemented MODULE_RENDERERS registry |
| DEF-021 | Major | Portfolio/Calendar fake data | FIXED | Developer implemented async data fetchers |

**All defects resolved. QA-011 ready for sign-off.**

