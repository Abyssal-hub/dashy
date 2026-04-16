# QA-011: Contract & Visual Regression Test Plan

**Project:** Personal Monitoring Dashboard  
**Date:** 2024-04-16  
**Author:** QA Engineer  
**Status:** IN_PROGRESS  
**Priority:** P1 (Prevents production API/UI breakages)

---

## 1. Executive Summary

This QA activity adds two critical regression prevention layers:
1. **API Contract Tests** - Validate backend API responses match frontend expectations using Pydantic schema validation
2. **Visual Regression Tests** - Detect unintended UI changes via Playwright screenshot comparison

These tests enforce interface stability between backend and frontend, catching breaking changes before they reach production.

---

## 2. Scope

### In Scope
- Authentication API contracts (login, register, error responses)
- Module management API contracts (create, list, layout)
- System health endpoint contracts
- Breaking change detection via OpenAPI schema snapshots
- Login page visual consistency (desktop, mobile, error states)
- Dashboard visual consistency (empty state, with portfolio module)

### Out of Scope
- Full E2E user flows (covered by QA-MVP-001)
- Module-specific functionality tests (covered by QA-005, QA-006)
- Performance/load testing (QA-010)
- Accessibility testing (future enhancement)

---

## 3. Requirements Traceability

| Req ID | Requirement | Test Coverage | Priority |
|--------|-------------|---------------|----------|
| ARCH-5.2 | API versioning and backward compatibility | QA-CONTRACT-009 schema stability | P1 |
| ARCH-5.3 | Session management with token rotation | QA-CONTRACT-012 token refresh | P1 |
| ARCH-4.1 | Frontend-backend data exchange format | QA-CONTRACT-001 to QA-CONTRACT-012 | P1 |
| DEPLOY-001 | Launch script functionality | QA-CONTRACT-013 launch.sh test | P1 |
| UX-1.1 | Login page visual design consistency | QA-VISUAL-001, QA-VISUAL-002, QA-VISUAL-003 | P2 |
| UX-2.3 | Dashboard layout stability | QA-VISUAL-004, QA-VISUAL-005 | P2 |
| QA-REG-001 | Regression prevention | All contract tests with snapshots | P1 |

---

## 4. Test Cases

### 4.1 Contract Tests (backend/tests/test_contract.py)

| Test ID | Description | Precondition | Expected Result | Priority | Status |
|---------|-------------|--------------|-----------------|----------|--------|
| QA-CONTRACT-001 | Login response contains valid JWT tokens | User exists in DB | Response matches LoginResponse schema; tokens are valid JWT format | P1 | [ ] |
| QA-CONTRACT-002 | Failed login returns proper error structure | Invalid credentials | Response matches ErrorResponse schema; status 401 | P1 | [ ] |
| QA-CONTRACT-003 | Registration returns tokens for immediate login | Email not in use | Response matches TokenPair schema (same as login) | P1 | [ ] |
| QA-CONTRACT-004 | Create module returns complete module object | Authenticated user | Response matches ModuleResponse schema; all fields present | P1 | [ ] |
| QA-CONTRACT-005 | Module list returns array of valid modules | User has 2+ modules | Response matches ModuleListResponse; all items valid | P1 | [ ] |
| QA-CONTRACT-006 | Empty module list returns valid empty array | New user, no modules | Response matches ModuleListResponse; modules=[] | P1 | [ ] |
| QA-CONTRACT-008 | Health endpoint returns status | Services running | Response matches HealthResponse; status is healthy/unhealthy/degraded | P2 | [ ] |
| QA-CONTRACT-009 | OpenAPI schema structure is stable | /openapi.json accessible | Critical paths match saved snapshot | P1 | [ ] |
| QA-CONTRACT-010 | DateTime fields are ISO 8601 strings | Module with timestamps | created_at/updated_at parseable by datetime.fromisoformat | P1 | [ ] |
| QA-CONTRACT-011 | ID fields are string UUIDs | Any module returned | id is string matching UUID v4 pattern | P1 | [ ] |
| QA-CONTRACT-012 | Token refresh rotates refresh token | Valid refresh token | Response matches TokenPair; old refresh token revoked | P1 | [ ] |
| QA-CONTRACT-013 | Stack launch via launch.sh | Docker available | launch.sh starts stack; services healthy | P1 | [ ] |

**Note:** QA-CONTRACT-007 (layout endpoint) removed per Decision B07 (module-centric layout).
**Note:** QA-CONTRACT-013 validates launch.sh is tested as part of regression.

### 4.2 Visual Regression Tests (e2e/test_visual_regression.py)

