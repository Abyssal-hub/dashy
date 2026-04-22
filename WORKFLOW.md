# Development Workflow

**Project:** Personal Monitoring Dashboard  
**Reference:** `ARCHITECTURE.md` is the single source of truth. All work must align with architecture decisions.

---

## 1. Roles & Responsibilities

**All team members are senior practitioners with 30+ years of experience in their domain and deep expertise in collaborative web-application delivery.**

| Role | Experience Level | Can Modify Tests? | Core Responsibility |
|------|------------------|-------------------|---------------------|
| **Developer** | Senior (30+ years software engineering) | ❌ NO | Implement features per architecture. Tests are the specification. |
| **UI/UX Designer** | Senior (30+ years product design) | ❌ NO | Design user flows, define UX requirements, review E2E scenarios. |
| **QA** | Senior (30+ years quality engineering) | ✅ YES | Write/update tests. Fix test expectations when they are incorrect. |
| **Architect** | Senior (30+ years systems architecture) | ✅ YES | Resolve specification conflicts. Approve architecture changes. |

---

## 2. Workflow by Work Type

### 2.1 Backend-Only Work

```
Ticket Created → Developer implements → Developer writes unit tests
                    ↓
              QA writes integration tests (if new endpoint/contract)
                    ↓
              All tests pass → Merge
```

**Rules:**
- Developer writes unit tests for new handlers/services.
- QA writes integration tests for new API contracts.
- Architecture compliance is verified by existing tests.

### 2.2 Frontend Work — **REQUIRES UI/UX + ARCHITECT + QA COLLABORATION**

```
Ticket Created → UI/UX designs flow + discusses feasibility with Architect
         ↓                                    ↓
    Architecture review ← ← ← ← ← ← ← ← ← ← ←
         ↓
    QA drafts E2E user journey tests
         ↓
    Developer implements frontend
         ↓
    E2E tests must pass before merge
         ↓
    All tests pass → Merge
```

**Rules (NEW REQUIREMENT):**
1. **UI/UX Designer** defines the user flow, then **discusses feasibility with the Architect** before finalizing designs.
   - If the flow requires new data models, API endpoints, or architectural changes, the Architect decides if it's feasible.
   - If the architecture can't support the UX flow, UI/UX and Architect iterate together until they agree.
2. **QA** writes E2E user journey tests covering the flow before or alongside implementation.
3. **Developer** implements frontend following the **architecture blueprint** (`ARCHITECTURE.md`).
4. **E2E tests are the definition of done** — if the test passes, the feature is complete.
5. **Developer never modifies E2E tests** to make code pass. If tests fail due to wrong expectations, escalate to QA.

### 2.3 Bug Fix / Defect Work

```
Defect Reported → QA reproduces → Developer fixes
                        ↓
                  Regression test added by QA
                        ↓
                  All tests pass → Merge
```

**Rules:**
- Every defect gets a regression test before merge.
- Developer does not modify existing tests.

---

## 3. E2E Test Requirements for Frontend Work

### 3.1 When E2E Tests Are Required

Any work touching the **frontend** MUST include E2E user journey tests:

- New module type added
- Module rendering changes
- Dashboard layout changes
- New user-facing feature
- Data flow changes (how frontend consumes backend)
- Authentication/authorization flow changes

### 3.2 E2E Test Must Cover

Per the UX designer audit, E2E tests must validate:

| Category | Scenarios |
|----------|-----------|
| **Happy Path** | Full user journey: signup → add modules → populate data → verify live data |
| **Empty State** | Module with no data shows helpful state, not blank box |
| **Error State** | API failures show friendly messages, not raw JSON/traceback |
| **Data Consistency** | Auto-refresh does not break DOM structure |
| **Responsive Density** | Different module sizes return appropriate data amounts |
| **State Persistence** | Refresh, resize, reposition — all survive browser reload |
| **Security** | Cross-user isolation, token expiry, unauthorized access |
| **Performance** | Large datasets load within acceptable time |
| **Config Updates** | Changes reflect immediately without page refresh |

### 3.3 E2E Test Template

See existing tests for patterns:
- `tests/test_mvp_flows.py` — Core user flows
- `tests/test_def020_def021_e2e.py` — Full user journey with real data
- `tests/test_ux_scenarios_e2e.py` — UX edge cases and error states

**Every E2E test must:**
1. Follow a real user UX flow (not just API calls)
2. Populate with real data (not hardcoded placeholders)
3. Verify the API returns values computed from the database
4. Assert on the full response structure (not just status code)

---

## 4. Architecture Compliance

### 4.1 Frontend Must Follow Architecture Blueprint

**Before implementing frontend work:**

1. Read `ARCHITECTURE.md` Section 4 (Frontend Architecture)
2. Read `ARCHITECTURE.md` Section 6 (Data Models) — database fields will be in API responses
3. Verify with existing API code — see actual response structures
4. Check `ARCHITECTURE.md` decisions — they capture deliberate trade-offs

