"""
MVP Flow Tests - Complete user journey validation.
Covers all 7 flows from MVP-UX-FLOWS.md
"""

import pytest
from httpx import AsyncClient

from app.services.auth.service import create_user, create_access_token


class TestFlow1FirstTimeUserOnboarding:
    """Flow 1: First-time user registers, logs in, sees empty dashboard"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_new_user_sees_empty_dashboard(self, client, db_session):
        """Step 1.1-1.7: New user onboarding flow
        
        Note: MVP uses direct user creation via service (no registration endpoint)
        """
        # Create user via service (MVP: registration via API not implemented)
        user = await create_user(db_session, "newuser@example.com", "testpass123")
        
        # Login
        login_response = await client.post("/auth/login", json={
            "email": "newuser@example.com",
            "password": "testpass123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Verify empty dashboard
        modules_response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert modules_response.status_code == 200
        assert modules_response.json()["modules"] == []
        
        # Verify layout exists (auto-created)
        layout_response = await client.get(
            "/api/dashboard/layout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert layout_response.status_code == 200
        assert layout_response.json()["positions"] == []


class TestFlow2AddFirstPortfolioModule:
    """Flow 2: User adds a portfolio module"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_add_portfolio_module_flow(self, client, db_session):
        """Step 2.1-2.6: Add portfolio module"""
        # Setup: Create and login user
        user = await create_user(db_session, "portfolio-user@example.com", "password123")
        token = create_access_token(str(user.id))
        
        # Step 2.1-2.5: Add module
        response = await client.post(
            "/api/modules",
            json={
                "module_type": "portfolio",
                "name": "My Investments",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Step 2.6: Verify module appears with correct data
        assert response.status_code == 201
        data = response.json()
        assert data["module_type"] == "portfolio"
        assert data["name"] == "My Investments"
        assert data["size"] == "medium"
        assert data["is_active"] is True
        assert "id" in data
        
        # Verify module appears in list
        list_response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == 200
        modules = list_response.json()["modules"]
        assert len(modules) == 1
        assert modules[0]["name"] == "My Investments"


class TestFlow3SessionPersistence:
    """Flow 3: User returns and finds dashboard intact"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_dashboard_persists_across_sessions(self, client, db_session):
        """Step 3.1-3.7: Session persistence"""
        # Setup: Create user with modules
        user = await create_user(db_session, "persist-user@example.com", "password123")
        token1 = create_access_token(str(user.id))
        
        # Create module
        await client.post(
            "/api/modules",
            json={
                "module_type": "portfolio",
                "name": "My Investments",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token1}"}
        )
        
        # Set layout
        await client.put(
            "/api/dashboard/layout",
            json={
                "columns": 12,
                "row_height": 100,
                "positions": []
            },
            headers={"Authorization": f"Bearer {token1}"}
        )
        
        # Simulate new session with fresh token (but same user)
        token2 = create_access_token(str(user.id))
        
        # Verify data persists
        modules_response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert modules_response.status_code == 200
        modules = modules_response.json()["modules"]
        assert len(modules) == 1
        assert modules[0]["name"] == "My Investments"
        
        layout_response = await client.get(
            "/api/dashboard/layout",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert layout_response.status_code == 200


class TestFlow4DeleteModule:
    """Flow 4: User removes a module"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_delete_module_flow(self, client, db_session):
        """Step 4.1-4.5: Delete module flow"""
        # Setup
        user = await create_user(db_session, "delete-user@example.com", "password123")
        token = create_access_token(str(user.id))
        
        # Create module to delete
        create_response = await client.post(
            "/api/modules",
            json={
                "module_type": "portfolio",
                "name": "To Delete",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        module_id = create_response.json()["id"]
        
        # Verify module exists
        list_before = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert len(list_before.json()["modules"]) == 1
        
        # Delete module (Step 4.5)
        delete_response = await client.delete(
            f"/api/modules/{module_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert delete_response.status_code == 204
        
        # Verify empty state (Step 4.5)
        list_after = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_after.json()["modules"] == []


class TestFlow5AddMultipleModuleTypes:
    """Flow 5: User creates diverse dashboard"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_add_multiple_module_types(self, client, db_session):
        """Step 5.1-5.5: Add portfolio, calendar, and log modules"""
        # Setup
        user = await create_user(db_session, "multi-user@example.com", "password123")
        token = create_access_token(str(user.id))
        
        # Add Portfolio (Step 5.1)
        await client.post(
            "/api/modules",
            json={"module_type": "portfolio", "name": "Stocks", "config": {}, "size": "medium"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Add Calendar (Step 5.2)
        await client.post(
            "/api/modules",
            json={"module_type": "calendar", "name": "Schedule", "config": {}, "size": "medium"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Add Log (Step 5.3)
        await client.post(
            "/api/modules",
            json={"module_type": "log", "name": "Notes", "config": {}, "size": "medium"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Verify all 3 modules exist (Step 5.4)
        response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        modules = response.json()["modules"]
        assert len(modules) == 3
        
        module_types = [m["module_type"] for m in modules]
        assert "portfolio" in module_types
        assert "calendar" in module_types
        assert "log" in module_types


class TestFlow6LogoutAndRelogin:
    """Flow 6: User logout and re-login"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_logout_and_relogin_flow(self, client, db_session):
        """Step 6.1-6.5: Logout clears session, re-login works"""
        from app.services.auth.service import create_refresh_token
        
        # Setup: Create user with data
        user = await create_user(db_session, "relogin-user@example.com", "password123")
        access_token = create_access_token(str(user.id))
        refresh_token_str, _ = await create_refresh_token(db_session, str(user.id))
        
        # Create a module
        await client.post(
            "/api/modules",
            json={"module_type": "portfolio", "name": "My Portfolio", "config": {}, "size": "medium"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Logout (Step 6.2)
        logout_response = await client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token_str},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert logout_response.status_code == 204
        
        # Verify refresh token revoked (Step 6.3)
        refresh_response = await client.post("/auth/refresh", json={
            "refresh_token": refresh_token_str
        })
        assert refresh_response.status_code == 401
        
        # Re-login (Step 6.5)
        login_response = await client.post("/auth/login", json={
            "email": "relogin-user@example.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        new_token = login_response.json()["access_token"]
        
        # Verify data persisted
        modules_response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert modules_response.status_code == 200
        assert len(modules_response.json()["modules"]) == 1


class TestFlow7ErrorHandling:
    """Flow 7: Error handling scenarios"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_invalid_login_error(self, client, db_session):
        """Scenario 7a: Invalid login shows error"""
        # Create user first
        await create_user(db_session, "error-test@example.com", "password123")
        
        # Try wrong password (Step 7a.3)
        response = await client.post("/auth/login", json={
            "email": "error-test@example.com",
            "password": "wrongpassword"
        })
        
        # Verify error (Step 7a.4)
        assert response.status_code == 401
        assert "detail" in response.json()
    
    @pytest.mark.asyncio
    async def test_unauthorized_access_error(self, client):
        """Scenario 7b: Protected endpoint without auth"""
        # Try to access dashboard without token
        response = await client.get("/api/modules")
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_invalid_module_type_error(self, client, db_session):
        """Scenario 7c: Invalid module type returns 422"""
        user = await create_user(db_session, "invalid-type@example.com", "password123")
        token = create_access_token(str(user.id))
        
        response = await client.post(
            "/api/modules",
            json={"module_type": "invalid_type", "name": "Test", "config": {}},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_module_error(self, client, db_session):
        """Delete non-existent module returns 404"""
        user = await create_user(db_session, "delete404@example.com", "password123")
        token = create_access_token(str(user.id))
        
        response = await client.delete(
            "/api/modules/123e4567-e89b-12d3-a456-426614174000",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404


class TestMVPAPIContract:
    """Verify API response schemas match MVP contract"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_get_modules_response_schema(self, client, db_session):
        """Verify GET /api/modules returns correct schema"""
        user = await create_user(db_session, "schema-test@example.com", "password123")
        token = create_access_token(str(user.id))
        
        # Create a module
        await client.post(
            "/api/modules",
            json={"module_type": "portfolio", "name": "Test Module", "config": {}, "size": "medium"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get modules and verify schema
        response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "modules" in data
        modules = data["modules"]
        assert isinstance(modules, list)
        assert len(modules) == 1
        
        module = modules[0]
        required_fields = ["id", "module_type", "name", "config", "size", "is_active", "created_at"]
        for field in required_fields:
            assert field in module, f"Missing required field: {field}"
        
        assert module["module_type"] == "portfolio"
        assert module["name"] == "Test Module"
        assert module["size"] == "medium"
        assert module["is_active"] is True
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_post_modules_response_schema(self, client, db_session):
        """Verify POST /api/modules returns correct schema"""
        user = await create_user(db_session, "schema-post@example.com", "password123")
        token = create_access_token(str(user.id))
        
        response = await client.post(
            "/api/modules",
            json={"module_type": "calendar", "name": "My Calendar", "config": {}, "size": "medium"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        required_fields = ["id", "module_type", "name", "config", "size",
                          "is_active", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert data["module_type"] == "calendar"
        assert data["name"] == "My Calendar"
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_error_response_schema(self, client):
        """Verify error responses include detail field"""
        response = await client.get("/api/modules")  # No auth
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data


class TestMVPLimitations:
    """Test known MVP limitations are documented"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_registration_via_service_only(self, client, db_session):
        """Registration UI not implemented - use service directly"""
        # This documents that registration works via service
        user = await create_user(db_session, "service-register@example.com", "testpass123")
        assert user is not None
        
        # Verify can login after service registration
        login_response = await client.post("/auth/login", json={
            "email": "service-register@example.com",
            "password": "testpass123"
        })
        assert login_response.status_code == 200
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_module_data_placeholder(self, client, db_session):
        """MVP shows placeholder data, not real values"""
        user = await create_user(db_session, "placeholder@example.com", "password123")
        token = create_access_token(str(user.id))
        
        # Create portfolio module
        await client.post(
            "/api/modules",
            json={"module_type": "portfolio", "name": "Stocks", "config": {}, "size": "medium"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # In MVP, module data endpoint returns placeholder
        # This test documents current behavior
        modules_response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert modules_response.status_code == 200
        # MVP: No real data yet, just module metadata
        modules = modules_response.json()["modules"]
        assert len(modules) == 1
        assert modules[0]["config"] == {}  # Empty config in MVP
