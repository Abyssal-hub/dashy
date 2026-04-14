# Defect Tracker

**Format:** DEF-XXX: Brief description

---

## DEF-001: Module creation API returns 400 error

**Status:** OPEN  
**Severity:** Major  
**Discovered:** 2024-01-15 during DEV-007 QA  
**Related To:** DEV-004, DEV-007

### Summary
POST `/api/modules` returns HTTP 400 instead of 201 when creating modules. This blocks integration testing of module-dependent features (Calendar, Portfolio events).

### Reproduction Steps
1. Authenticate and get JWT token
2. POST `/api/modules` with valid payload:
   ```json
   {
     "module_type": "calendar",
     "name": "Test Calendar",
     "config": {},
     "size": "medium"
   }
   ```
3. Observe 400 response

### Expected
- HTTP 201 Created
- Response body with created module including `id` field

### Actual
- HTTP 400 Bad Request
- No module created

### Impact
- Blocks QA testing of Calendar event CRUD
- Blocks QA testing of Portfolio asset CRUD
- Core feature (module creation) non-functional

### Notes
- May be related to config validation in ModuleCreate schema
- Check if `config` field validation is too strict
- Handler registration and module type enum may be mismatching

---

## Template

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
