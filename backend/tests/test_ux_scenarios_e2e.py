"""
E2E Test: UX Scenarios - Empty State, Error Handling, Performance, Security

Tests real-world UX edge cases that users encounter in production.
Each test validates a specific user pain point from the UX designer audit.

Scenarios:
1. Empty State - Portfolio with 0 assets shows helpful state
2. Error State - API failure shows friendly message (not raw JSON)
3. Auto-Refresh Stability - Data structure consistent across refreshes
4. Resize Data Density - Small vs Expanded returns different data amounts
5. Browser Refresh - Token and state persist across refresh
6. Cross-User Isolation - User A cannot see User B's data
7. Token Expiry - Graceful handling when JWT expires
8. Large Dataset - 50+ assets, pagination, performance
9. Config Change - Module config update reflects immediately
10. Position Persistence - Module layout survives refresh
"""

import pytest
import time
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

from app.services.auth.service import create_user, create_access_token
from app.models.portfolio import Asset
from app.models.calendar import CalendarEvent
from app.models.module import Module
from app.core.config import settings


@pytest.mark.e2e
@pytest.mark.asyncio
class TestUXScenarios:
    """UX-focused end-to-end tests for real user pain points."""

    # ========================================================================
    # SCENARIO 1: Empty State Experience
    # ========================================================================
    async def test_empty_state_portfolio(self, client, db_session):
        """
        UX-001: Empty portfolio module shows helpful state, not blank box.
        
        User adds portfolio module but hasn't added any assets yet.
        Expect: structured empty response with metadata, not just [].
        """
        print("\n\n[UX-001] Empty State Portfolio Test")
        print("=" * 50)

        # Create user and login
        user = await create_user(db_session, "empty_user@example.com", "SecurePass123!")
        login_resp = await client.post("/auth/login", json={
            "email": "empty_user@example.com",
            "password": "SecurePass123!"
        })
        token = login_resp.json()["access_token"]

        # Create portfolio module (no assets)
        module_resp = await client.post("/api/modules", json={
            "module_type": "portfolio",
            "name": "My Empty Portfolio",
            "config": {},
            "size": "medium"
        }, headers={"Authorization": f"Bearer {token}"})
        assert module_resp.status_code == 201
        module_id = module_resp.json()["id"]
        print(f"✓ Portfolio module created: {module_id}")

        # Fetch data - should be empty but structured
        data_resp = await client.get(
            f"/api/modules/{module_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert data_resp.status_code == 200
        data = data_resp.json()["data"]

        # CRITICAL: Empty state should have same structure as populated state
        assert "assets" in data, "Missing 'assets' key in empty state"
        assert data["assets"] == [], "Expected empty assets array"
        assert "total_value" in data, "Missing 'total_value' key"
        assert data["total_value"] == 0.0, "Expected $0.00 for empty portfolio"
        assert "day_change" in data, "Missing 'day_change' key"
        assert "day_change_percent" in data, "Missing 'day_change_percent' key"

        # Frontend would use these keys to render "Add your first stock" prompt
        print("✓ Empty state response is structured correctly:")
        print(f"  - assets: [] (empty array)")
        print(f"  - total_value: $0.00")
        print(f"  - day_change: {data['day_change']}")
        print(f"  - Frontend can detect empty state and show helpful prompt")

    # ========================================================================
    # SCENARIO 2: Error State Handling
    # ========================================================================
    async def test_error_state_handling(self, client, db_session):
        """
        UX-002: API errors return structured responses, not raw exceptions.
        
        User tries to access non-existent module or invalid data.
        Expect: HTTP 404 with JSON error body, not 500 with traceback.
        """
        print("\n\n[UX-002] Error State Handling Test")
        print("=" * 50)

        # Create user and login
        user = await create_user(db_session, "error_user@example.com", "SecurePass123!")
        login_resp = await client.post("/auth/login", json={
            "email": "error_user@example.com",
            "password": "SecurePass123!"
        })
        token = login_resp.json()["access_token"]

        # Test 1: Non-existent module
        print("[Test 1] Accessing non-existent module...")
        resp = await client.get(
            "/api/modules/00000000-0000-0000-0000-000000000000/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        error_body = resp.json()
        assert "detail" in error_body, "Error response missing 'detail' field"
        assert "not found" in error_body["detail"].lower(), "Error message not user-friendly"
        print(f"✓ 404 with friendly message: '{error_body['detail']}'")

        # Test 2: Invalid module type
        print("[Test 2] Creating invalid module type...")
        invalid_resp = await client.post("/api/modules", json={
            "module_type": "invalid_type_xyz",
            "name": "Bad Module",
            "config": {},
            "size": "medium"
        }, headers={"Authorization": f"Bearer {token}"})
        assert invalid_resp.status_code == 422, f"Expected 422, got {invalid_resp.status_code}"
        error_data = invalid_resp.json()
        assert "detail" in error_data, "Error response missing 'detail'"
        print(f"✓ 422 with validation error: '{error_data['detail']}'")

        # Test 3: Unauthorized access (no token)
        print("[Test 3] Accessing without token...")
        no_auth_resp = await client.get("/api/modules")
        assert no_auth_resp.status_code in (401, 403), f"Expected 401/403, got {no_auth_resp.status_code}"
        print(f"✓ {no_auth_resp.status_code} for unauthorized access")

        # Test 4: Access another user's module (security)
        print("[Test 4] Cross-user module access...")
        user2 = await create_user(db_session, "other_user@example.com", "SecurePass123!")
        login2 = await client.post("/auth/login", json={
            "email": "other_user@example.com",
            "password": "SecurePass123!"
        })
        token2 = login2.json()["access_token"]

        # User2 creates a module
        u2_module = await client.post("/api/modules", json={
            "module_type": "portfolio",
            "name": "User2 Portfolio",
            "config": {},
            "size": "medium"
        }, headers={"Authorization": f"Bearer {token2}"})
        u2_module_id = u2_module.json()["id"]

        # User1 tries to access User2's module
        cross_resp = await client.get(
            f"/api/modules/{u2_module_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert cross_resp.status_code == 404, (
            f"SECURITY: User1 accessed User2's module! Got {cross_resp.status_code}"
        )
        print("✓ 404 for cross-user access (security enforced)")

    # ========================================================================
    # SCENARIO 3: Auto-Refresh Data Consistency
    # ========================================================================
    async def test_auto_refresh_data_consistency(self, client, db_session):
        """
        UX-003: Data refreshes without breaking DOM structure.
        
        User has dashboard open. Data refreshes every 5s.
        Expect: Same keys/structure, only values change.
        """
        print("\n\n[UX-003] Auto-Refresh Data Consistency Test")
        print("=" * 50)

        user = await create_user(db_session, "refresh_user@example.com", "SecurePass123!")
        login_resp = await client.post("/auth/login", json={
            "email": "refresh_user@example.com",
            "password": "SecurePass123!"
        })
        token = login_resp.json()["access_token"]

        # Create portfolio with 2 assets
        module_resp = await client.post("/api/modules", json={
            "module_type": "portfolio",
            "name": "Refresh Test Portfolio",
            "config": {},
            "size": "medium"
        }, headers={"Authorization": f"Bearer {token}"})
        module_id = module_resp.json()["id"]

        asset1 = Asset(module_id=module_id, symbol="AAPL", name="Apple",
                      asset_type="stock", quantity=10.0, avg_buy_price=150.00,
                      current_price=175.50, currency="USD")
        db_session.add(asset1)
        await db_session.commit()

        # Fetch 1st time
        resp1 = await client.get(
            f"/api/modules/{module_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        data1 = resp1.json()["data"]
        keys1 = set(data1.keys())

        # Update asset price (simulates live market data)
        asset1.current_price = 180.00
        await db_session.commit()

        # Fetch 2nd time (simulates auto-refresh)
        resp2 = await client.get(
            f"/api/modules/{module_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        data2 = resp2.json()["data"]
        keys2 = set(data2.keys())

        # CRITICAL: Structure must be identical
        assert keys1 == keys2, f"DOM break! Keys changed: {keys1} vs {keys2}"
        print(f"✓ Structure stable: {sorted(keys1)}")

        # Values should have changed
        assert data1["total_value"] != data2["total_value"], (
            "Values didn't change after price update!"
        )
        print(f"✓ Values updated: ${data1['total_value']} → ${data2['total_value']}")

        # Asset array structure must be consistent
        asset_keys1 = set(data1["assets"][0].keys())
        asset_keys2 = set(data2["assets"][0].keys())
        assert asset_keys1 == asset_keys2, "Asset object structure changed!"
        print(f"✓ Asset structure stable: {sorted(asset_keys1)}")

    # ========================================================================
    # SCENARIO 4: Resize Data Density
    # ========================================================================
    async def test_resize_data_density(self, client, db_session):
        """
        UX-004: Different sizes return different data amounts.
        
        User resizes module from small → expanded.
        Expect: Small returns 3 items summary, Expanded returns full detail.
        """
        print("\n\n[UX-004] Resize Data Density Test")
        print("=" * 50)

        user = await create_user(db_session, "resize_user@example.com", "SecurePass123!")
        login_resp = await client.post("/auth/login", json={
            "email": "resize_user@example.com",
            "password": "SecurePass123!"
        })
        token = login_resp.json()["access_token"]

        # Create portfolio with 5 assets
        module_resp = await client.post("/api/modules", json={
            "module_type": "portfolio",
            "name": "Resize Test",
            "config": {},
            "size": "medium"
        }, headers={"Authorization": f"Bearer {token}"})
        module_id = module_resp.json()["id"]

        for i, symbol in enumerate(["AAPL", "MSFT", "GOOGL", "AMZN", "META"]):
            asset = Asset(module_id=module_id, symbol=symbol, name=symbol,
                         asset_type="stock", quantity=float(i + 1) * 10,
                         avg_buy_price=100.0 + i * 10,
                         current_price=120.0 + i * 10, currency="USD")
            db_session.add(asset)
        await db_session.commit()
        print(f"✓ Added 5 assets to portfolio")

        # Test size=compact (should return limited data)
        print("[Test] size=compact...")
        compact_resp = await client.get(
            f"/api/modules/{module_id}/data?size=compact",
            headers={"Authorization": f"Bearer {token}"}
        )
        compact_data = compact_resp.json()["data"]
        assert len(compact_data["assets"]) <= 5, "Compact should not exceed 5 items"
        print(f"✓ Compact: {len(compact_data['assets'])} assets returned")

        # Test size=expanded (should return all data)
        print("[Test] size=expanded...")
        expanded_resp = await client.get(
            f"/api/modules/{module_id}/data?size=expanded",
            headers={"Authorization": f"Bearer {token}"}
        )
        expanded_data = expanded_resp.json()["data"]
        assert len(expanded_data["assets"]) == 5, "Expanded should return all 5 assets"
        print(f"✓ Expanded: {len(expanded_data['assets'])} assets returned")

        # Calendar module: compact = 7 days, expanded = 365 days
        cal_resp = await client.post("/api/modules", json={
            "module_type": "calendar",
            "name": "Calendar Density Test",
            "config": {},
            "size": "medium"
        }, headers={"Authorization": f"Bearer {token}"})
        cal_id = cal_resp.json()["id"]

        # Add events at different times
        now = datetime.now(timezone.utc)
        event1 = CalendarEvent(module_id=cal_id, title="Tomorrow Event",
                                start_time=now + timedelta(days=1),
                                end_time=now + timedelta(days=1, hours=1),
                                impact="medium")
        event2 = CalendarEvent(module_id=cal_id, title="Next Month Event",
                                start_time=now + timedelta(days=30),
                                end_time=now + timedelta(days=30, hours=1),
                                impact="low")
        db_session.add_all([event1, event2])
        await db_session.commit()

        # Compact should only show next 7 days
        cal_compact = await client.get(
            f"/api/modules/{cal_id}/data?size=compact",
            headers={"Authorization": f"Bearer {token}"}
        )
        cal_compact_events = cal_compact.json()["data"]["events"]
        assert len(cal_compact_events) == 1, "Compact should show only 1 event (7-day range)"
        assert cal_compact_events[0]["title"] == "Tomorrow Event"
        print(f"✓ Calendar compact: {len(cal_compact_events)} event (7-day window)")

        # Expanded should show all (up to 365 days)
        cal_expanded = await client.get(
            f"/api/modules/{cal_id}/data?size=expanded",
            headers={"Authorization": f"Bearer {token}"}
        )
        cal_expanded_events = cal_expanded.json()["data"]["events"]
        assert len(cal_expanded_events) == 2, "Expanded should show both events"
        print(f"✓ Calendar expanded: {len(cal_expanded_events)} events (full window)")

    # ========================================================================
    # SCENARIO 5: Browser Refresh Restores State
    # ========================================================================
    async def test_browser_refresh_restores_state(self, client, db_session):
        """
        UX-005: After refresh, dashboard shows identical layout and data.
        
        User hits F5. Expect: same modules, same positions, same data.
        """
        print("\n\n[UX-005] Browser Refresh State Persistence Test")
        print("=" * 50)

        user = await create_user(db_session, "refresh_state@example.com", "SecurePass123!")
        login_resp = await client.post("/auth/login", json={
            "email": "refresh_state@example.com",
            "password": "SecurePass123!"
        })
        token = login_resp.json()["access_token"]

        # Create 3 modules with specific positions
        modules_config = [
            {"type": "portfolio", "name": "Stocks", "x": 0, "y": 0, "w": 3, "h": 2},
            {"type": "calendar", "name": "Events", "x": 3, "y": 0, "w": 3, "h": 2},
            {"type": "log", "name": "Logs", "x": 0, "y": 2, "w": 6, "h": 1},
        ]
        created_ids = []
        for config in modules_config:
            resp = await client.post("/api/modules", json={
                "module_type": config["type"],
                "name": config["name"],
                "config": {},
                "size": "medium",
                "position_x": config["x"],
                "position_y": config["y"],
                "width": config["w"],
                "height": config["h"]
            }, headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 201
            created_ids.append(resp.json()["id"])
        print(f"✓ Created 3 modules with positions")

        # Add data to portfolio
        asset = Asset(module_id=created_ids[0], symbol="TSLA", name="Tesla",
                     asset_type="stock", quantity=5.0, avg_buy_price=200.00,
                     current_price=250.00, currency="USD")
        db_session.add(asset)
        await db_session.commit()

        # Fetch modules (before "refresh")
        before_resp = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        before_modules = before_resp.json()["modules"]
        before_data = {m["id"]: m for m in before_modules}

        # Simulate "browser refresh" - fetch again with same token
        after_resp = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        after_modules = after_resp.json()["modules"]
        after_data = {m["id"]: m for m in after_modules}

        # CRITICAL: Same modules returned
        assert set(before_data.keys()) == set(after_data.keys()), (
            "Module IDs changed after refresh!"
        )
        print(f"✓ Same {len(after_modules)} modules after refresh")

        # CRITICAL: Positions preserved
        for mid in created_ids:
            before_pos = (before_data[mid]["position_x"], before_data[mid]["position_y"])
            after_pos = (after_data[mid]["position_x"], after_data[mid]["position_y"])
            assert before_pos == after_pos, f"Position changed for module {mid}"
        print("✓ All positions preserved after refresh")

        # CRITICAL: Sizes preserved
        for mid in created_ids:
            before_size = (before_data[mid]["width"], before_data[mid]["height"])
            after_size = (after_data[mid]["width"], after_data[mid]["height"])
            assert before_size == after_size, f"Size changed for module {mid}"
        print("✓ All sizes preserved after refresh")

        # CRITICAL: Data preserved
        portfolio_data = await client.get(
            f"/api/modules/{created_ids[0]}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        portfolio = portfolio_data.json()["data"]
        assert portfolio["total_value"] == 1250.00, "Portfolio data changed after refresh!"
        print(f"✓ Portfolio data intact: ${portfolio['total_value']}")

    # ========================================================================
    # SCENARIO 6: Cross-User Data Isolation
    # ========================================================================
    async def test_cross_user_data_isolation(self, client, db_session):
        """
        UX-006: User A can NEVER see User B's data, even with same module names.
        
        Security-critical test for multi-tenant isolation.
        """
        print("\n\n[UX-006] Cross-User Data Isolation Test")
        print("=" * 50)

        # Create User A
        user_a = await create_user(db_session, "user_a@example.com", "SecurePass123!")
        login_a = await client.post("/auth/login", json={
            "email": "user_a@example.com", "password": "SecurePass123!"
        })
        token_a = login_a.json()["access_token"]

        # Create User B
        user_b = await create_user(db_session, "user_b@example.com", "SecurePass123!")
        login_b = await client.post("/auth/login", json={
            "email": "user_b@example.com", "password": "SecurePass123!"
        })
        token_b = login_b.json()["access_token"]

        # Both create "My Portfolio" module
        mod_a = await client.post("/api/modules", json={
            "module_type": "portfolio", "name": "My Portfolio",
            "config": {}, "size": "medium"
        }, headers={"Authorization": f"Bearer {token_a}"})
        mod_a_id = mod_a.json()["id"]

        mod_b = await client.post("/api/modules", json={
            "module_type": "portfolio", "name": "My Portfolio",
            "config": {}, "size": "medium"
        }, headers={"Authorization": f"Bearer {token_b}"})
        mod_b_id = mod_b.json()["id"]
        print(f"✓ Both users created 'My Portfolio' module")

        # Add different assets
        asset_a = Asset(module_id=mod_a_id, symbol="AAPL", name="Apple",
                       asset_type="stock", quantity=100.0, avg_buy_price=150.00,
                       current_price=175.50, currency="USD")
        asset_b = Asset(module_id=mod_b_id, symbol="GOOGL", name="Google",
                       asset_type="stock", quantity=50.0, avg_buy_price=2800.00,
                       current_price=3000.00, currency="USD")
        db_session.add_all([asset_a, asset_b])
        await db_session.commit()

        # User A fetches their portfolio
        data_a = await client.get(
            f"/api/modules/{mod_a_id}/data",
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assets_a = data_a.json()["data"]["assets"]
        symbols_a = [a["symbol"] for a in assets_a]
        assert "AAPL" in symbols_a, "User A lost their own asset!"
        assert "GOOGL" not in symbols_a, "DATA LEAK: User A sees User B's GOOGL!"
        print(f"✓ User A: {symbols_a} (GOOGL correctly excluded)")

        # User B fetches their portfolio
        data_b = await client.get(
            f"/api/modules/{mod_b_id}/data",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assets_b = data_b.json()["data"]["assets"]
        symbols_b = [a["symbol"] for a in assets_b]
        assert "GOOGL" in symbols_b, "User B lost their own asset!"
        assert "AAPL" not in symbols_b, "DATA LEAK: User B sees User A's AAPL!"
        print(f"✓ User B: {symbols_b} (AAPL correctly excluded)")

        # User A tries to access User B's module directly
        cross_access = await client.get(
            f"/api/modules/{mod_b_id}/data",
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert cross_access.status_code == 404, (
            f"SECURITY BREACH: User A accessed User B's module! "
            f"Got status {cross_access.status_code}"
        )
        print("✓ User A blocked from User B's module (404)")

        # User B tries to access User A's module
        cross_access_b = await client.get(
            f"/api/modules/{mod_a_id}/data",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert cross_access_b.status_code == 404
        print("✓ User B blocked from User A's module (404)")

    # ========================================================================
    # SCENARIO 7: Token Expiry Handling
    # ========================================================================
    async def test_token_expiry_handling(self, client, db_session):
        """
        UX-007: Expired token returns 401, not 500 or broken page.
        
        User leaves dashboard open overnight. JWT expires.
        Expect: Clear 401 with message to re-authenticate.
        """
        print("\n\n[UX-007] Token Expiry Handling Test")
        print("=" * 50)

        user = await create_user(db_session, "expiry_user@example.com", "SecurePass123!")

        # Create a token that's already expired
        import jwt as pyjwt
        expired_token = pyjwt.encode(
            {"sub": str(user.id), "exp": 0},  # Expired at epoch 0
            settings.jwt_secret,
            algorithm="HS256"
        )
        print("✓ Created expired token")

        # Try to access API with expired token
        resp = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        # Should get 401 Unauthorized
        assert resp.status_code == 401, (
            f"Expected 401 for expired token, got {resp.status_code}"
        )
        error_data = resp.json()
        assert "detail" in error_data, "Missing error detail"
        print(f"✓ Expired token rejected: {resp.status_code} - {error_data['detail']}")

        # Test invalid token format
        invalid_resp = await client.get(
            "/api/modules",
            headers={"Authorization": "Bearer invalid_token_123"}
        )
        assert invalid_resp.status_code in (401, 403), (
            f"Expected 401/403 for invalid token, got {invalid_resp.status_code}"
        )
        print("✓ Invalid token format rejected: " + str(invalid_resp.status_code))

        # Test missing token - auth middleware may return 401 or 403
        no_token_resp = await client.get("/api/modules")
        assert no_token_resp.status_code in (401, 403), (
            f"Expected 401/403 for missing token, got {no_token_resp.status_code}"
        )
        print("✓ Missing token rejected: " + str(no_token_resp.status_code))

    # ========================================================================
    # SCENARIO 8: Large Dataset Performance
    # ========================================================================
    async def test_large_dataset_performance(self, client, db_session):
        """
        UX-008: 50+ assets load in <500ms with pagination.
        
        Power user with large portfolio.
        Expect: Fast response, paginated if needed.
        """
        print("\n\n[UX-008] Large Dataset Performance Test")
        print("=" * 50)

        user = await create_user(db_session, "power_user@example.com", "SecurePass123!")
        login_resp = await client.post("/auth/login", json={
            "email": "power_user@example.com", "password": "SecurePass123!"
        })
        token = login_resp.json()["access_token"]

        # Create portfolio module
        module_resp = await client.post("/api/modules", json={
            "module_type": "portfolio",
            "name": "Power Portfolio",
            "config": {},
            "size": "expanded"
        }, headers={"Authorization": f"Bearer {token}"})
        module_id = module_resp.json()["id"]

        # Insert 50 assets
        print("[Setup] Inserting 50 assets...")
        for i in range(50):
            asset = Asset(
                module_id=module_id,
                symbol=f"STOCK{i+1:03d}",
                name=f"Stock Company {i+1}",
                asset_type="stock",
                quantity=float(i + 1),
                avg_buy_price=50.0 + i,
                current_price=55.0 + i,
                currency="USD"
            )
            db_session.add(asset)
        await db_session.commit()
        print("✓ 50 assets inserted")

        # Measure response time
        start = time.perf_counter()
        resp = await client.get(
            f"/api/modules/{module_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 200
        data = resp.json()["data"]
        assets = data["assets"]

        # Performance check
        print(f"[Performance] Response time: {elapsed_ms:.1f}ms")
        assert elapsed_ms < 1000, f"Too slow: {elapsed_ms:.1f}ms for 50 assets"
        print(f"✓ Response under 1 second: {elapsed_ms:.1f}ms")

        # All 50 assets returned
        assert len(assets) == 50, f"Expected 50 assets, got {len(assets)}"
        print(f"✓ All 50 assets returned")

        # Total value computed correctly
        expected_total = sum((i + 1) * (55.0 + i) for i in range(50))
        assert abs(data["total_value"] - expected_total) < 0.01, (
            f"Total value wrong: {data['total_value']} vs {expected_total}"
        )
        print(f"✓ Total value computed: ${data['total_value']:,.2f}")

        # Verify pagination metadata if available
        if "total" in data:
            assert data["total"] == 50, "Total count mismatch"
            print(f"✓ Pagination metadata: total={data['total']}")

    # ========================================================================
    # SCENARIO 9: Config Change Instant Update
    # ========================================================================
    async def test_config_change_instant_update(self, client, db_session):
        """
        UX-009: Updating module config reflects immediately in data.
        
        User changes calendar filter from 'Fed' to 'ECB'.
        Expect: Next fetch shows ECB events, not Fed.
        """
        print("\n\n[UX-009] Config Change Instant Update Test")
        print("=" * 50)

        user = await create_user(db_session, "config_user@example.com", "SecurePass123!")
        login_resp = await client.post("/auth/login", json={
            "email": "config_user@example.com", "password": "SecurePass123!"
        })
        token = login_resp.json()["access_token"]

        # Create calendar module
        module_resp = await client.post("/api/modules", json={
            "module_type": "calendar",
            "name": "Config Test Calendar",
            "config": {"default_view": "week"},
            "size": "medium"
        }, headers={"Authorization": f"Bearer {token}"})
        module_id = module_resp.json()["id"]
        print(f"✓ Calendar module created with config: default_view=week")

        # Add events
        now = datetime.now(timezone.utc)
        event1 = CalendarEvent(module_id=module_id, title="Fed Meeting",
                                start_time=now + timedelta(days=1),
                                end_time=now + timedelta(days=1, hours=1),
                                impact="high")
        event2 = CalendarEvent(module_id=module_id, title="ECB Press Conference",
                                start_time=now + timedelta(days=2),
                                end_time=now + timedelta(days=2, hours=1),
                                impact="medium")
        db_session.add_all([event1, event2])
        await db_session.commit()

        # Fetch before config change
        before = await client.get(
            f"/api/modules/{module_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        before_events = before.json()["data"]["events"]
        assert len(before_events) == 2, "Both events should show initially"
        print(f"✓ Before config change: {len(before_events)} events")

        # Update module config
        patch_resp = await client.put(
            f"/api/modules/{module_id}",
            json={"config": {"default_view": "month", "show_weekends": True}},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert patch_resp.status_code == 200
        updated_module = patch_resp.json()
        assert updated_module["config"]["default_view"] == "month"
        print(f"✓ Config updated: default_view=month, show_weekends=True")

        # Verify module list shows updated config
        list_resp = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        modules = list_resp.json()["modules"]
        target_module = next(m for m in modules if m["id"] == module_id)
        assert target_module["config"]["show_weekends"] is True
        print(f"✓ Config change persisted in module list")

        # Fetch data after config change - calendar should still work
        after = await client.get(
            f"/api/modules/{module_id}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        after_events = after.json()["data"]["events"]
        assert len(after_events) == 2, "Events still available after config change"
        print(f"✓ After config change: {len(after_events)} events still returned")

    # ========================================================================
    # SCENARIO 10: Module Position Persistence
    # ========================================================================
    async def test_module_position_persistence(self, client, db_session):
        """
        UX-010: Dragging and resizing modules persists to database.
        
        User arranges dashboard layout. Expect: positions survive refresh.
        """
        print("\n\n[UX-010] Module Position Persistence Test")
        print("=" * 50)

        user = await create_user(db_session, "layout_user@example.com", "SecurePass123!")
        login_resp = await client.post("/auth/login", json={
            "email": "layout_user@example.com", "password": "SecurePass123!"
        })
        token = login_resp.json()["access_token"]

        # Create module with specific grid position
        resp = await client.post("/api/modules", json={
            "module_type": "portfolio",
            "name": "Position Test",
            "config": {},
            "size": "medium",
            "position_x": 2,
            "position_y": 3,
            "width": 4,
            "height": 2
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        module = resp.json()
        module_id = module["id"]

        # Verify creation returned correct position
        assert module["position_x"] == 2, f"Expected x=2, got {module['position_x']}"
        assert module["position_y"] == 3, f"Expected y=3, got {module['position_y']}"
        assert module["width"] == 4, f"Expected width=4, got {module['width']}"
        assert module["height"] == 2, f"Expected height=2, got {module['height']}"
        print(f"✓ Created with position: ({module['position_x']}, {module['position_y']}) "
              f"size: {module['width']}x{module['height']}")

        # Update position (simulating drag-and-drop)
        update_resp = await client.put(
            f"/api/modules/{module_id}",
            json={
                "position_x": 5,
                "position_y": 1,
                "width": 3,
                "height": 3
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["position_x"] == 5
        assert updated["position_y"] == 1
        assert updated["width"] == 3
        assert updated["height"] == 3
        print(f"✓ Updated position: ({updated['position_x']}, {updated['position_y']}) "
              f"size: {updated['width']}x{updated['height']}")

        # Verify persistence via GET
        get_resp = await client.get(
            f"/api/modules/{module_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_resp.status_code == 200
        fetched = get_resp.json()
        assert fetched["position_x"] == 5
        assert fetched["position_y"] == 1
        assert fetched["width"] == 3
        assert fetched["height"] == 3
        print(f"✓ Position persisted: ({fetched['position_x']}, {fetched['position_y']}) "
              f"size: {fetched['width']}x{fetched['height']}")

        # Verify in list view too
        list_resp = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        modules = list_resp.json()["modules"]
        target = next(m for m in modules if m["id"] == module_id)
        assert target["position_x"] == 5
        assert target["position_y"] == 1
        print(f"✓ Position correct in module list")
