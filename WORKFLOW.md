# Team Workflow: Personal Monitoring Dashboard

**Version:** 1.0  
**Effective Date:** 2024-01-15  
**Team:** Architect (Lead), Developer, QA

---

## 1. Work Artifacts

### 1.1 Single Source of Truth
| Artifact | Location | Owner | Purpose |
|----------|----------|-------|---------|
| **Architecture** | `ARCHITECTURE.md` | Architect | Technical blueprint. All implementation references this. |
| **Workflow** | `WORKFLOW.md` (this file) | Architect | How the team works together. |
| **Task Board** | `TASKS.md` | Architect | Active work items, assignments, status. |
| **Decision Log** | `DECISIONS.md` | Architect | Why decisions were made. Updated when architecture changes. |
| **Defect Tracker** | `DEFECTS.md` | QA | Bug reports, reproduction steps, resolution status. |

### 1.2 Artifact Rules
- **Never work from memory.** If it is not in `ARCHITECTURE.md`, it does not exist.
- **Architect updates `ARCHITECTURE.md` first.** Then notifies team of changes.
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
| State | Meaning | Who Moves |
|-------|---------|-----------|
| **BACKLOG** | Work identified but not assigned | Architect |
| **ASSIGNED** | Task assigned to Developer or QA | Architect |
| **IN_PROGRESS** | Work actively being done | Developer/QA |
| **BLOCKED** | Cannot proceed without input | Developer/QA |
| **UNBLOCKED** | Blocker resolved | Architect |
| **IN_REVIEW** | Deliverable complete, ready for review | Developer/QA |
| **DEFECTS_FOUND** | QA found issues, returned to Developer | QA |
| **FIXED** | Developer addressed defects | Developer |
| **DONE** | Accepted by Architect, merged | Architect |

### 2.3 Task ID Format
- `ARCH-XXX`: Architecture tasks (blueprint updates)
- `DEV-XXX`: Development tasks (code implementation)
- `QA-XXX`: QA tasks (test writing, validation)
- `DEF-XXX`: Defects (bug reports)

---

## 3. Daily Workflow

### 3.1 Morning Assignment (Architect → Team)
```
Architect reviews TASKS.md
         ↓
[For each ready task]
         ↓
Architect spawns/assigns to Developer or QA
         ↓
Team member acknowledges, asks clarifying questions
         ↓
Work begins
```

### 3.2 Work Execution (Developer/QA)
```
Pick up ASSIGNED task
         ↓
Move to IN_PROGRESS (update TASKS.md)
         ↓
Implement / Test per ARCHITECTURE.md spec
         ↓
[If ambiguity found]
         ↓
Report BLOCKED to Architect with specific question
         ↓
[If completed]
         ↓
Move to IN_REVIEW, notify Architect
```

### 3.3 Review Cycle (Architect → QA)
```
Developer marks DEV task IN_REVIEW
         ↓
Architect does structural review (15 min max)
         ↓
Architect assigns QA task to validate the work
         ↓
QA executes test plan
         ↓
[If defects found]
         ↓
QA files DEF in DEFECTS.md
QA moves DEV task to DEFECTS_FOUND
         ↓
Developer fixes, moves to FIXED
QA retests
         ↓
[If no defects]
         ↓
QA marks task DONE
Architect merges/closes
         ↓
[Before next DEV task assigned]
         ↓
Architect assigns QA-REG: run full CI / regression suite
         ↓
[If CI green]
         ↓
Next DEV task can begin
[If CI red]
         ↓
Developer fixes, re-runs CI until green
```

---

## 4. Communication Protocols

### 4.1 Handoff Messages

**Architect → Developer (New Task):**
```
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
BLOCKER: DEV-001
ISSUE: [Specific problem]
TRIED: [What you already attempted]
OPTIONS CONSIDERED:
A. [Option A with pros/cons]
B. [Option B with pros/cons]
RECOMMENDATION: [Which option you prefer and why]
```

**Developer → Architect (Complete):**
```
COMPLETE: DEV-001
DELIVERABLE: [What was built]
LOCATION: [File paths, URLs]
NOTES: [Where architecture was unclear, suggestions for improvement]
READY FOR: QA review
```

**QA → Developer (Defect):**
```
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
2. Architect reviews structure
3. QA validates thoroughly
4. Architect merges to main
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
**Rule:** Developer stops work immediately. Reports to Architect.
**Architect decides:**
- A. Complete task as-is, new work becomes new task
- B. Revise task scope, update acceptance criteria
- C. Cancel task, remove from backlog

### 6.2 Architecture Proven Wrong
**Rule:** Developer stops, reports specific flaw.
**Architect:**
1. Acknowledges within 4 hours
2. Revises `ARCHITECTURE.md` with new design
3. Updates `DECISIONS.md` with rationale for change
4. Notifies team of revised approach
5. Resumes work with new spec

### 6.3 External API Breaks (Yahoo, CoinGecko, etc.)
**Rule:** This is not a code defect. This is an operational issue.
**Architect:**
1. Confirms circuit breaker is working as designed
2. Decides: Wait for fix vs implement fallback vs disable module temporarily
3. Updates `DECISIONS.md` with incident record
4. May create new task to add fallback data source

### 6.4 Team Member Unresponsive
**Rule:** Architect checks `subagents list` for status.
**If agent stuck:**
1. Attempt `subagents steer` with clarifying question
2. If no response in 24 hours, kill and respawn with simplified task
3. Document in `DECISIONS.md` if pattern emerges

---

## 7. Quality Gates

### 7.1 Definition of Done
A task is DONE when:
- [ ] Deliverable matches ARCHITECTURE.md spec
- [ ] Code is committed to repository
- [ ] Unit tests pass (Developer)
- [ ] QA validation passes (QA sign-off)
- [ ] Architect structural review passes
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

## 9. Meeting Cadence

### 9.1 Async-First
Default is async communication via task updates.

### 9.2 Sync Touchpoints
| Meeting | Trigger | Duration | Attendees |
|---------|---------|----------|-----------|
| **Kickoff** | Phase 1 starts | 30 min | All |
| **Mid-phase check** | 50% tasks complete | 15 min | All |
| **Phase 1 retrospective** | Phase 1 done | 30 min | All |

### 9.3 Ad-hoc Sync
Called by Architect if:
- Major architecture revision needed
- Blocker affects multiple tasks
- External dependency changes (API breaks, etc.)

---

## 10. Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2024-01-15 | Initial workflow | Architect |

---

**Next Step:** Create `TASKS.md` with Phase 1 work breakdown, then spawn Developer and QA agents.