**Golden Rule:** Architecture is the single source of truth. Frontend implementation must follow it; tests verify compliance.

### 4.2 Frontend-Backend Contract

The contract is defined in `ARCHITECTURE.md` Section 12 (API Contract):

- `GET /api/modules/{id}/data` returns structured data per module type
- `PortfolioHandler` returns `assets[]`, `total_value`, `day_change`, etc.
- `CalendarHandler` returns `events[]` with time ranges
- `LogHandler` returns `logs[]`, `severity_counts`, pagination metadata

**Frontend must consume this contract.** Bypassing it (e.g., calling `GET /api/logs` directly) creates technical debt.

### 4.3 Why UI/UX Must Discuss with the Architect

**Real examples from this project where UI/UX + Architect collaboration was critical:**

| Scenario | UI/UX Wanted | Architecture Said | Resolution |
|----------|-------------|-------------------|------------|
| Portfolio drag-to-reorder | Drag cards between grid positions | `ARCHITECTURE.md` Section 6.1: modules table has `position_x`, `position_y`, `width`, `height` columns | Feasible — already supported |
| Log module live updates | Show new logs streaming in without refresh | Backend `GET /api/modules/{id}/data` exists but `LogHandler` returned hardcoded empty data | Backend handler needed fixing before frontend could consume real data |
| Calendar 7-day vs 365-day view | Different data density at different sizes | `CalendarHandler` didn't accept `size` parameter | Added size-aware date range filtering |
| Cross-user data leak | User A and User B have same-named modules | `ARCHITECTURE.md` uses `user_id` scoped queries but frontend was bypassing `/modules/{id}/data` | Enforced contract compliance |

**Rule:** UI/UX must validate their designs against the architecture before implementation. If the architecture can't support the flow, **either the architecture changes (Architect approves) or the UI/UX adapts (Designer agrees)** — never the Developer hacking around it.

**Anti-pattern:** UI/UX designs a drag-and-drop dashboard layout without checking if the database stores coordinates. Developer ends up storing layout in `localStorage` instead of the database, creating data loss on refresh.

---

## 5. Test Ownership Matrix

| Test Type | Written By | Can Modify |
|-----------|-----------|------------|
| Unit Tests | Developer | Developer |
| Integration Tests | QA (+ Developer support) | QA |
| E2E Tests | QA | QA |
| Regression Tests | QA | QA |

**Escalation Rule:** If a test fails and the developer believes the expectation is wrong, escalate to QA. QA decides whether to fix the test or file a defect.

---

## 6. Definition of Done

For **frontend work**, the definition of done is:

1. ✅ Code implemented per `ARCHITECTURE.md`
2. ✅ Unit tests pass (Developer)
3. ✅ Integration tests pass (QA)
4. ✅ **E2E user journey tests pass (QA + UI/UX reviewed)**
5. ✅ No hardcoded placeholder data in responses
6. ✅ Cross-user isolation verified (if data is user-scoped)
7. ✅ Error states show friendly messages (tested via E2E)

For **backend-only work**, the definition of done is:

1. ✅ Code implemented per `ARCHITECTURE.md`
2. ✅ Unit tests pass (Developer)
3. ✅ Integration tests pass (QA)
4. ✅ No breaking changes to existing API contracts

---

## 8. Tool & Agent Rules

### 8.1 Coding Tasks — Kimi-Coding ACP Harness (MANDATORY)

**Rule:** All coding tasks (implementation, bug fixes, refactoring, test writing) **MUST** be executed via the `kimi-coding` ACP harness.

**Why:**
- Dedicated coding agent with optimized context for code generation
- Parallel execution — I (main agent) retain planning/oversight while Kimi Code handles implementation
- Cleaner separation of concerns: planning vs execution
- Follows GStack methodology: separate planning agent from execution agent

**How:**
1. **I (main agent)** analyze the task, gather context, and prepare requirements
2. **Spawn** `sessions_spawn` with `runtime: "acp"`, `agentId: "kimi"`
3. **Kimi Code** implements the fix/feature in its own session
4. **I verify** results, run tests, and report back to you

**Exceptions:**
- Quick file reads/writes for context gathering (still done by me)
- Running tests and verifying results (I do this)
- Architectural decisions (I coordinate with Architect role)
- Non-code tasks (documentation, planning, analysis — I handle these)

**Example workflow:**
```
User: "Fix the log module bug"
  ↓
Me: Analyze bug → Read files → Identify root cause → Prepare task spec
  ↓
Spawn: sessions_spawn(runtime="acp", agentId="kimi", task="Fix...")
  ↓
Kimi Code: Implements fix in its session
  ↓
Me: Verify fix → Run tests → Commit → Report results
```

- `ARCHITECTURE.md` — Single source of truth for design decisions
- `QA-001-TEST-STRATEGY.md` — Test pyramid and tooling
- `docs/MVP-UX-FLOWS.md` — Manual UX flow documentation
- `tests/test_ux_scenarios_e2e.py` — Automated UX scenario tests
