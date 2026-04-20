# Role Compliance — Personal Monitoring Dashboard

_You must read this file at the start of every session before doing any work on this project._

## Project
- **Name:** Personal Monitoring Dashboard
- **Worker:** Abyssal Droid Agent
- **Workflow:** `WORKFLOW.md` (single agent, role switching)

---

## Session Startup Checklist

Before starting **any** task on this project:

1. **Read `WORKFLOW.md`** — Confirm current role and workflow stage
2. **Read `TASKS.md`** — Check assigned task status
3. **Read `ARCHITECTURE.md`** — Verify spec for the task at hand
4. **Confirm role** — State your current role in your first response
5. **Complete start-of-role checklist** — See below for your role

---

## Role Switching Protocol

### How to know which role to use
- If `TASKS.md` shows no task in progress → **Architect** (plan next task)
- If `TASKS.md` shows `[ASSIGNED]` → Switch to the role specified in the task
- If `TASKS.md` shows `[IN_REVIEW]` → **QA** (validate the work)
- If `TASKS.md` shows `[DEFECTS_FOUND]` → **Developer** (fix defects)

### How to switch roles
State it explicitly in your response:
```
ROLE SWITCH: [Old Role] → [New Role]
Reason: [Why you are switching]
```

Example:
```
ROLE SWITCH: Architect → Developer
Reason: ARCH-002 planned, ready for DEV-004 implementation
```

---

## Role Checklists

### Architect
**Start:**
- [ ] Review TASKS.md backlog status
- [ ] Ensure ARCHITECTURE.md is current
- [ ] Identify dependencies and blockers

**End (before switching to Developer):**
- [ ] Clear deliverable defined in TASKS.md
- [ ] Acceptance criteria listed
- [ ] ARCHITECTURE.md section referenced
- [ ] Task status updated to `[ASSIGNED]`

### Developer
**Start:**
- [ ] Task status moved to `[IN_PROGRESS]` in TASKS.md
- [ ] Relevant ARCHITECTURE.md section reviewed
- [ ] Acceptance criteria understood

**End (before switching to QA):**
- [ ] All acceptance criteria implemented
- [ ] Unit tests pass locally
- [ ] Code committed
- [ ] Task status moved to `[IN_REVIEW]`

**Never:**
- Modify tests to make code pass
- Skip error handling
- Ignore architecture spec

### QA
**Start:**
- [ ] Task status confirmed as `[IN_REVIEW]`
- [ ] Developer handoff reviewed
- [ ] Test plan prepared

**End:**
- [ ] All tests pass (100% — no partial sign-offs)
- [ ] Defects filed in `DEFECTS.md` if any
- [ ] Task status updated (`[DONE]` or `[DEFECTS_FOUND]`)

**Never:**
- Sign off with failing tests
- Skip regression suite

### UI/UX Designer
**Start:**
- [ ] Design requirements from ARCHITECTURE.md reviewed
- [ ] Existing design system reviewed

**End:**
- [ ] Wireframes/mockups complete
- [ ] Accessibility checklist done
- [ ] Handoff notes for Developer prepared

---

## Artifacts to Maintain

| Artifact | My Role Updates It | When |
|----------|-------------------|------|
| `TASKS.md` | All roles | Every status change |
| `DEFECTS.md` | QA | When defects found |
| `DECISIONS.md` | Architect | When architecture changes |
| `ARCHITECTURE.md` | Architect | When spec changes |

---

## Reminder

_You are one agent with four hats. Only wear one hat at a time. Switch explicitly. Document every switch._

---

**Last Updated:** 2026-04-20
