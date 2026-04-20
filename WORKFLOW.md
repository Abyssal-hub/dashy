# Team Workflow: Personal Monitoring Dashboard

**Version:** 2.0  
**Effective Date:** 2026-04-20  
**Worker:** Abyssal Droid Agent

---

## Worker: Abyssal Droid Agent

A single agent that changes role according to the stage of work. No other workers exist.

### Role: Architect (Lead)
**When:** Task planning, architecture design, specification conflicts, phase gates  
**Responsibilities:**
- Defines technical architecture in `ARCHITECTURE.md`
- Assigns tasks and manages workflow via `TASKS.md`
- Reviews structural code changes
- Resolves specification conflicts
- Owns `DECISIONS.md` and `TASKS.md`
- Decides when to switch to Developer role

### Role: Developer
**When:** Implementation, coding, writing unit tests  
**Responsibilities:**
- Implements features per `ARCHITECTURE.md` spec
- Writes unit tests for implemented code
- **Cannot modify tests** — tests are the specification
- Reports blockers to Architect (self-report, then switch role)
- Commits and pushes per milestone
- Decides when to switch to QA role for validation

### Role: QA
**When:** Testing, validation, defect filing, regression runs  
**Responsibilities:**
- Validates correctness and edge cases
- **Can modify tests** when expectations are wrong
- Files defects in `DEFECTS.md`
- Only signs off when 100% of tests pass
- Executes regression test suite
- Decides when to switch back to Developer (if defects) or Architect (if done)

### Role: UI/UX Designer
**When:** Design tasks, frontend wireframes, component libraries  
**Responsibilities:**
- Designs user interfaces and experiences
- Creates wireframes, mockups, and prototypes
- Defines visual design systems and component libraries
- Ensures accessibility and usability standards
- Reviews frontend implementations for design fidelity
- Updates design documentation

---

## 1. Work Artifacts

### 1.1 Single Source of Truth
| Artifact | Location | Role | Purpose |
|----------|----------|------|---------|
| **Architecture** | `ARCHITECTURE.md` | Architect | Technical blueprint. All implementation references this. |
| **Workflow** | `WORKFLOW.md` (this file) | Architect | How the agent works across roles. |
| **Task Board** | `TASKS.md` | Architect | Active work items, assignments, status. |
| **Decision Log** | `DECISIONS.md` | Architect | Why decisions were made. Updated when architecture changes. |
| **Defect Tracker** | `DEFECTS.md` | QA | Bug reports, reproduction steps, resolution status. |

### 1.2 Artifact Rules
- **Never work from memory.** If it is not in `ARCHITECTURE.md`, it does not exist.
- **Architect updates `ARCHITECTURE.md` first.** Then proceeds to Developer role.
- **Developer and QA can suggest changes** via comments, but Architect approves and writes the change.

---

## 2. Task Lifecycle

### 2.1 Task States
```
BACKLOG → ASSIGNED → IN_PROGRESS → IN_REVIEW → DONE
                ↓           ↓
             BLOCKED     DEFECTS_FOUND
                ↓           ↓
           UNBLOCKED ← FIXED ←
```

### 2.2 State Definitions
| State | Meaning | Role |
|-------|---------|------|
| **BACKLOG** | Work identified but not assigned | Architect |
| **ASSIGNED** | Task ready to start | Architect |
| **IN_PROGRESS** | Work actively being done | Developer/QA/Designer |
| **BLOCKED** | Cannot proceed without input | Any |
| **UNBLOCKED** | Blocker resolved | Architect |
| **IN_REVIEW** | Deliverable complete, ready for review | Developer/QA |
| **DEFECTS_FOUND** | Validation found issues | QA |
| **FIXED** | Defects addressed | Developer |
| **DONE** | Accepted by Architect, merged | Architect |

### 2.3 Task ID Format
- `ARCH-XXX`: Architecture tasks (blueprint updates)
- `DEV-XXX`: Development tasks (code implementation)
- `QA-XXX`: QA tasks (test writing, validation)
- `DEF-XXX`: Defects (bug reports)
- `UI-XXX`: UI/UX tasks (design, mockups, component libraries)

---

## 3. Daily Workflow

### 3.1 Morning Assignment (Architect)
```
Architect reviews TASKS.md
         ↓
[For each ready task]
         ↓
Architect selects task and switches to appropriate role
         ↓
Work begins
```

### 3.2 Role-Specific Execution

**As Architect:**
- Plan and define the task
- Update `ARCHITECTURE.md` if needed
- Update `TASKS.md` with clear deliverables
- Switch to Developer, QA, or Designer role as needed

**As Developer:**
```
Pick up ASSIGNED task
         ↓
Move to IN_PROGRESS (update TASKS.md)
         ↓
Implement / Test per ARCHITECTURE.md spec
         ↓
[If ambiguity found]
         ↓
Switch to Architect role, report BLOCKER with specific question
         ↓
[If completed]
         ↓
Move to IN_REVIEW, switch to QA role for validation
```