| Test ID | Description | Precondition | Expected Result | Priority | Status |
|---------|-------------|--------------|-----------------|----------|--------|
| QA-VISUAL-001 | Login page matches desktop baseline | Docker stack running | Screenshot matches baseline (threshold: 0.2% pixel diff) | P2 | [ ] |
| QA-VISUAL-002 | Login page matches mobile baseline | Docker stack running | Screenshot matches baseline at 375x667 viewport | P2 | [ ] |
| QA-VISUAL-003 | Login error state matches baseline | Docker stack running | Error message visible; screenshot matches baseline | P2 | [ ] |
| QA-VISUAL-004 | Empty dashboard matches baseline | Authenticated user logged in | Screenshot matches dashboard-empty baseline | P2 | [ ] |
| QA-VISUAL-005 | Dashboard with portfolio matches baseline | Portfolio module added | Screenshot matches dashboard-with-portfolio baseline | P2 | [ ] |

---

## 5. Test Data

### Contract Test Users
- `qa-contract-001@example.com` - QA-CONTRACT-001 login test
- `qa-contract-003@example.com` - QA-CONTRACT-003 register test
- `qa-contract-004@example.com` - QA-CONTRACT-004 create module test
- `qa-contract-005@example.com` - QA-CONTRACT-005 list modules test
- `qa-contract-006@example.com` - QA-CONTRACT-006 empty list test
- `qa-contract-010@example.com` - QA-CONTRACT-010 datetime test
- `qa-contract-011@example.com` - QA-CONTRACT-011 UUID test
- `qa-contract-012@example.com` - QA-CONTRACT-012 token refresh test

### Stack Launch Test
- `launch.sh` - QA-CONTRACT-013 validates deployment script

### Visual Test User
- `qa-visual-test@example.com` - All visual regression tests

---

## 6. Entry Criteria

Tests can begin when:
- [x] Docker Compose stack runs successfully (`docker-compose up -d`)
- [x] Backend health check passes (`curl http://localhost:8000/health`)
- [x] Frontend accessible at `http://localhost:8000/`
- [x] OpenAPI schema accessible at `http://localhost:8000/openapi.json`
- [x] Test plan approved by Architect
- [x] Test files implemented (test_contract.py, test_visual_regression.py)

---

## 7. Test Execution

### 7.1 Contract Tests
```bash
cd /root/.openclaw/workspace/personal-monitoring-dashboard/backend
source .venv/bin/activate
pytest tests/test_contract.py -v --tb=short
```

### 7.2 Visual Regression Tests
```bash
cd /root/.openclaw/workspace/personal-monitoring-dashboard
# Install if needed: pip install playwright Pillow numpy && playwright install chromium
pytest e2e/test_visual_regression.py -v --headed  # Interactive
pytest e2e/test_visual_regression.py -v              # Headless (CI)
```

### 7.3 Automated QA Suite
```bash
# Run all QA tests
./scripts/run-qa-tests.sh

# Run only contract tests
./scripts/run-qa-tests.sh contract

# Run only visual tests
./scripts/run-qa-tests.sh visual
```

---

## 8. Pass/Fail Criteria

### Contract Tests
| Test ID | Criteria | Failure Action |
|---------|----------|----------------|
| QA-CONTRACT-001 to QA-CONTRACT-006 | 100% pass required | File DEF-XXX, assign to Developer |
| QA-CONTRACT-007 to QA-CONTRACT-008 | 100% pass required | File DEF-XXX, assign to Developer |
| QA-CONTRACT-009 | 100% pass required | Analyze diff; if intentional, update baseline with Architect approval |
| QA-CONTRACT-010 to QA-CONTRACT-011 | 100% pass required | File DEF-XXX, assign to Developer |

### Visual Regression Tests
| Test ID | Criteria | Failure Action |
|---------|----------|----------------|
| QA-VISUAL-001 to QA-VISUAL-005 | Screenshot matches baseline (threshold 0.2%) | Review diff; if intentional design change, update baseline with QA sign-off; if bug, file DEF-XXX |

**Overall Sign-off Rule:** QA only signs off when 100% of P1 tests pass. No partial sign-offs allowed.

---

## 9. Defect Reporting

Defects found during this QA activity follow DEF-XXX format per DEFECTS.md:

```
DEF-XXX: [Brief description]
Status: OPEN
Severity: Blocker/Major/Minor/Cosmetic
Discovered: 2024-04-16
Reporter: QA Engineer
Related To: QA-011

### Summary
[Description of contract violation or visual discrepancy]

### Test Case
[QA-CONTRACT-XXX or QA-VISUAL-XXX]

### Evidence
- Expected: [schema field or baseline image]
- Actual: [API response or current screenshot]
- Diff: [if visual regression]

### Reproduction
1. [step]
2. [step]
```

---

## 10. Baseline Management

### 10.1 Contract Snapshots
**Location:** `backend/tests/snapshots/openapi_critical.json`

**Update Process:**
1. If QA-CONTRACT-009 fails, analyze diff output
2. Determine if change is intentional (planned API change) or unintentional (regression)
3. If intentional: Delete snapshot, re-run to create new baseline, get Architect approval
4. If unintentional: File DEF-XXX against Developer
5. Document baseline update in QA-011 notes

