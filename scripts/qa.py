#!/usr/bin/env python3
"""
GStack QA V2 — Executable QA Script

Usage: python qa.py [--url BASE_URL]

Tests dashboard backend API and verifies frontend files.
"""

import sys
import argparse
import requests
import json
from pathlib import Path
from datetime import datetime

class DashboardQA:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.results = []
        self.token = None
        self.user_id = None

    def log(self, status, test, detail=""):
        emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}.get(status, "❓")
        self.results.append({
            "status": status,
            "test": test,
            "detail": detail,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{emoji} [{status}] {test}")
        if detail:
            print(f"   {detail}")

    def test_health(self):
        """Test health endpoint."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.log("PASS", "Health Check", f"Status: {data.get('status')}")
                return True
            else:
                self.log("FAIL", "Health Check", f"HTTP {resp.status_code}")
                return False
        except Exception as e:
            self.log("FAIL", "Health Check", str(e))
            return False

    def test_auth_register(self):
        """Test user registration."""
        try:
            resp = requests.post(
                f"{self.base_url}/auth/register",
                json={
                    "email": f"qatest_{datetime.now().timestamp()}@example.com",
                    "password": "qatest123",
                    "name": "QA Test User"
                },
                timeout=5
            )
            if resp.status_code == 201:
                data = resp.json()
                self.token = data.get("access_token")
                self.log("PASS", "Auth Register", "User created successfully")
                return True
            else:
                self.log("WARN", "Auth Register", f"HTTP {resp.status_code} — may already exist")
                return False
        except Exception as e:
            self.log("FAIL", "Auth Register", str(e))
            return False

    def test_auth_login(self):
        """Test user login."""
        try:
            resp = requests.post(
                f"{self.base_url}/auth/login",
                json={"email": "qatest@example.com", "password": "qatest123"},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                self.log("PASS", "Auth Login", "Login successful, token received")
                return True
            else:
                self.log("FAIL", "Auth Login", f"HTTP {resp.status_code}")
                return False
        except Exception as e:
            self.log("FAIL", "Auth Login", str(e))
            return False

    def test_modules_list(self):
        """Test modules list endpoint."""
        if not self.token:
            self.log("WARN", "Modules List", "No auth token, skipping")
            return False

        try:
            resp = requests.get(
                f"{self.api_url}/modules",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                modules = data.get("modules", [])
                self.log("PASS", "Modules List", f"Retrieved {len(modules)} modules")
                return True
            else:
                self.log("FAIL", "Modules List", f"HTTP {resp.status_code}")
                return False
        except Exception as e:
            self.log("FAIL", "Modules List", str(e))
            return False

    def test_dashboard_endpoint(self):
        """Test dashboard endpoint (may not exist)."""
        if not self.token:
            self.log("WARN", "Dashboard API", "No auth token, skipping")
            return False

        try:
            resp = requests.get(
                f"{self.api_url}/dashboard",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            if resp.status_code == 200:
                self.log("PASS", "Dashboard API", "Endpoint exists")
                return True
            elif resp.status_code == 404:
                self.log("WARN", "Dashboard API", "Endpoint not implemented (404)")
                return False
            else:
                self.log("FAIL", "Dashboard API", f"HTTP {resp.status_code}")
                return False
        except Exception as e:
            self.log("FAIL", "Dashboard API", str(e))
            return False

    def test_frontend_files(self):
        """Verify frontend files exist and have correct structure."""
        frontend_dir = Path(__file__).parent.parent / "frontend"

        # Check dashboard.html
        dashboard_html = frontend_dir / "dashboard.html"
        if not dashboard_html.exists():
            self.log("FAIL", "Frontend Files", "dashboard.html not found")
            return False

        content = dashboard_html.read_text()

        # Check for XSS fixes
        if "escapeHtml(module.name)" in content and "escapeHtml(module.module_type)" in content:
            self.log("PASS", "XSS Fix", "module.name and module.module_type escaped")
        else:
            self.log("FAIL", "XSS Fix", "module.name or module.module_type not escaped")

        # Check for onclick removal
        if 'onclick="logout()"' in content or 'onclick="openAddModuleModal()"' in content:
            self.log("FAIL", "Inline onclick", "Inline onclick handlers still present")
        else:
            self.log("PASS", "Inline onclick", "No inline onclick handlers found")

        # Check for event listeners
        if "addEventListener('click', logout)" in content:
            self.log("PASS", "Event Listeners", "Proper event listeners attached")
        else:
            self.log("WARN", "Event Listeners", "May use different attachment pattern")

        # Check for accessibility
        if "aria-label" in content:
            self.log("PASS", "Accessibility", "aria-label found")
        else:
            self.log("WARN", "Accessibility", "No aria-label found")

        return True

    def run_all_tests(self):
        print("=" * 60)
        print("🧪 GStack QA V2 — Dashboard Testing")
        print(f"   URL: {self.base_url}")
        print(f"   Time: {datetime.now().isoformat()}")
        print("=" * 60)
        print()

        # Backend tests
        self.test_health()
        self.test_auth_login()
        self.test_auth_register()
        self.test_modules_list()
        self.test_dashboard_endpoint()

        print()

        # Frontend tests
        self.test_frontend_files()

        print()

    def generate_report(self):
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        warnings = len([r for r in self.results if r["status"] == "WARN"])

        report = []
        report.append("# QA Report V2")
        report.append(f"**URL:** {self.base_url}")
        report.append(f"**Date:** {datetime.now().isoformat()}")
        report.append("")
        report.append("## Summary")
        report.append(f"- ✅ PASS: {passed}")
        report.append(f"- ❌ FAIL: {failed}")
        report.append(f"- ⚠️ WARN: {warnings}")
        report.append(f"- **Total:** {len(self.results)}")
        report.append("")

        report.append("## Results")
        for result in self.results:
            emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}.get(result["status"], "❓")
            report.append(f"### {emoji} {result['status']}: {result['test']}")
            if result["detail"]:
                report.append(f"{result['detail']}")
            report.append("")

        # Recommendation
        if failed > 0:
            report.append("## Recommendation: 🔴 FIX_THEN_SHIP")
            report.append("Failed tests must be resolved before deployment.")
        elif warnings > 0:
            report.append("## Recommendation: 🟡 FIX_THEN_SHIP")
            report.append("Warnings should be addressed before deployment.")
        else:
            report.append("## Recommendation: 🟢 SHIP")
            report.append("All tests passed. Ready for deployment.")

        return '\n'.join(report)

def main():
    parser = argparse.ArgumentParser(description="GStack QA V2 — Dashboard Testing")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL")
    args = parser.parse_args()

    qa = DashboardQA(args.url)
    qa.run_all_tests()

    report = qa.generate_report()
    print(report)

    # Save report
    output_path = Path(__file__).parent.parent / "docs" / "qa-report-v2-executed.md"
    output_path.write_text(report)
    print(f"\n💾 Report saved to: {output_path}")

if __name__ == '__main__':
    main()
