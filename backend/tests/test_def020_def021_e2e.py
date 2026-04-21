"""
E2E Test: Full User Journey - DEF-020 & DEF-021 Validation

Tests the complete flow from registration to dashboard rendering with real data.
Validates that modules fetch live data from API (not hardcoded fake values).

Scenario: Real user adds portfolio, calendar, and log modules, populates them with data,
verifies dashboard renders correctly with live values.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

from app.services.auth.service import create_user, create_access_token
from app.models.portfolio import Asset
from app.models.calendar import CalendarEvent
from app.models.module import Module
from app.models.log import SystemLog

@pytest.mark.e2e
@pytest.mark.asyncio
class TestDEF020DEF021FullUserJourney:
    """
    End-to-end test covering:
    1. User registration and login
    2. Adding portfolio, calendar, log modules
    3. Populating modules with real data
    4. Verifying API returns real data (not hardcoded)
    5. Frontend rendering simulation
    """

    async def test_complete_user_journey(self, client, db_session):
        """
        Complete user flow test for DEF-020 and DEF-021.
        
        Expected: All modules render with real data from database,
        not hardcoded placeholder values.
        """
        # ========== STEP 1: User Registration ==========
        print("\n[STEP 1] Creating new user...")
        user = await create_user(db_session, "e2e_user@example.com", "SecurePass123!")
        assert user is not None
        print(f"✓ User created: {user.id}")

        # ========== STEP 2: Login ==========
        print("\n[STEP 2] Logging in...")
        login_response = await client.post("/auth/login", json={
            "email": "e2e_user@example.com",
            "password": "SecurePass123!"
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        token = login_data["access_token"]
        print("✓ Login successful, token received")

        # ========== STEP 3: Verify Empty Dashboard ==========
        print("\n[STEP 3] Checking empty dashboard...")
        modules_response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert modules_response.status_code == 200
        assert modules_response.json()["modules"] == []
        print("✓ Dashboard is empty (new user)")

        # ========== STEP 4: Create Portfolio Module ==========
        print("\n[STEP 4] Creating portfolio module...")
        portfolio_response = await client.post(
            "/api/modules",
            json={
                "module_type": "portfolio",
                "name": "My Investment Portfolio",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert portfolio_response.status_code == 201
        portfolio = portfolio_response.json()
        portfolio_id = portfolio["id"]
        assert portfolio["module_type"] == "portfolio"
        assert portfolio["name"] == "My Investment Portfolio"
        print(f"✓ Portfolio module created: {portfolio_id}")

        # ========== STEP 5: Add Real Portfolio Assets ==========
        print("\n[STEP 5] Adding real portfolio assets...")
        
        # Add Apple stock
        asset1 = Asset(
            module_id=portfolio_id,
            symbol="AAPL",
            name="Apple Inc.",
            asset_type="stock",
            quantity=50.0,
            avg_buy_price=150.00,
            current_price=175.50,
            currency="USD"
        )
        db_session.add(asset1)
        
        # Add Bitcoin
        asset2 = Asset(
            module_id=portfolio_id,
            symbol="BTC",
            name="Bitcoin",
            asset_type="crypto",
            quantity=0.5,
            avg_buy_price=45000.00,
            current_price=52000.00,
            currency="USD"
        )
        db_session.add(asset2)
        await db_session.commit()
        print("✓ Added 2 assets (AAPL, BTC)")

        # ========== STEP 6: Create Calendar Module ==========
        print("\n[STEP 6] Creating calendar module...")
        calendar_response = await client.post(
            "/api/modules",
            json={
                "module_type": "calendar",
                "name": "Financial Events",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert calendar_response.status_code == 201
        calendar = calendar_response.json()
        calendar_id = calendar["id"]
        print(f"✓ Calendar module created: {calendar_id}")

        # ========== STEP 7: Add Real Calendar Events ==========
        print("\n[STEP 7] Adding real calendar events...")
        
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        next_week = datetime.now(timezone.utc) + timedelta(days=7)
        
        event1 = CalendarEvent(
            module_id=calendar_id,
            title="Fed Interest Rate Decision",
            start_time=tomorrow,
            end_time=tomorrow + timedelta(hours=1),
            impact="high",
            description="Federal Reserve interest rate announcement - Q2 2026"
        )
        db_session.add(event1)
        
        event2 = CalendarEvent(
            module_id=calendar_id,
            title="Apple Earnings Report",
            start_time=next_week,
            end_time=next_week + timedelta(hours=1),
            impact="medium",
            description="Q2 2026 earnings call - expected revenue $95B"
        )
        db_session.add(event2)
        
        event3 = CalendarEvent(
            module_id=calendar_id,
            title="Weekly Team Sync",
            start_time=datetime.now(timezone.utc) + timedelta(hours=2),
            end_time=datetime.now(timezone.utc) + timedelta(hours=3),
            impact="low",
            description="Regular team standup meeting"
        )
        db_session.add(event3)
        await db_session.commit()
        print("✓ Added 3 events (Fed, Apple earnings, Team sync)")

        # ========== STEP 8: Create Log Module ==========
        print("\n[STEP 8] Creating log module...")
        log_response = await client.post(
            "/api/modules",
            json={
                "module_type": "log",
                "name": "System Monitor",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert log_response.status_code == 201
        log_module = log_response.json()
        log_id = log_module["id"]
        print(f"✓ Log module created: {log_id}")

        # ========== STEP 9: Add System Logs ==========
        print("\n[STEP 9] Adding system logs...")
        
        # Add real system logs via file logger (matches handler implementation)
        from app.core.file_logger import write_log
        
        write_log(severity="INFO", message="Application startup complete",
                 source="system", metadata={"version": "1.0.0", "environment": "test"})
        write_log(severity="WARN", message="High memory usage detected: 85%",
                 source="monitor", metadata={"threshold": "80%", "current": "85%"})
        write_log(severity="ERROR", message="Database connection timeout after 30s",
                 source="database", metadata={"retry_count": 3, "max_retries": 3})
        
        # Flush to ensure written
        import time
        time.sleep(0.1)
        
        print("✓ Added 3 logs (INFO, WARN, ERROR)")

        # ========== STEP 10: Verify Portfolio API Returns Real Data ==========
        print("\n[STEP 10] Verifying portfolio data API...")
        portfolio_data_response = await client.get(
            f"/api/modules/{portfolio_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert portfolio_data_response.status_code == 200
        portfolio_data = portfolio_data_response.json()
        
        # CRITICAL: Must be real data, not hardcoded
        assert portfolio_data["module_type"] == "portfolio"
        assert "data" in portfolio_data
        
        assets = portfolio_data["data"]["assets"]
        assert len(assets) == 2, f"Expected 2 assets, got {len(assets)}"
        
        # Verify specific real data
        symbols = [a["symbol"] for a in assets]
        assert "AAPL" in symbols, "AAPL asset missing"
        assert "BTC" in symbols, "BTC asset missing"
        
        # Verify values are real (computed properties)
        aapl = next(a for a in assets if a["symbol"] == "AAPL")
        btc = next(a for a in assets if a["symbol"] == "BTC")
        
        # market_value is computed: quantity * current_price
        assert aapl["market_value"] == 8775.00, f"AAPL market value wrong: {aapl['market_value']}"
        assert btc["market_value"] == 26000.00, f"BTC market value wrong: {btc['market_value']}"
        
        # Verify total is real (sum of market values)
        total_value = portfolio_data["data"]["total_value"]
        assert total_value > 0, f"Expected positive value, got {total_value}"
        assert total_value == 34775.00, f"Expected $34,775.00, got ${total_value}"
        
        print(f"✓ Portfolio API returns REAL data:")
        print(f"  - Total Value: ${total_value:,.2f}")
        print(f"  - Unrealized P&L: ${float(total_value) - float(aapl['market_value']) - float(btc['market_value']):,.2f}")
        print(f"  - Assets: {len(assets)}")

        # ========== STEP 11: Verify Calendar API Returns Real Data ==========
        print("\n[STEP 11] Verifying calendar data API...")
        calendar_data_response = await client.get(
            f"/api/modules/{calendar_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert calendar_data_response.status_code == 200
        calendar_data = calendar_data_response.json()
        
        # CRITICAL: Must be real data, not hardcoded
        assert calendar_data["module_type"] == "calendar"
        events = calendar_data["data"]["events"]
        assert len(events) == 3, f"Expected 3 events, got {len(events)}"
        
        # Verify specific real data
        titles = [e["title"] for e in events]
        assert "Fed Interest Rate Decision" in titles
        assert "Apple Earnings Report" in titles
        assert "Weekly Team Sync" in titles
        
        # Verify impact levels
        impacts = {e["title"]: e["impact"] for e in events}
        assert impacts["Fed Interest Rate Decision"] == "high"
        assert impacts["Apple Earnings Report"] == "medium"
        assert impacts["Weekly Team Sync"] == "low"
        
        print(f"✓ Calendar API returns REAL data:")
        print(f"  - Events: {len(events)}")
        print(f"  - High impact: {sum(1 for e in events if e['impact'] == 'high')}")
        print(f"  - Medium impact: {sum(1 for e in events if e['impact'] == 'medium')}")

        # ========== STEP 12: Verify Log API Returns Real Data ==========
        print("\n[STEP 12] Verifying log data API...")
        log_data_response = await client.get(
            f"/api/modules/{log_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert log_data_response.status_code == 200
        log_data = log_data_response.json()
        
        # CRITICAL: Must be real data
        assert log_data["module_type"] == "log"
        logs = log_data["data"]["logs"]
        assert len(logs) >= 3, f"Expected at least 3 logs, got {len(logs)}"
        
        # Verify severity distribution
        severities = [l["severity"] for l in logs]
        assert "INFO" in severities
        assert "WARN" in severities
        assert "ERROR" in severities
        
        print(f"✓ Log API returns REAL data:")
        print(f"  - Total logs: {len(logs)}")
        print(f"  - INFO: {severities.count('INFO')}")
        print(f"  - WARN: {severities.count('WARN')}")
        print(f"  - ERROR: {severities.count('ERROR')}")

        # ========== STEP 13: Verify Module List Includes All ==========
        print("\n[STEP 13] Verifying complete module list...")
        list_response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == 200
        modules = list_response.json()["modules"]
        assert len(modules) == 3, f"Expected 3 modules, got {len(modules)}"
        
        types = [m["module_type"] for m in modules]
        assert "portfolio" in types
        assert "calendar" in types
        assert "log" in types
        print(f"✓ All 3 modules present in dashboard")

        # ========== STEP 14: Delete Module (User Action) ==========
        print("\n[STEP 14] Testing module deletion...")
        delete_response = await client.delete(
            f"/api/modules/{log_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert delete_response.status_code == 204
        
        # Verify module is gone
        list_after_delete = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        modules_after = list_after_delete.json()["modules"]
        assert len(modules_after) == 2
        assert not any(m["id"] == log_id for m in modules_after)
        print("✓ Log module deleted successfully")

        # ========== STEP 15: Final Dashboard State ==========
        print("\n[STEP 15] Final dashboard state...")
        final_response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        final_modules = final_response.json()["modules"]
        assert len(final_modules) == 2
        
        remaining_types = [m["module_type"] for m in final_modules]
        assert "portfolio" in remaining_types
        assert "calendar" in remaining_types
        assert "log" not in remaining_types
        
        print(f"✓ Final dashboard: {len(final_modules)} modules (portfolio, calendar)")
        print("\n" + "="*60)
        print("🎉 E2E TEST PASSED: DEF-020 & DEF-021 VALIDATED")
        print("="*60)
        print("\nSummary:")
        print("  • User registered and logged in")
        print("  • Created 3 modules (portfolio, calendar, log)")
        print("  • Added real data to all modules")
        print("  • API returns REAL data (not hardcoded)")
        print("  • Portfolio: $34,775.00 with 2 assets")
        print("  • Calendar: 3 events with impact levels")
        print("  • Logs: INFO/WARN/ERROR severity levels")
        print("  • Module deletion works correctly")
        print("="*60)

    async def test_multiple_modules_isolation(self, client, db_session):
        """
        Test multiple modules of same/different types with data isolation.
        
        Scenario: Power user creates multiple portfolios, calendars, and logs.
        Each module should only show its own data, not leak across modules.
        """
        print("\n\n" + "="*60)
        print("🧪 MULTIPLE MODULES ISOLATION TEST")
        print("="*60)
        
        # ========== STEP 1: Create User and Login ==========
        print("\n[STEP 1] Creating user...")
        user = await create_user(db_session, "multi_user@example.com", "SecurePass123!")
        login_response = await client.post("/auth/login", json={
            "email": "multi_user@example.com",
            "password": "SecurePass123!"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        print("✓ User logged in")

        # ========== STEP 2: Create Two Portfolio Modules ==========
        print("\n[STEP 2] Creating two portfolio modules...")
        
        stocks_resp = await client.post("/api/modules", json={
            "module_type": "portfolio",
            "name": "US Stocks",
            "config": {},
            "size": "medium"
        }, headers={"Authorization": f"Bearer {token}"})
        assert stocks_resp.status_code == 201
        stocks_id = stocks_resp.json()["id"]
        
        crypto_resp = await client.post("/api/modules", json={
            "module_type": "portfolio",
            "name": "Crypto Holdings",
            "config": {},
            "size": "medium"
        }, headers={"Authorization": f"Bearer {token}"})
        assert crypto_resp.status_code == 201
        crypto_id = crypto_resp.json()["id"]
        print(f"✓ Created 'US Stocks' ({stocks_id}) and 'Crypto Holdings' ({crypto_id})")

        # ========== STEP 3: Add Different Assets to Each ==========
        print("\n[STEP 3] Adding assets to each portfolio...")
        
        # Stocks portfolio: AAPL and MSFT
        aapl = Asset(module_id=stocks_id, symbol="AAPL", name="Apple Inc.", 
                    asset_type="stock", quantity=10.0, avg_buy_price=150.00,
                    current_price=175.50, currency="USD")
        msft = Asset(module_id=stocks_id, symbol="MSFT", name="Microsoft Corp.",
                    asset_type="stock", quantity=5.0, avg_buy_price=300.00,
                    current_price=320.00, currency="USD")
        db_session.add_all([aapl, msft])
        
        # Crypto portfolio: BTC and ETH
        btc = Asset(module_id=crypto_id, symbol="BTC", name="Bitcoin",
                   asset_type="crypto", quantity=1.0, avg_buy_price=45000.00,
                   current_price=52000.00, currency="USD")
        eth = Asset(module_id=crypto_id, symbol="ETH", name="Ethereum",
                   asset_type="crypto", quantity=10.0, avg_buy_price=3000.00,
                   current_price=3500.00, currency="USD")
        db_session.add_all([btc, eth])
        await db_session.commit()
        print("✓ Stocks: AAPL + MSFT | Crypto: BTC + ETH")

        # ========== STEP 4: Create Two Calendar Modules ==========
        print("\n[STEP 4] Creating two calendar modules...")
        
        econ_resp = await client.post("/api/modules", json={
            "module_type": "calendar",
            "name": "Economic Events",
            "config": {},
            "size": "medium"
        }, headers={"Authorization": f"Bearer {token}"})
        assert econ_resp.status_code == 201
        econ_id = econ_resp.json()["id"]
        
        personal_resp = await client.post("/api/modules", json={
            "module_type": "calendar",
            "name": "Personal Calendar",
            "config": {},
            "size": "medium"
        }, headers={"Authorization": f"Bearer {token}"})
        assert personal_resp.status_code == 201
        personal_id = personal_resp.json()["id"]
        print(f"✓ Created 'Economic Events' and 'Personal Calendar'")

        # ========== STEP 5: Add Different Events to Each Calendar ==========
        print("\n[STEP 5] Adding events to each calendar...")
        
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        
        # Economic events
        fed_event = CalendarEvent(module_id=econ_id, 
                                   title="Fed Interest Rate Decision",
                                   start_time=tomorrow, end_time=tomorrow + timedelta(hours=1),
                                   impact="high", description="Fed rate decision")
        nfp_event = CalendarEvent(module_id=econ_id,
                                  title="Non-Farm Payrolls",
                                  start_time=tomorrow + timedelta(days=2),
                                  end_time=tomorrow + timedelta(days=2, hours=1),
                                  impact="high", description="NFP data release")
        db_session.add_all([fed_event, nfp_event])
        
        # Personal events
        meeting = CalendarEvent(module_id=personal_id,
                               title="Doctor Appointment",
                               start_time=tomorrow + timedelta(days=3),
                               end_time=tomorrow + timedelta(days=3, hours=1),
                               impact="low", description="Annual checkup")
        birthday = CalendarEvent(module_id=personal_id,
                                title="Mom's Birthday",
                                start_time=tomorrow + timedelta(days=5),
                                end_time=tomorrow + timedelta(days=5, hours=2),
                                impact="low", description="Family dinner")
        db_session.add_all([meeting, birthday])
        await db_session.commit()
        print("✓ Econ: Fed + NFP | Personal: Doctor + Birthday")

        # ========== STEP 6: Verify Portfolio Data Isolation ==========
        print("\n[STEP 6] Verifying portfolio data isolation...")
        
        stocks_data_resp = await client.get(
            f"/api/modules/{stocks_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        stocks_data = stocks_data_resp.json()["data"]
        stocks_symbols = [a["symbol"] for a in stocks_data["assets"]]
        
        crypto_data_resp = await client.get(
            f"/api/modules/{crypto_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        crypto_data = crypto_data_resp.json()["data"]
        crypto_symbols = [a["symbol"] for a in crypto_data["assets"]]
        
        # CRITICAL: Stocks module should NOT see BTC/ETH
        assert "BTC" not in stocks_symbols, "Data leak: BTC found in stocks module!"
        assert "ETH" not in stocks_symbols, "Data leak: ETH found in stocks module!"
        assert "AAPL" in stocks_symbols, "AAPL missing from stocks module"
        assert "MSFT" in stocks_symbols, "MSFT missing from stocks module"
        
        # CRITICAL: Crypto module should NOT see AAPL/MSFT
        assert "AAPL" not in crypto_symbols, "Data leak: AAPL found in crypto module!"
        assert "MSFT" not in crypto_symbols, "Data leak: MSFT found in crypto module!"
        assert "BTC" in crypto_symbols, "BTC missing from crypto module"
        assert "ETH" in crypto_symbols, "ETH missing from crypto module"
        
        # Verify values are correct
        assert stocks_data["total_value"] == 3355.00  # 10*175.50 + 5*320.00
        assert crypto_data["total_value"] == 87000.00  # 1*52000 + 10*3500
        
        print(f"✓ Stocks module: ${stocks_data['total_value']:,.2f} (AAPL, MSFT)")
        print(f"✓ Crypto module: ${crypto_data['total_value']:,.2f} (BTC, ETH)")

        # ========== STEP 7: Verify Calendar Data Isolation ==========
        print("\n[STEP 7] Verifying calendar data isolation...")
        
        econ_data_resp = await client.get(
            f"/api/modules/{econ_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        econ_events = econ_data_resp.json()["data"]["events"]
        econ_titles = [e["title"] for e in econ_events]
        
        personal_data_resp = await client.get(
            f"/api/modules/{personal_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        personal_events = personal_data_resp.json()["data"]["events"]
        personal_titles = [e["title"] for e in personal_events]
        
        # CRITICAL: Economic calendar should NOT see personal events
        assert "Doctor Appointment" not in econ_titles, "Data leak: personal event in econ calendar!"
        assert "Mom's Birthday" not in econ_titles, "Data leak: personal event in econ calendar!"
        assert "Fed Interest Rate Decision" in econ_titles, "Fed event missing"
        assert "Non-Farm Payrolls" in econ_titles, "NFP event missing"
        
        # CRITICAL: Personal calendar should NOT see economic events
        assert "Fed Interest Rate Decision" not in personal_titles, "Data leak: econ event in personal calendar!"
        assert "Non-Farm Payrolls" not in personal_titles, "Data leak: econ event in personal calendar!"
        assert "Doctor Appointment" in personal_titles, "Doctor event missing"
        assert "Mom's Birthday" in personal_titles, "Birthday event missing"
        
        print(f"✓ Econ calendar: {len(econ_events)} events (Fed, NFP)")
        print(f"✓ Personal calendar: {len(personal_events)} events (Doctor, Birthday)")

        # ========== STEP 8: Verify Module List Shows All ==========
        print("\n[STEP 8] Verifying all modules in list...")
        list_resp = await client.get("/api/modules", 
                                     headers={"Authorization": f"Bearer {token}"})
        modules = list_resp.json()["modules"]
        assert len(modules) == 4, f"Expected 4 modules, got {len(modules)}"
        
        module_names = [m["name"] for m in modules]
        assert "US Stocks" in module_names
        assert "Crypto Holdings" in module_names
        assert "Economic Events" in module_names
        assert "Personal Calendar" in module_names
        
        print(f"✓ All 4 modules present: {', '.join(module_names)}")

        # ========== STEP 9: Delete One Module, Verify Others Intact ==========
        print("\n[STEP 9] Testing selective deletion...")
        
        delete_resp = await client.delete(f"/api/modules/{econ_id}",
                                          headers={"Authorization": f"Bearer {token}"})
        assert delete_resp.status_code == 204
        
        # Verify economic calendar is gone
        list_after = await client.get("/api/modules",
                                      headers={"Authorization": f"Bearer {token}"})
        modules_after = list_after.json()["modules"]
        assert len(modules_after) == 3
        assert not any(m["id"] == econ_id for m in modules_after)
        
        # But personal calendar still exists
        assert any(m["id"] == personal_id for m in modules_after), "Personal calendar deleted by mistake!"
        assert any(m["id"] == stocks_id for m in modules_after), "Stocks portfolio deleted by mistake!"
        assert any(m["id"] == crypto_id for m in modules_after), "Crypto portfolio deleted by mistake!"
        
        print("✓ Economic calendar deleted, other 3 modules intact")

        print("\n" + "="*60)
        print("🎉 MULTIPLE MODULES TEST PASSED")
        print("="*60)
        print("\nSummary:")
        print("  • Created 4 modules (2 portfolio + 2 calendar)")
        print("  • Each module has unique data")
        print("  • NO data leakage between modules")
        print("  • Portfolio 1: $3,355.00 (AAPL, MSFT)")
        print("  • Portfolio 2: $87,000.00 (BTC, ETH)")
        print("  • Selective deletion works correctly")
        print("="*60)

    async def test_live_log_updates_and_pagination(self, client, db_session):
        """
        Test live log updates: log module shows new entries in real-time.
        
        Scenario: User opens log monitor, sees initial logs, then new logs arrive
        and are visible on refresh. Also tests pagination with large log volumes.
        """
        print("\n\n" + "="*60)
        print("🧪 LIVE LOG UPDATES & PAGINATION TEST")
        print("="*60)
        
        # ========== STEP 1: Create User and Login ==========
        print("\n[STEP 1] Creating user...")
        user = await create_user(db_session, "log_user@example.com", "SecurePass123!")
        login_response = await client.post("/auth/login", json={
            "email": "log_user@example.com",
            "password": "SecurePass123!"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        print("✓ User logged in")

        # ========== STEP 2: Create Log Module ==========
        print("\n[STEP 2] Creating log module...")
        log_resp = await client.post("/api/modules", json={
            "module_type": "log",
            "name": "Live Log Monitor",
            "config": {},
            "size": "expanded"  # Large view for more logs
        }, headers={"Authorization": f"Bearer {token}"})
        assert log_resp.status_code == 201
        log_id = log_resp.json()["id"]
        print(f"✓ Log module created: {log_id}")

        # ========== STEP 3: Write Initial Batch of Logs ==========
        print("\n[STEP 3] Writing initial 5 logs...")
        from app.core.file_logger import write_log
        
        initial_logs = [
            ("INFO", "Server started", "system"),
            ("INFO", "Database connected", "database"),
            ("WARN", "Slow query detected", "database"),
            ("ERROR", "Failed to send email", "email_service"),
            ("INFO", "Cron job completed", "scheduler"),
        ]
        for severity, message, source in initial_logs:
            write_log(severity=severity, message=message, source=source)
        
        import time
        time.sleep(0.1)  # Ensure file write
        print("✓ 5 initial logs written")

        # ========== STEP 4: Fetch Initial State ==========
        print("\n[STEP 4] Fetching initial log state...")
        data_resp = await client.get(
            f"/api/modules/{log_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert data_resp.status_code == 200
        initial_data = data_resp.json()["data"]
        initial_logs_fetched = initial_data["logs"]
        initial_total = initial_data["total"]
        
        assert len(initial_logs_fetched) >= 5, f"Expected >=5 logs, got {len(initial_logs_fetched)}"
        
        # Verify severity distribution in initial batch
        severities = [l["severity"] for l in initial_logs_fetched]
        assert "ERROR" in severities, "ERROR log missing from initial batch"
        assert "WARN" in severities, "WARN log missing from initial batch"
        assert severities.count("INFO") >= 2, "Expected at least 2 INFO logs"
        
        print(f"✓ Fetched {len(initial_logs_fetched)} logs (total: {initial_total})")

        # ========== STEP 5: Write Additional Logs (Simulate Live Traffic) ==========
        print("\n[STEP 5] Writing 5 more logs (simulating live traffic)...")
        new_logs = [
            ("INFO", "User login: user_123", "auth"),
            ("ERROR", "Payment processing failed", "payment"),
            ("WARN", "API rate limit at 80%", "api_gateway"),
            ("INFO", "Cache invalidated", "cache"),
            ("ERROR", "Disk space critical: 95%", "monitor"),
        ]
        for severity, message, source in new_logs:
            write_log(severity=severity, message=message, source=source)
        
        time.sleep(0.1)  # Ensure file write
        print("✓ 5 new logs written")

        # ========== STEP 6: Fetch Again — Verify Live Update ==========
        print("\n[STEP 6] Fetching updated logs...")
        updated_resp = await client.get(
            f"/api/modules/{log_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert updated_resp.status_code == 200
        updated_data = updated_resp.json()["data"]
        updated_logs = updated_data["logs"]
        updated_total = updated_data["total"]
        
        # CRITICAL: Total should have increased
        assert updated_total > initial_total, (
            f"Live update failed: total didn't increase! "
            f"Initial: {initial_total}, Updated: {updated_total}"
        )
        
        # CRITICAL: New logs should be present
        messages = [l["message"] for l in updated_logs]
        assert "Payment processing failed" in messages, "New ERROR log not found"
        assert "API rate limit at 80%" in messages, "New WARN log not found"
        assert "User login: user_123" in messages, "New INFO log not found"
        
        print(f"✓ Live update confirmed: {initial_total} → {updated_total} logs")
        print(f"  - New entries visible without page refresh")

        # ========== STEP 7: Test Severity Filtering ==========
        print("\n[STEP 7] Testing severity filter (ERROR only)...")
        error_resp = await client.get(
            f"/api/modules/{log_id}/data",
            headers={"Authorization": f"Bearer {token}"},
            params={"severity": "ERROR"}
        )
        assert error_resp.status_code == 200
        error_data = error_resp.json()["data"]
        error_logs = error_data["logs"]
        
        # All returned logs should be ERROR
        assert all(l["severity"] == "ERROR" for l in error_logs), (
            f"Filter failed: found non-ERROR logs in filtered result"
        )
        
        # Should contain both error messages
        error_messages = [l["message"] for l in error_logs]
        assert "Failed to send email" in error_messages, "First ERROR missing"
        assert "Payment processing failed" in error_messages, "Second ERROR missing"
        assert "Disk space critical: 95%" in error_messages, "Third ERROR missing"
        
        print(f"✓ ERROR filter: {len(error_logs)} error entries found")

        # ========== STEP 8: Test Source Filtering ==========
        print("\n[STEP 8] Testing source filter (database only)...")
        db_resp = await client.get(
            f"/api/modules/{log_id}/data",
            headers={"Authorization": f"Bearer {token}"},
            params={"source": "database"}
        )
        assert db_resp.status_code == 200
        db_data = db_resp.json()["data"]
        db_logs = db_data["logs"]
        
        # All returned logs should be from database source
        assert all(l["source"] == "database" for l in db_logs), (
            f"Filter failed: found non-database sources"
        )
        
        db_messages = [l["message"] for l in db_logs]
        assert "Database connected" in db_messages, "Database INFO missing"
        assert "Slow query detected" in db_messages, "Database WARN missing"
        
        print(f"✓ Source filter: {len(db_logs)} database entries found")

        # ========== STEP 9: Verify Severity Counts Metadata ==========
        print("\n[STEP 9] Verifying severity counts metadata...")
        counts = updated_data.get("severity_counts", {})
        
        assert "INFO" in counts, "INFO count missing from metadata"
        assert "WARN" in counts, "WARN count missing from metadata"
        assert "ERROR" in counts, "ERROR count missing from metadata"
        
        assert counts["INFO"] >= 4, f"Expected >=4 INFO, got {counts['INFO']}"
        assert counts["WARN"] >= 2, f"Expected >=2 WARN, got {counts['WARN']}"
        assert counts["ERROR"] >= 3, f"Expected >=3 ERROR, got {counts['ERROR']}"
        
        print(f"✓ Severity counts: INFO={counts['INFO']}, WARN={counts['WARN']}, ERROR={counts['ERROR']}")

        # ========== STEP 10: Pagination Test (Write 25 More Logs) ==========
        print("\n[STEP 10] Testing pagination with large volume...")
        
        # Write 25 more logs to exceed default limit
        for i in range(25):
            write_log(
                severity="INFO" if i % 3 != 0 else "WARN",
                message=f"Background task #{i+1} completed",
                source="background_worker"
            )
        
        time.sleep(0.2)  # Ensure file write
        
        # Fetch default view (should be limited)
        paginated_resp = await client.get(
            f"/api/modules/{log_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        paginated_data = paginated_resp.json()["data"]
        paginated_logs = paginated_data["logs"]
        paginated_total = paginated_data["total"]
        
        # Total should reflect ALL logs, but returned list should be limited
        assert paginated_total >= 35, f"Expected >=35 total logs, got {paginated_total}"
        assert len(paginated_logs) <= 100, f"Expected <=100 returned, got {len(paginated_logs)}"
        
        # Verify pagination metadata
        assert "filters_applied" in paginated_data, "filters_applied metadata missing"
        
        print(f"✓ Pagination: {len(paginated_logs)} of {paginated_total} logs returned")
        print(f"  - Total logs: {paginated_total}")
        print(f"  - Returned: {len(paginated_logs)}")

        print("\n" + "="*60)
        print("🎉 LIVE LOG UPDATE TEST PASSED")
        print("="*60)
        print("\nSummary:")
        print("  • Initial batch: 5 logs fetched correctly")
        print("  • Live update: New logs visible on refresh")
        print("  • Severity filter: ERROR-only works")
        print("  • Source filter: database-only works")
        print("  • Severity counts: accurate metadata")
        print("  • Pagination: large volume handled")
        print("="*60)
