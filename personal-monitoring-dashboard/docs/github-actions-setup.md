# GitHub Actions Workflow for Extended Development

## Problem
Subagents timeout after 5 minutes due to API rate limits during implementation tasks.

## Solution
GitHub Actions provides:
- **25-30 minute timeouts** (5-6x longer than current limit)
- **No API rate limits** for test execution and Docker builds
- **Real PostgreSQL and Redis** services for integration testing
- **Parallel job execution** for faster feedback

## Workflows

### 1. QA Regression (`qa-regression.yml`)
Runs automatically on push/PR:
- Backend tests with testcontainers
- Docker build verification
- Alembic migration up/down test

### 2. Development Tasks (`dev-tasks.yml`)
Manually triggered for implementation work:
```bash
# Trigger via GitHub UI or API
# - Provides 25-minute timeout
# - Has real PostgreSQL + Redis
# - Can run complex implementation tasks
```

## How This Helps the Team Workflow

| Before | After |
|--------|-------|
| QA subagent runs pytest (3 min) → times out | GitHub Actions runs pytest (2 min) → QA just reviews |
| Developer subagent implements (5 min) → times out | Trigger dev-task workflow (25 min) → Developer monitors |
| Docker build in subagent (slow) | Docker build in CI (fast, cached) |
| Sequential testing | Parallel jobs |

## Next Steps to Enable

1. **Push this repository to GitHub**
2. **Configure repository secrets** (if needed for private deps)
3. **Trigger first workflow run** to verify setup

## Future Enhancement

Once running, we can:
- Add self-hosted runner with OpenClaw for true subagent execution
- Auto-trigger workflows from Architect assignments
- Report results back to main session