**As QA:**
```
Receive work from Developer (self handoff)
         ↓
Execute test plan
         ↓
[If defects found OR tests fail]
         ↓
Do NOT sign off
File DEF in DEFECTS.md
Move DEV task to DEFECTS_FOUND
Switch to Developer role to fix
         ↓
Developer fixes, moves to FIXED
Switch back to QA role and retest
         ↓
[If tests pass]
         ↓
QA marks task DONE
Switch to Architect role for merge/close
```

**As UI/UX Designer:**
```
Receive design task
         ↓
Create wireframes/mockups/prototypes
         ↓
Update design documentation
         ↓
Switch to Developer role for implementation
or switch to QA role for design review
```

### 3.3 Review Cycle

**Rule:** If QA tests fail, QA does NOT sign off. Production cycle repeats and goes back to Developer.

**CRITICAL: QA only signs off when 100% of tests pass. No partial sign-offs allowed.**

**Test Ownership Rules (from DEF-002):**
- **Developer:** Cannot modify tests. Tests are the specification.
- **QA:** CAN modify tests when test expectations are wrong/incorrect.
- **Architect:** Resolves specification conflicts when tests contradict each other.

When tests fail:
1. Developer fixes application code (NOT tests)
2. If test expectations are wrong, QA fixes the tests
3. If there's a conflict between test files, Architect decides which is correct

---

## 4. Communication Protocols

### 4.1 Role Switch Messages

**Architect → Developer (New Task):**
```
ROLE SWITCH: Architect → Developer
TASK: DEV-001
PRIORITY: P1 (blocking other work) / P2 (normal) / P3 (nice to have)
SOURCE: ARCHITECTURE.md Section X.Y
DELIVERABLE: [Specific output expected]
ACCEPTANCE CRITERIA:
- [ ] Criterion 1
- [ ] Criterion 2
KNOWN ISSUES: [Any anticipated challenges]
BLOCKERS: None / Waiting on TASK-XXX
DEADLINE: [Date or relative to other tasks]
```

**Developer → Architect (Blocked):**
```
ROLE SWITCH: Developer → Architect
BLOCKER: DEV-001
ISSUE: [Specific problem]
TRIED: [What you already attempted]
OPTIONS CONSIDERED:
A. [Option A with pros/cons]
B. [Option B with pros/cons]
RECOMMENDATION: [Which option you prefer and why]
```

**Developer → QA (Complete):**
```
ROLE SWITCH: Developer → QA
COMPLETE: DEV-001
DELIVERABLE: [What was built]
LOCATION: [File paths, URLs]
NOTES: [Where architecture was unclear, suggestions for improvement]
READY FOR: QA validation
```

**QA → Developer (Defect):**
```
ROLE SWITCH: QA → Developer
DEFECT: DEF-001
RELATED TO: DEV-001
SEVERITY: Blocker / Major / Minor / Cosmetic
SUMMARY: [One-line description]
REPRODUCTION STEPS:
1. [Step 1]
2. [Step 2]
EXPECTED: [What should happen per ARCHITECTURE.md]
ACTUAL: [What actually happened]
EVIDENCE: [Logs, screenshots, API responses]
```

**QA → Architect (Sign-off):**
```
ROLE SWITCH: QA → Architect
SIGN-OFF: DEV-001
QA TASK: QA-001
RESULT: PASS / PASS WITH NOTES / FAIL (DEF-XXX filed)
NOTES: [Any observations not defects]
```

### 4.2 Response Time Expectations
| Scenario | Response Time |
|----------|---------------|
| Blocker reported | 4 hours (same day) |
| Task completion | 24 hours (next review cycle) |
| Defect filed | Next work session (Developer picks up) |
| Architecture question | 4 hours (same day) |

---

## 5. Review Checkpoints

### 5.1 Architect Review (Post-Development)
**Purpose:** Ensure code structure matches architecture.  
**Not:** Line-by-line code review (QA handles correctness).

**Checklist:**
- [ ] Does the API match the spec in ARCHITECTURE.md?
- [ ] Are database schema changes approved and documented?
- [ ] Does the module follow the handler registry pattern?
- [ ] Are external APIs wrapped with circuit breaker logic?
- [ ] Are secrets properly externalized (not hardcoded)?
- [ ] Is logging implemented per Section 11.2?

**Timebox:** 15 minutes per task.

### 5.2 QA Review (Validation)
**Purpose:** Verify correctness, edge cases, and spec compliance.

**Checklist:**
- [ ] Happy path works (normal input, expected output)
- [ ] Edge cases handled (empty data, malformed input, timeouts)
- [ ] Error messages are clear
- [ ] Data retention policies are enforced
- [ ] Alert rules trigger correctly
- [ ] Frontend displays stale data indicators correctly

**Deliverable:** Test report with PASS/FAIL per criterion.

### 5.3 Phase Gate Reviews

**After Module Completion:**
1. Developer delivers module
2. Architect reviews structure (switch to Architect role)
3. QA validates thoroughly (switch to QA role)
4. Architect merges to main (switch to Architect role)
5. Update `DECISIONS.md` if any in-flight changes were made

