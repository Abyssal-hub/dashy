# E2E Testing with Playwright

End-to-end tests for critical user flows using Playwright.

## Setup

```bash
# Install Playwright dependencies
pip install pytest-playwright
playwright install

# Or add to requirements.txt:
# pytest-playwright>=0.4.0
```

## Running Tests

**Prerequisites:**
```bash
# Start the application
./start.sh

# Wait for services to be ready
```

**Run E2E tests:**

```bash
# Headless (CI mode)
pytest e2e/

# With visible browser (debugging)
pytest e2e/ --headed

# Specific test
pytest e2e/test_critical_flows.py::TestFlow2AddPortfolioModule -v

# With tracing (for debugging failures)
pytest e2e/ --tracing=retain-on-failure
```

## Test Coverage

| Flow | Test Class | Description |
|------|------------|-------------|
| Flow 1 | `TestFlow1FirstTimeUser` | Login page loads correctly |
| Flow 2 | `TestFlow2AddPortfolioModule` | Login → Add module → Verify |
| Flow 6 | `TestFlow6LogoutAndRelogin` | Logout clears session |
| Flow 7 | `TestFlow7ErrorHandling` | Invalid login shows error |

## Architecture

```
e2e/
├── conftest.py              # Shared fixtures (if needed)
├── test_critical_flows.py   # Critical path tests
└── README.md                # This file
```

## Writing New Tests

```python
def test_example(page: Page):
    page.goto("http://localhost:8000/dashboard")
    
    # Use Playwright locators
    page.get_by_role("button", name="Add Module").click()
    
    # Assert with expect
    expect(page.locator("text=Add Module")).to_be_visible()
```

## Debugging Failed Tests

```bash
# Run with headed browser
pytest e2e/ --headed --slowmo=1000

# Generate trace
pytest e2e/ --tracing=on

# View trace
playwright show-trace trace.zip
```

## CI Integration

```yaml
# .github/workflows/e2e.yml snippet
- name: Run E2E tests
  run: |
    ./start.sh
    sleep 10
    pytest e2e/ --headed=false
```