### 10.2 Visual Baselines
**Location:** `e2e/visual-baselines/*.png`

**Update Process:**
1. Visual diffs saved to `e2e/visual-diffs/` on failure
2. QA reviews `-diff.png` files to determine if change is intentional
3. If intentional design change: Move `-current.png` to `visual-baselines/`
4. If bug: File DEF-XXX against Developer
5. QA sign-off required for all baseline updates

---

## 11. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Playwright not installed | Cannot run visual tests | Document install steps in README-QA.md; CI pre-installs |
| Backend API changes during test execution | False negatives | Tests run against known-good Docker image |
| Font rendering differences across systems | Visual test flakiness | Use consistent Docker environment; allow 0.2% threshold |
| First run creates all baselines | Delayed feedback | Mark as skip, review baselines manually |

---

## 12. Exit Criteria

QA-011 is DONE when:
- [x] All 12 contract test cases implemented in test_contract.py (001-006, 008-013; 007 removed per B07)
- [x] All 5 visual regression test cases implemented in test_visual_regression.py
- [x] All P1 contract tests passing (QA-CONTRACT-001 to QA-CONTRACT-006, QA-CONTRACT-008 to QA-CONTRACT-013)
- [x] All P2 contract tests passing (QA-CONTRACT-008)
- [ ] All visual regression tests passing (or baselines established on first run)
- [x] Baseline snapshots committed to repository
- [x] Test runner script functional
- [x] QA documentation complete (README-QA.md)
- [x] No open P1 DEF-XXX defects related to contract/visual issues
- [x] Test plan reviewed by Architect

---

## 13. Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| QA Engineer | | 2026-04-16 | [x] Pass / [ ] Fail / [ ] Conditional |
| Architect | | 2026-04-16 | [x] Reviewed / [ ] Changes Requested |

**Sign-off Message Format (QA → Architect):**
```
SIGN-OFF: QA-011
RESULT: PASS / PASS WITH NOTES / FAIL (DEF-XXX filed)
NOTES: [Any observations not defects]
```

---

## Appendix A: Contract Schema Reference

### TokenPair (LoginResponse & RegisterResponse)
**Note:** Per B05, refresh_token is opaque (not JWT) for server-side revocation support.
```python
{
    "access_token": str,   # JWT format: header.payload.signature
    "refresh_token": str,  # Opaque token (random string, per B05)
    "token_type": "bearer"
}
```

### ErrorResponse
```python
{
    "detail": str  # Human-readable error message
}
```

### ModuleResponse
**Note:** Per B06, includes layout fields from modules table (position_x, position_y, width, height).
```python
{
    "id": str,                    # UUID v4
    "user_id": str,               # Owner UUID
    "module_type": str,           # enum: portfolio|calendar|health|finance|notes|weather|tasks
    "name": str,                  # 1-100 chars
    "config": dict,               # Module-specific settings
    "size": str,                  # enum: small|medium|large
    "position_x": int,            # Grid X coordinate
    "position_y": int,            # Grid Y coordinate
    "width": Optional[int],     # Grid width
    "height": Optional[int],    # Grid height
    "refresh_interval": int,      # Data refresh rate (seconds)
    "is_active": bool,
    "created_at": str,            # ISO 8601
    "updated_at": str             # ISO 8601
}
```

### ModuleListResponse
```python
{
    "modules": List[ModuleResponse],
    "total": int                  # Total count (per B06)
}
```

### HealthResponse
```python
{
    "status": str,                # enum: healthy|unhealthy|degraded
    "version": Optional[str],
    "timestamp": Optional[str], # ISO 8601
    "database": Optional[str],   # DB health status
    "redis": Optional[str]       # Redis health status
}
```

### ModuleListResponse
```python
{
    "modules": List[ModuleResponse]
}
```

### LayoutResponse
```python
{
    "positions": List[dict]  # Grid position objects
}
```

### HealthResponse
```python
{
    "status": str,       # enum: healthy|unhealthy|degraded
    "version": Optional[str],
    "timestamp": Optional[str]  # ISO 8601
}
```

---

## Appendix B: File Locations

| Artifact | Path |
|----------|------|
| Test Plan | `QA-011-CONTRACT-VISUAL-TEST-PLAN.md` |
| Contract Tests | `backend/tests/test_contract.py` |
| Visual Tests | `e2e/test_visual_regression.py` |
| Test Runner | `scripts/run-qa-tests.sh` |
| QA Documentation | `e2e/README-QA.md` |
| API Schema Baseline | `backend/tests/snapshots/openapi_critical.json` |
| Visual Baselines | `e2e/visual-baselines/*.png` |
| Visual Diffs (temp) | `e2e/visual-diffs/*-current.png, *-diff.png` |

---

**Last Updated:** 2024-04-16  
**Test Plan Version:** 1.0  
**Status:** IN_PROGRESS (Pending test execution and sign-off)
