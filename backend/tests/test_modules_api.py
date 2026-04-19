"""
QA-003: Backend API tests - Module CRUD

Tests for module CRUD operations per DEV-004.
Validates that module endpoints work correctly with authentication.

Related: DEV-004, ARCHITECTURE.md Section 5.2, 7
"""

import pytest
from uuid import uuid4

from app.services.auth.service import create_user, create_access_token
from app.models.module import Module


def get_auth_headers(user_id: str) -> dict:
    """Create authorization headers for a user."""
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


class TestModuleCreate:
    """Test POST /api/modules - Create module."""

    @pytest.mark.asyncio
    async def test_create_module_with_valid_data(self, client, db_session):
        """QA-003-001: Create module with valid data succeeds."""
        user = await create_user(db_session, "module-create@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        module_data = {
            "name": "My Portfolio",
            "module_type": "portfolio",
            "config": {"currency": "SGD"},
            "position_x": 0,
            "position_y": 0,
            "width": 2,
            "height": 2,
        }

        response = await client.post("/api/modules", json=module_data, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Portfolio"
        assert data["module_type"] == "portfolio"
        assert data["user_id"] == str(user.id)
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_module_with_invalid_type_fails(self, client, db_session):
        """QA-003-002: Create module with invalid type fails."""
        user = await create_user(db_session, "module-invalid@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        module_data = {
            "name": "Invalid Module",
            "module_type": "invalid_type",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }

        response = await client.post("/api/modules", json=module_data, headers=headers)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_module_without_auth_fails(self, client, db_session):
        """QA-003-003: Create module without authentication fails."""
        module_data = {
            "name": "My Module",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }

        response = await client.post("/api/modules", json=module_data)

        assert response.status_code in (401, 403)  # Either is acceptable for auth failure

    @pytest.mark.asyncio
    async def test_create_module_with_missing_name_fails(self, client, db_session):
        """QA-003-004: Create module without required name fails."""
        user = await create_user(db_session, "module-noname@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        module_data = {
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }

        response = await client.post("/api/modules", json=module_data, headers=headers)

        assert response.status_code == 422


class TestModuleList:
    """Test GET /api/modules - List modules."""

    @pytest.mark.asyncio
    async def test_list_modules_returns_only_user_modules(self, client, db_session):
        """QA-003-005: List modules returns only the user's modules."""
        user1 = await create_user(db_session, "user1@example.com", "password123")
        user2 = await create_user(db_session, "user2@example.com", "password123")

        # Create module for user1
        headers1 = get_auth_headers(str(user1.id))
        module_data = {
            "name": "User1 Portfolio",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }
        await client.post("/api/modules", json=module_data, headers=headers1)

        # Create module for user2
        headers2 = get_auth_headers(str(user2.id))
        module_data2 = {
            "name": "User2 Calendar",
            "module_type": "calendar",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }
        await client.post("/api/modules", json=module_data2, headers=headers2)

        # List as user1
        response = await client.get("/api/modules", headers=headers1)
        assert response.status_code == 200
        data = response.json()

        assert len(data["modules"]) == 1
        assert data["total"] == 1
        assert data["modules"][0]["name"] == "User1 Portfolio"

    @pytest.mark.asyncio
    async def test_list_modules_empty_for_new_user(self, client, db_session):
        """QA-003-006: List modules returns empty for new user."""
        user = await create_user(db_session, "newuser@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        response = await client.get("/api/modules", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["modules"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_modules_without_auth_fails(self, client, db_session):
        """QA-003-007: List modules without authentication fails."""
        response = await client.get("/api/modules")
        assert response.status_code in (401, 403)  # Either is acceptable for auth failure


class TestModuleUpdate:
    """Test PUT /api/modules/{id} - Update module."""

    @pytest.mark.asyncio
    async def test_update_module_settings_persists(self, client, db_session):
        """QA-003-008: Update module settings persists correctly."""
        user = await create_user(db_session, "module-update@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Create module
        module_data = {
            "name": "Original Name",
            "module_type": "portfolio",
            "config": {"currency": "SGD"},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers)
        module_id = create_response.json()["id"]

        # Update module
        update_data = {
            "name": "Updated Name",
            "config": {"currency": "USD"},
        }
        response = await client.put(f"/api/modules/{module_id}", json=update_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["config"]["currency"] == "USD"

    @pytest.mark.asyncio
    async def test_update_module_not_found_fails(self, client, db_session):
        """QA-003-009: Update non-existent module fails with 404."""
        user = await create_user(db_session, "module-update-404@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        fake_id = str(uuid4())
        update_data = {"name": "New Name"}

        response = await client.put(f"/api/modules/{fake_id}", json=update_data, headers=headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_other_user_module_fails(self, client, db_session):
        """QA-003-010: Cannot update another user's module."""
        user1 = await create_user(db_session, "user1-update@example.com", "password123")
        user2 = await create_user(db_session, "user2-update@example.com", "password123")

        # Create module as user1
        headers1 = get_auth_headers(str(user1.id))
        module_data = {
            "name": "User1 Module",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers1)
        module_id = create_response.json()["id"]

        # Try to update as user2
        headers2 = get_auth_headers(str(user2.id))
        update_data = {"name": "Hacked Name"}
        response = await client.put(f"/api/modules/{module_id}", json=update_data, headers=headers2)

        assert response.status_code == 404  # Should not reveal existence


class TestModuleDelete:
    """Test DELETE /api/modules/{id} - Delete module."""

    @pytest.mark.asyncio
    async def test_delete_module_removes_from_dashboard(self, client, db_session):
        """QA-003-011: Delete module removes it from dashboard."""
        user = await create_user(db_session, "module-delete@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Create module
        module_data = {
            "name": "To Delete",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers)
        module_id = create_response.json()["id"]

        # Verify module exists
        list_response = await client.get("/api/modules", headers=headers)
        assert len(list_response.json()["modules"]) == 1

        # Delete module
        delete_response = await client.delete(f"/api/modules/{module_id}", headers=headers)
        assert delete_response.status_code == 204

        # Verify module is gone
        list_response = await client.get("/api/modules", headers=headers)
        assert len(list_response.json()["modules"]) == 0

    @pytest.mark.asyncio
    async def test_delete_module_not_found_fails(self, client, db_session):
        """QA-003-012: Delete non-existent module fails with 404."""
        user = await create_user(db_session, "module-delete-404@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        fake_id = str(uuid4())
        response = await client.delete(f"/api/modules/{fake_id}", headers=headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_other_user_module_fails(self, client, db_session):
        """QA-003-013: Cannot delete another user's module."""
        user1 = await create_user(db_session, "user1-delete@example.com", "password123")
        user2 = await create_user(db_session, "user2-delete@example.com", "password123")

        # Create module as user1
        headers1 = get_auth_headers(str(user1.id))
        module_data = {
            "name": "User1 Module",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers1)
        module_id = create_response.json()["id"]

        # Try to delete as user2
        headers2 = get_auth_headers(str(user2.id))
        response = await client.delete(f"/api/modules/{module_id}", headers=headers2)

        assert response.status_code == 404


class TestModuleGet:
    """Test GET /api/modules/{id} - Get single module."""

    @pytest.mark.asyncio
    async def test_get_module_returns_details(self, client, db_session):
        """QA-003-014: Get module returns full details."""
        user = await create_user(db_session, "module-get@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Create module
        module_data = {
            "name": "My Module",
            "module_type": "calendar",
            "config": {"timezone": "UTC"},
            "position_x": 1,
            "position_y": 2,
            "width": 3,
            "height": 2,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers)
        module_id = create_response.json()["id"]

        # Get module
        response = await client.get(f"/api/modules/{module_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == module_id
        assert data["name"] == "My Module"
        assert data["module_type"] == "calendar"
        assert data["config"]["timezone"] == "UTC"
        assert data["position_x"] == 1
        assert data["position_y"] == 2
        assert data["width"] == 3
        assert data["height"] == 2

    @pytest.mark.asyncio
    async def test_get_module_not_found_fails(self, client, db_session):
        """QA-003-015: Get non-existent module fails with 404."""
        user = await create_user(db_session, "module-get-404@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        fake_id = str(uuid4())
        response = await client.get(f"/api/modules/{fake_id}", headers=headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_other_user_module_fails(self, client, db_session):
        """QA-003-016: Cannot get another user's module."""
        user1 = await create_user(db_session, "user1-get@example.com", "password123")
        user2 = await create_user(db_session, "user2-get@example.com", "password123")

        # Create module as user1
        headers1 = get_auth_headers(str(user1.id))
        module_data = {
            "name": "User1 Module",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers1)
        module_id = create_response.json()["id"]

        # Try to get as user2
        headers2 = get_auth_headers(str(user2.id))
        response = await client.get(f"/api/modules/{module_id}", headers=headers2)

        assert response.status_code == 404


class TestModuleTypes:
    """Test all supported module types."""

    @pytest.mark.asyncio
    async def test_create_portfolio_module(self, client, db_session):
        """QA-003-017: Can create portfolio module."""
        user = await create_user(db_session, "portfolio-type@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        module_data = {
            "name": "Portfolio",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }
        response = await client.post("/api/modules", json=module_data, headers=headers)

        assert response.status_code == 201
        assert response.json()["module_type"] == "portfolio"

    @pytest.mark.asyncio
    async def test_create_calendar_module(self, client, db_session):
        """QA-003-018: Can create calendar module."""
        user = await create_user(db_session, "calendar-type@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        module_data = {
            "name": "Calendar",
            "module_type": "calendar",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }
        response = await client.post("/api/modules", json=module_data, headers=headers)

        assert response.status_code == 201
        assert response.json()["module_type"] == "calendar"

    @pytest.mark.asyncio
    async def test_create_log_module(self, client, db_session):
        """QA-003-019: Can create log module."""
        user = await create_user(db_session, "log-type@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        module_data = {
            "name": "System Logs",
            "module_type": "log",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 1,
            "height": 1,
        }
        response = await client.post("/api/modules", json=module_data, headers=headers)

        assert response.status_code == 201
        assert response.json()["module_type"] == "log"


class TestModulePosition:
    """Test module position and layout constraints."""

    @pytest.mark.asyncio
    async def test_create_module_with_position(self, client, db_session):
        """QA-003-020: Module stores position correctly."""
        user = await create_user(db_session, "module-position@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        module_data = {
            "name": "Positioned Module",
            "module_type": "portfolio",
            "config": {},
            "position_x": 2,
            "position_y": 3,
            "width": 2,
            "height": 1,
        }
        response = await client.post("/api/modules", json=module_data, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["position_x"] == 2
        assert data["position_y"] == 3
        assert data["width"] == 2
        assert data["height"] == 1


class TestModuleTypesEndpoint:
    """Test GET /api/modules/types endpoint."""

    @pytest.mark.asyncio
    async def test_get_module_types_returns_list(self, client, db_session):
        """QA-003-021: Get module types returns available types."""
        user = await create_user(db_session, "module-types@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        response = await client.get("/api/modules/types", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert isinstance(data["types"], list)
        assert "portfolio" in data["types"]
        assert "calendar" in data["types"]
        assert "log" in data["types"]
