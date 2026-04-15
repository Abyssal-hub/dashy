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

**Status:** FIXED  
**Severity:** Major  
**Discovered:** 2024-01-15 during QA-REG-002  
**Fixed:** 2024-01-15 by QA  
**Related To:** QA-REG-002, test_mvp_flows.py, test_modules.py

### Summary
Test files had conflicting expectations for HTTP status codes.

### Conflicts
| Scenario | test_mvp_flows.py | test_modules.py |
|----------|------------------|-----------------|
| Unauthorized | 403 | 401 |
| Invalid module type | 422 | 400 |

### Resolution
QA fixed test_modules.py to match correct HTTP semantics and test_mvp_flows.py (MVP acceptance criteria):
- Changed 401 → 403 for missing authentication
- Changed 400 → 422 for invalid module type (validation error)

Also fixed rate limiting issue by:
- Adding `rate_limit_enabled = False` in conftest.py (before app import)
- Implementing conditional rate limiting in `app/core/limiter.py`

### Files Modified
- `backend/tests/test_modules.py`: Updated expected status codes
- `backend/tests/conftest.py`: Added `rate_limit_enabled = False` for tests
- `backend/app/core/limiter.py`: Added conditional rate limiting support

### Result
- All 59 tests now pass (2 skipped)
- QA-REG-002 signed off

---

## Template

### DEF-XXX: Title
**Status:** OPEN / FIXED / CLOSED  
**Severity:** Blocker / Major / Minor / Cosmetic  
**Discovered:** YYYY-MM-DD  
**Reporter:** (who found it: Developer/QA/Architect)  
**Owner:** (who fixes it: Developer/QA/Architect)  
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
