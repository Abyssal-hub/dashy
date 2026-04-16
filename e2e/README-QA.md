# QA-011: Contract & Visual Regression Tests

This directory contains QA-compliant test suites for validating API contracts and visual regression.

## 📋 Quick Start

```bash
# Run all QA tests
./scripts/run-qa-tests.sh

# Run only contract tests
./scripts/run-qa-tests.sh contract

# Run only visual tests
./scripts/run-qa-tests.sh visual
```

## 📁 Test Structure

```
personal-monitoring-dashboard/
├── backend/tests/
│   └── test_contract.py          # QA-CONTRACT-001 to QA-CONTRACT-011
│   └── snapshots/
│       └── openapi_critical.json # API schema baseline (auto-generated)
├── e2e/
│   └── test_visual_regression.py # QA-VISUAL-001 to QA-VISUAL-005
│   └── visual-baselines/         # Screenshot baselines (committed)
│       ├── login-desktop.png
│       ├── login-mobile.png
│       ├── login-error.png
│       ├── dashboard-empty.png
│       └── dashboard-with-portfolio.png
│   └── visual-diffs/             # Failed comparison outputs (git-ignored)
├── QA-011-CONTRACT-VISUAL-TEST-PLAN.md  # Test plan document
└── scripts/
    └── run-qa-tests.sh           # Test runner script
```

## 🔬 Contract Tests

**Purpose:** Ensure backend API responses match frontend expectations

### Running Manually

```bash
cd backend
source .venv/bin/activate
pytest tests/test_contract.py -v
```

### What They Validate

| Test ID | What It Checks |
|---------|----------------|
| QA-CONTRACT-001 | Login returns valid JWT tokens (format, claims) |
| QA-CONTRACT-002 | Failed login returns proper error structure |
| QA-CONTRACT-003 | Registration returns user with expected fields |
| QA-CONTRACT-004 | Create module returns complete module object |
| QA-CONTRACT-005 | Module list returns array of valid modules |
| QA-CONTRACT-006 | Empty module list returns valid empty array |
| QA-CONTRACT-007 | Layout endpoint returns positions array |
| QA-CONTRACT-008 | Health endpoint returns proper status |
| QA-CONTRACT-009 | **Breaking change detection** - OpenAPI schema stable |
| QA-CONTRACT-010 | DateTime fields are ISO 8601 strings |
| QA-CONTRACT-011 | ID fields are string UUIDs |

### Schema Snapshots

The `snapshots/` directory contains API schema baselines. If QA-CONTRACT-009 fails:

1. **Analyze the diff** - Run tests to see what changed
2. **Determine intent** - Is this a planned API change?
3. **If intentional** - Delete snapshot, re-run to create new baseline, get QA sign-off
4. **If unintentional** - File DEF-XXX against developer

```bash
# View diff
pytest backend/tests/test_contract.py::TestSchemaStability::test_qa_contract_009_openapi_schema_stable -v

# Update baseline (after QA sign-off)
rm backend/tests/snapshots/openapi_critical.json
pytest backend/tests/test_contract.py::TestSchemaStability::test_qa_contract_009_openapi_schema_stable -v
```

## 🎨 Visual Regression Tests

**Purpose:** Detect unintended UI changes

### Prerequisites

```bash
pip install playwright Pillow numpy
playwright install chromium
```

### Running Manually

```bash
# Headless (CI mode)
pytest e2e/test_visual_regression.py -v

# Interactive (for debugging)
pytest e2e/test_visual_regression.py -v --headed
```

### What They Validate

| Test ID | Viewport | What It Captures |
|---------|----------|------------------|
| QA-VISUAL-001 | 1280x720 | Login page (desktop) |
| QA-VISUAL-002 | 375x667 | Login page (mobile) |
| QA-VISUAL-003 | 1280x720 | Login page (error state) |
| QA-VISUAL-004 | 1280x900 | Empty dashboard |
| QA-VISUAL-005 | 1280x900 | Dashboard with portfolio module |

### Baseline Management

**First Run:** Creates baseline images automatically

**Subsequent Runs:** Compare current screenshots to baselines

**On Failure:**

