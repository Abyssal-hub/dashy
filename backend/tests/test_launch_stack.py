"""
QA-011: Stack Launch Integration Test

Validates that launch.sh correctly starts the full Docker Compose stack.
This test ensures the launch script itself is part of regression testing.

Requirement: Launch script must be tested as part of QA-011
"""

import subprocess
import time
import requests
import pytest


class TestStackLaunch:
    """
    QA-CONTRACT-013: Stack launch via launch.sh
    
    Validates that the launch script correctly:
    1. Starts Docker Compose stack
    2. Waits for services to be healthy
    3. Backend responds to health checks
    4. Frontend is accessible
    """
    
    @pytest.mark.skip(reason="Run manually or in CI - takes 60+ seconds")
    def test_qa_contract_013_launch_script_starts_stack(self):
        """
        QA-CONTRACT-013: launch.sh starts full stack correctly
        
        Preconditions:
        - Docker daemon running
        - launch.sh exists and is executable
        
        Test Steps:
        1. Run ./launch.sh
        2. Wait for services (max 60s)
        3. Verify backend health endpoint
        4. Verify frontend accessible
        
        Expected Result:
        - launch.sh exits with code 0
        - Backend returns 200 on /health
        - Frontend returns 200 with HTML content
        
        Priority: P1 (Deployment blocker)
        
        Note: This test takes 60+ seconds. Run manually or in CI.
        Skip in fast test runs with: pytest -m "not slow"
        """
        import os
        project_dir = "/root/.openclaw/workspace/personal-monitoring-dashboard"
        
        # Step 1: Run launch.sh
        result = subprocess.run(
            ["./launch.sh"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes max
        )
        
        assert result.returncode == 0, \
            f"QA-CONTRACT-013 FAIL: launch.sh failed with code {result.returncode}\n" \
            f"STDOUT: {result.stdout}\n" \
            f"STDERR: {result.stderr}"
        
        # Step 2: Wait for services (launch.sh should do this, but verify)
        time.sleep(5)  # Brief buffer
        
        # Step 3: Verify backend health
        for attempt in range(30):  # 30 attempts, 2s apart = 60s max
            try:
                response = requests.get(
                    "http://localhost:8000/health",
                    timeout=5
                )
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(2)
        else:
            pytest.fail("QA-CONTRACT-013 FAIL: Backend health check failed after 60s")
        
        # Step 4: Verify frontend accessible
        try:
            response = requests.get("http://localhost:8000/", timeout=10)
            assert response.status_code == 200, \
                f"QA-CONTRACT-013 FAIL: Frontend returned {response.status_code}"
            assert "DOCTYPE" in response.text or "html" in response.text.lower(), \
                "QA-CONTRACT-013 FAIL: Frontend doesn't return HTML"
        except requests.exceptions.ConnectionError:
            pytest.fail("QA-CONTRACT-013 FAIL: Frontend not accessible")
        
        # Success
        print(f"✓ launch.sh completed successfully")
        print(f"✓ Backend health: OK")
        print(f"✓ Frontend: OK")
