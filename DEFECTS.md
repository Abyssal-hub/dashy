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

## Summary: QA-011 Defects (ALL RESOLVED)

| ID | Severity | Issue | Status | Resolution |
|----|----------|-------|--------|------------|
| DEF-011-001 | Major | Refresh token format conflict | RESOLVED | QA updated test per Architect B05 |
| DEF-011-002 | Blocker | Register endpoint 404 | FIXED | Developer added endpoint |
| DEF-011-003 | Major | API response fields mismatch | RESOLVED | QA updated test per Architect B06 |
| DEF-011-004 | Minor | Wrong import path in tests | FIXED | QA removed broken imports |
| DEF-011-005 | Minor | Missing json import | FIXED | QA added import |
| DEF-011-006 | Major | Missing pytest-playwright | FIXED | QA added custom fixtures |

**All defects resolved. QA-011 ready for sign-off.**