```bash
# Check diff outputs
cd e2e/visual-diffs/
ls -la  # Shows: login-desktop-current.png, login-desktop-diff.png

# Review differences visually
# If intentional design change, update baseline:
cp e2e/visual-diffs/login-desktop-current.png e2e/visual-baselines/login-desktop.png

# If bug, file DEF-XXX
cat >> DEFECTS.md << 'EOF'
## DEF-XXX: Login page styling regression

**Status:** OPEN
**Severity:** Major
**Discovered:** $(date +%Y-%m-%d)
**Reporter:** QA Engineer
**Related To:** QA-VISUAL-001

### Summary
Button color changed from purple to blue. Appears to be unintended.

### Evidence
- Baseline: e2e/visual-baselines/login-desktop.png
- Current:  e2e/visual-diffs/login-desktop-current.png
- Diff:     e2e/visual-diffs/login-desktop-diff.png

### Expected
Button uses brand-gradient purple (#8b5cf6 to #7c3aed)

### Actual
Button appears blue (#3b82f6)
EOF
```

## 📊 Test Results Interpretation

### Contract Test Failures

```
QA-CONTRACT-004 FAIL: Create module response violates contract
  field required (type=value_error.missing)
  config
```

**Meaning:** Backend stopped returning `config` field in create module response. Frontend will crash when trying to access `module.config`.

**Action:** File DEF-XXX - API breaking change

### Visual Regression Failures

```
Visual regression detected: 5.23% pixel difference
Threshold: 0.2%
```

**Meaning:** UI changed significantly. 5.23% of pixels differ from baseline.

**Action:** 
1. Check diff images in `e2e/visual-diffs/`
2. If intentional (design update) → Update baseline with QA sign-off
3. If unintentional (CSS bug) → File DEF-XXX

## 🔄 CI Integration

```yaml
# .github/workflows/qa-contract-visual.yml
name: QA-011 Contract & Visual Tests

on: [push, pull_request]

jobs:
  contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start services
        run: docker-compose up -d
      - name: Run contract tests
        run: |
          cd backend
          source .venv/bin/activate
          pytest tests/test_contract.py -v

  visual:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start services
        run: docker-compose up -d
      - name: Install Playwright
        run: |
          pip install playwright Pillow numpy
          playwright install chromium
      - name: Run visual tests
        run: pytest e2e/test_visual_regression.py -v
      - name: Upload diffs on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: visual-diffs
          path: e2e/visual-diffs/
```

## 📋 QA Sign-Off Checklist

Before marking QA-011 complete:

- [ ] All 11 contract tests passing (P1: 100% required)
- [ ] All 5 visual regression tests passing (or baselines established)
- [ ] Contract snapshots committed to git
- [ ] Visual baselines committed to git
- [ ] No open DEF-XXX from contract/visual issues
- [ ] Test plan QA-011-CONTRACT-VISUAL-TEST-PLAN.md reviewed
- [ ] Defect reporting template understood by team

## 🆘 Troubleshooting

### Contract Tests: "Backend not responding"

```bash
# Start the stack
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

### Visual Tests: "PIL/numpy not available"

```bash
pip install Pillow numpy
```

### Visual Tests: "Playwright not installed"

```bash
pip install playwright
playwright install chromium
```

### Baseline Updates

If you intentionally changed the API or UI:

```bash
# For contract tests (API change)
rm backend/tests/snapshots/openapi_critical.json
pytest backend/tests/test_contract.py::TestSchemaStability -v

# For visual tests (UI change)
pytest e2e/test_visual_regression.py -v  # Creates *-current.png
# Manually copy approved changes to baselines
cp e2e/visual-diffs/login-desktop-current.png e2e/visual-baselines/login-desktop.png
```

## 📚 References

- **Test Plan:** `QA-011-CONTRACT-VISUAL-TEST-PLAN.md`
- **Test Strategy:** `QA-001-TEST-STRATEGY.md`
- **Architecture:** `ARCHITECTURE.md` Section 5.2 (API contracts)
- **Defects:** `DEFECTS.md`

## 👤 QA Contact

QA Engineer responsible for contract/visual test maintenance.

---

**Last Updated:** 2024-04-16  
**Test Plan Version:** 1.0  
**Status:** In Progress