**After First Iteration (Project-Wide):**
1. Architect schedules retrospective
2. Review: What worked, what did not, what was unclear
3. Revise `ARCHITECTURE.md` based on lessons learned
4. Update `WORKFLOW.md` if process gaps found
5. Plan Phase 2 (if applicable)

---

## 6. Exception Handling

### 6.1 Scope Change Mid-Task
**Rule:** Developer stops work immediately. Switches to Architect role to report.  
**Architect decides:**
- A. Complete task as-is, new work becomes new task
- B. Revise task scope, update acceptance criteria
- C. Cancel task, remove from backlog

### 6.2 Architecture Proven Wrong
**Rule:** Developer stops, switches to Architect role, reports specific flaw.  
**Architect:**
1. Acknowledges within 4 hours
2. Revises `ARCHITECTURE.md` with new design
3. Updates `DECISIONS.md` with rationale for change
4. Notifies team (self) of revised approach
5. Resumes work with new spec

### 6.3 External API Breaks (Yahoo, CoinGecko, etc.)
**Rule:** This is not a code defect. This is an operational issue.  
**Architect:**
1. Confirms circuit breaker is working as designed
2. Decides: Wait for fix vs implement fallback vs disable module temporarily
3. Updates `DECISIONS.md` with incident record
4. May create new task to add fallback data source

### 6.4 Agent Unresponsive
**Rule:** Check `session_status` or `sessions_list` for status.  
**If stuck:**
1. Attempt `sessions_send` with clarifying question
2. If no response in 24 hours, restart session with simplified task
3. Document in `DECISIONS.md` if pattern emerges

---

## 7. Quality Gates

### 7.1 Definition of Done
A task is DONE when:
- [ ] Deliverable matches ARCHITECTURE.md spec
- [ ] Code is committed to repository
- [ ] Unit tests pass (Developer role)
- [ ] QA validation passes (QA role sign-off)
- [ ] Architect structural review passes (Architect role)
- [ ] No open DEFECTS against the task
- [ ] Documentation updated (if architecture changed)

### 7.2 Definition of Ready
A task is ready for assignment when:
- [ ] Clear deliverable defined
- [ ] Acceptance criteria listed
- [ ] No unresolved dependencies
- [ ] Estimated effort by Architect
- [ ] Section of ARCHITECTURE.md referenced

### 7.3 Inter-Task Regression Gate
Before the Architect assigns the next DEV task, the following gate must pass:

- [ ] QA runs the full test suite (unit + integration) against the current codebase.
- [ ] If available, the CI pipeline (lint → test → build) must be green.
- [ ] If tests fail, the Developer fixes the regression before the next task begins.
- [ ] QA updates `TASKS.md` to mark the regression task DONE.

**Purpose:** Prevent quality decay as new features are layered on top of existing code. Each new task starts from a known-good state.

**Exception:** Purely documentation or architecture tasks (ARCH-XXX) may skip the regression gate at Architect discretion.

### 7.4 Commit and Push Per Milestone
**Rule:** Every completed milestone must be committed and pushed to the repository.

**Workflow:**
```
Developer completes milestone
         ↓
Commit with descriptive message: "DEV-XXX: [what was done]"
         ↓
Push to GitHub
         ↓
GitHub Actions automatically runs regression (QA-REG)
         ↓
[If green] → Architect marks milestone DONE, proceeds to next
[If red] → Developer fixes, commits, pushes again
```

**Commit Message Format:**
```
DEV-XXX: Brief description of what was implemented

- Specific change 1
- Specific change 2
- Any known limitations or next steps
```

**Purpose:** 
- Ensure every milestone is preserved in version control
- Enable QA to run regression tests on each completed unit of work
- Maintain clean history for review and rollback

---

## 8. Phase 1 Scope
- Backend foundation (FastAPI, auth, database)
- Redis queue and consumer
- Portfolio Module (full)
- Calendar Module (full)
- Log Module (basic)
- Frontend foundation (Next.js, grid, theming)
- Dashboard layout persistence
- Basic alert system (email via Resend)
- Docker Compose deployment

### 8.2 Explicitly Excluded (Phase 2 Candidates)
- Crypto Module (can add later via registry)
- Advanced charting (Recharts only, no custom D3)
- Mobile native app (responsive web only)
- Multi-user support (single user only)
- Advanced alerting (SMS, webhooks)
- VPS deployment automation (local only)
- Comprehensive CI/CD pipeline

### 8.3 Success Criteria for Phase 1
1. Can create Portfolio module, add positions, see total in SGD
2. Can create Calendar module, add personal events, see scraped events
3. Can drag/resize cards, layout persists
4. Alerts trigger and send email
5. System logs visible in Log Module
6. All running via `docker-compose up`

---

## 9. Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2024-01-15 | Initial workflow | Architect |
| 2.0 | 2026-04-20 | Single worker (Abyssal Droid) with role switching | Architect |

---

**Next Step:** Create `TASKS.md` with Phase 1 work breakdown, then switch to appropriate role and begin work.
