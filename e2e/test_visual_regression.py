"""
QA-011: Visual Regression Tests
Detects unintended UI changes by comparing screenshots to baselines.

Test Plan: QA-011-CONTRACT-VISUAL-TEST-PLAN.md
Requirements: UX-1.1, UX-2.3 (Visual consistency)
"""

import pytest
import requests
from pathlib import Path
from playwright.sync_api import Page, expect
from playwright.sync_api import sync_playwright


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "http://localhost:8000"
BASELINE_DIR = Path(__file__).parent / "visual-baselines"
DIFF_DIR = Path(__file__).parent / "visual-diffs"

# Ensure directories exist
BASELINE_DIR.mkdir(exist_ok=True)
DIFF_DIR.mkdir(exist_ok=True)

# Test user for visual tests
TEST_USER = {
    "email": "qa-visual-test@example.com",
    "password": "VisualTest123!"
}


@pytest.fixture(scope="module")
def playwright_instance():
    """DEF-011-006: Provide playwright instance for all tests."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="module")
def browser(playwright_instance):
    """DEF-011-006: Launch browser instance."""
    browser = playwright_instance.chromium.launch(headless=True)
    yield browser
    browser.close()


@pytest.fixture
def page(browser):
    """DEF-011-006: Create new page for each test."""
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    yield page
    context.close()


def setup_module():
    """
    Launch stack via launch.sh and create test user.
    
    This ensures launch.sh is tested as part of visual regression.
    If stack not running, launch.sh is executed (validating deployment path).
    """
    import subprocess
    import time
    import os
    
    # Check if stack is already running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            # Stack already running, just create user
            _create_test_user()
            return
    except requests.exceptions.ConnectionError:
        pass  # Stack not running, need to launch
    
    # Launch stack using launch.sh (tests the launch script)
    print("\n[!] Stack not running. Launching via launch.sh...")
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    result = subprocess.run(
        ["./launch.sh"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode != 0:
        pytest.fail(
            f"launch.sh failed to start stack:\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )
    
    # Wait for services to be ready
    print("[.] Waiting for services...")
    for attempt in range(30):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("[✓] Stack ready")
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    else:
        pytest.fail("Stack failed to become healthy after 60s")
    
    # Create test user
    _create_test_user()


def _create_test_user():
    """Helper: Create visual test user."""
    try:
        requests.post(
            f"{BASE_URL}/auth/register",
            json=TEST_USER,
            timeout=5
        )
    except requests.exceptions.RequestException:
        pass  # User may already exist


def compare_screenshot(page: Page, name: str, threshold: float = 0.2):
    """
    Capture screenshot and compare to baseline.
    
    Args:
        page: Playwright page object
        name: Baseline name (e.g., "login-desktop")
        threshold: Maximum allowed pixel difference percentage (default 0.2%)
    
    Raises:
        pytest.fail: If visual regression detected
    """
    # Capture full page screenshot
    screenshot = page.screenshot(full_page=True)
    
    # Define paths
    baseline_path = BASELINE_DIR / f"{name}.png"
    current_path = DIFF_DIR / f"{name}-current.png"
    diff_path = DIFF_DIR / f"{name}-diff.png"
    
    # Save current for inspection
    current_path.write_bytes(screenshot)
    
    # Check if baseline exists
    if not baseline_path.exists():
        # First run - create baseline
        baseline_path.write_bytes(screenshot)
        pytest.skip(f"Created baseline: {name}.png (first run)")
    
    # Compare images using PIL
    try:
        from PIL import Image
        import numpy as np
        
        baseline = Image.open(baseline_path)
        current = Image.open(current_path)
        
        # Size check
        if baseline.size != current.size:
            pytest.fail(
                f"Visual regression: Size changed from {baseline.size} to {current.size}\n"
                f"Check {current_path} and {baseline_path}"
            )
        
        # Calculate pixel difference
        baseline_arr = np.array(baseline)
        current_arr = np.array(current)
        
        # Absolute difference
        diff = np.abs(baseline_arr.astype(float) - current_arr.astype(float))
        
        # Calculate percentage of changed pixels
        diff_percentage = np.mean(diff) / 255 * 100
        
        if diff_percentage > threshold:
            # Generate diff visualization
            diff_img = Image.fromarray(np.clip(diff * 2, 0, 255).astype(np.uint8))
            diff_img.save(diff_path)
            
            pytest.fail(
                f"Visual regression detected: {diff_percentage:.2f}% pixel difference\n"
                f"Threshold: {threshold}%\n"
                f"Baseline: {baseline_path}\n"
                f"Current:  {current_path}\n"
                f"Diff:     {diff_path}\n\n"
                f"To update baseline: cp {current_path} {baseline_path}"
            )
        
        # Cleanup on success
        current_path.unlink(missing_ok=True)
        
    except ImportError:
        pytest.skip("PIL/numpy not available for image comparison. Install: pip install Pillow numpy")


# ============================================================================
# TEST CLASS: Login Page Visuals
# Requirement: UX-1.1 (Login page visual design)
# ============================================================================

class TestVisualLoginPage:
    """
    QA-VISUAL-001 through QA-VISUAL-003
    Validates login page visual consistency
    """
    
    def test_qa_visual_001_login_desktop(self, page: Page):
        """
        QA-VISUAL-001: Login page matches desktop baseline
        
        Preconditions:
        - Docker stack running
        - Frontend accessible at localhost:8000
        
        Test Steps:
        1. Navigate to login page
        2. Set viewport to 1280x720 (desktop)
        3. Wait for animations/fonts to settle
        4. Capture screenshot
        
        Expected Result:
        - Screenshot matches baseline (threshold: 0.2% pixel diff)
        
        Priority: P2
        """
        page.goto(f"{BASE_URL}/")
        page.set_viewport_size({"width": 1280, "height": 720})
        
        # Wait for fonts and animations
        page.wait_for_timeout(800)
        
        # Verify key elements before screenshot
        expect(page.locator("h1")).to_contain_text("Dashy")
        expect(page.get_by_placeholder("you@example.com")).to_be_visible()
        
        compare_screenshot(page, "login-desktop")
    
    def test_qa_visual_002_login_mobile(self, page: Page):
        """
        QA-VISUAL-002: Login page matches mobile baseline
        
        Preconditions:
        - Docker stack running
        
        Test Steps:
        1. Navigate to login page
        2. Set viewport to 375x667 (iPhone SE size)
        3. Wait for render
        4. Capture screenshot
        
        Expected Result:
        - Screenshot matches mobile baseline
        - Layout adapts to mobile viewport
        
        Priority: P2
        """
        page.goto(f"{BASE_URL}/")
        page.set_viewport_size({"width": 375, "height": 667})
        
        page.wait_for_timeout(800)
        
        # Verify mobile elements
        expect(page.locator("h1")).to_contain_text("Dashy")
        
        compare_screenshot(page, "login-mobile")
    
    def test_qa_visual_003_login_error_state(self, page: Page):
        """
        QA-VISUAL-003: Login error state matches baseline
        
        Preconditions:
        - Docker stack running
        
        Test Steps:
        1. Navigate to login page
        2. Enter invalid credentials
        3. Submit form
        4. Wait for error message
        5. Capture screenshot
        
        Expected Result:
        - Error message visible with correct styling
        - Screenshot matches baseline
        
        Priority: P2
        """
        page.goto(f"{BASE_URL}/")
        page.set_viewport_size({"width": 1280, "height": 720})
        
        # Trigger error
        page.get_by_placeholder("you@example.com").fill("invalid@example.com")
        page.get_by_placeholder("••••••••").fill("wrongpassword")
        page.get_by_role("button", name="Sign In").click()
        
        # Wait for error to appear
        expect(page.locator("text=Invalid credentials")).to_be_visible()
        page.wait_for_timeout(500)
        
        compare_screenshot(page, "login-error")


# ============================================================================
# TEST CLASS: Dashboard Visuals
# Requirement: UX-2.3 (Dashboard layout stability)
# ============================================================================

class TestVisualDashboard:
    """
    QA-VISUAL-004 through QA-VISUAL-005
    Validates dashboard visual consistency
    """
    
    def login_user(self, page: Page):
        """Helper: Login test user and return to dashboard."""
        page.goto(f"{BASE_URL}/")
        page.get_by_placeholder("you@example.com").fill(TEST_USER["email"])
        page.get_by_placeholder("••••••••").fill(TEST_USER["password"])
        page.get_by_role("button", name="Sign In").click()
        page.wait_for_url(f"{BASE_URL}/dashboard")
        return page
    
    def test_qa_visual_004_dashboard_empty(self, page: Page):
        """
        QA-VISUAL-004: Empty dashboard matches baseline
        
        Preconditions:
        - Docker stack running
        - Test user authenticated
        - User has no modules (or modules cleared)
        
        Test Steps:
        1. Login as test user
        2. Wait for dashboard to load
        3. Capture screenshot
        
        Expected Result:
        - Empty state displayed correctly
        - Screenshot matches baseline
        
        Priority: P2
        """
        page = self.login_user(page)
        page.set_viewport_size({"width": 1280, "height": 900})
        
        # Wait for dashboard to fully render
        page.wait_for_timeout(1000)
        
        # Verify we're on dashboard
        expect(page.locator("text=Dashy")).to_be_visible()
        
        compare_screenshot(page, "dashboard-empty")
    
    def test_qa_visual_005_dashboard_with_portfolio(self, page: Page):
        """
        QA-VISUAL-005: Dashboard with portfolio matches baseline
        
        Preconditions:
        - Docker stack running
        - Test user authenticated
        
        Test Steps:
        1. Login as test user
        2. Add portfolio module via UI
        3. Verify module appears
        4. Capture screenshot
        
        Expected Result:
        - Portfolio module visible with correct styling
        - Screenshot matches baseline
        
        Priority: P2
        
        Note: This test may need baseline updates if module styling changes.
        """
        page = self.login_user(page)
        page.set_viewport_size({"width": 1280, "height": 900})
        
        # Click Add Module
        # Handle either "Add Your First Module" (empty state) or "Add Module" button
        try:
            if page.locator("text=No modules yet").is_visible():
                page.get_by_role("button", name="Add Your First Module").click()
            else:
                page.get_by_role("button", name="Add Module").first.click()
        except:
            # Try generic add button
            page.locator("button:has-text('Add')").first.click()
        
        # Fill modal
        page.wait_for_selector("text=Add Module")
        page.locator("select").select_option("portfolio")
        page.locator("input[type='text']").fill("QA Visual Test Portfolio")
        page.get_by_role("button", name="Add").click()
        
        # Wait for module to appear
        expect(page.locator("text=QA Visual Test Portfolio")).to_be_visible()
        page.wait_for_timeout(800)
        
        compare_screenshot(page, "dashboard-with-portfolio")
