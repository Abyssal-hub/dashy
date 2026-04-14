# Defect Tracker

**Format:** DEF-XXX: Brief description

---

## DEF-001: Module creation API returns 400 error

**Status:** FIXED  
**Severity:** Major  
**Discovered:** 2024-01-15 during DEV-007 QA  
**Fixed:** 2024-01-15  
**Related To:** DEV-004, DEV-007

### Summary
POST `/api/modules` returned HTTP 400 instead of 201 when creating modules. This blocked integration testing of module-dependent features (Calendar, Portfolio events).

### Root Cause
1. Module handlers were never imported, so they weren't registered in the handler registry
2. Modules router expected `current_user: User` object but `get_current_user` returned `user_id: str`
3. Pydantic response schemas expected UUID objects but SQLAlchemy returned UUIDs that weren't being serialized

### Resolution
- Added handler imports in `app/modules/__init__.py` to trigger registration
- Fixed modules router to use `user_id: str` throughout
- Fixed calendar API to use `user_id: str`
- Changed `ModuleResponse.id` and `user_id` from `UUID` to `str`
- Added `field_validator` to `DashboardLayoutResponse` for UUID→str conversion

### Tests
- Calendar tests: 10/10 passing
- MVP flow tests: 4/15 passing (remaining failures are separate issues)

---

## DEF-002: Inconsistent HTTP status code expectations across test files

**Status:** OPEN  
**Severity:** Major  
**Discovered:** 2024-01-15 during QA-REG-002  
**Related To:** QA-REG-002, test_mvp_flows.py, test_modules.py

### Summary
Test files have conflicting expectations for HTTP status codes. Cannot satisfy all tests simultaneously without modifying tests (which violates QA integrity rules).

### Conflicts

| Scenario | test_mvp_flows.py expects | test_modules.py expects |
|----------|--------------------------|------------------------|
| Unauthorized access (no token) | 403 | 401 |
| Invalid module type | 422 | 400 |

### Impact
- QA cannot sign off on 100% pass rate
- Developer cannot fix without violating "don't modify tests" rule
- Production cycle blocked

### Resolution Required
**Architect decision needed:** Which test file is the source of truth?

Option A: test_mvp_flows.py takes precedence (MVP acceptance criteria)
- Code returns: 403 for unauthorized, 422 for invalid module type
- Requires: Update test_modules.py expectations

Option B: test_modules.py takes precedence (module API unit tests)
- Code returns: 401 for unauthorized, 400 for invalid module type
- Requires: Update test_mvp_flows.py expectations

Option C: Follow HTTP semantics strictly
- 401 = missing/invalid auth (current implementation)
- 403 = authenticated but forbidden (not applicable here)
- 422 = validation error (invalid module type)
- Requires: Update both test files to match HTTP semantics

---

### DEF-XXX: Title
**Status:** OPEN / FIXED / CLOSED  
**Severity:** Blocker / Major / Minor / Cosmetic  
**Discovered:** YYYY-MM-DD  
**Related To:** TASK-XXX

### Summary
Brief description of the issue.

### Reproduction Steps
1. Step 1
2. Step 2
3. Step 3

### Expected
What should happen.

### Actual
What actually happens.

### Evidence
Logs, screenshots, API responses.

### Resolution
[To be filled when fixed]
