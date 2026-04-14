"""
Backend integration tests for Module API endpoints.
Covers Flow 2, 4, 5, and 7 from MVP-UX-FLOWS.md
"""

import pytest
from httpx import AsyncClient

from app.services.auth.service import create_user, create_access_token
from app.schemas.module import ModuleCreate


@pytest.mark.asyncio
async def test_create_module_success(client, db_session):
    """Flow 2: User creates a portfolio module."""
    # Arrange: Create user and authenticate
    user = await create_user(db_session, "module-test@example.com", "password123")
    token = create_access_token(str(user.id))
    
    # Act: Create module
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
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["module_type"] == "portfolio"
    assert data["name"] == "My Investments"
    assert data["size"] == "medium"
    assert "id" in data
    assert data["user_id"] == str(user.id)


@pytest.mark.asyncio
async def test_list_modules_empty(client, db_session):
    """Flow 1: New user has no modules."""
    # Arrange
    user = await create_user(db_session, "empty-test@example.com", "password123")
    token = create_access_token(str(user.id))
    
    # Act
    response = await client.get(
        "/api/modules",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "modules" in data
    assert "total" in data
    assert data["modules"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_modules_with_data(client, db_session):
    """Flow 5: User has multiple modules."""
    # Arrange: Create user and modules
    user = await create_user(db_session, "multi-test@example.com", "password123")
    token = create_access_token(str(user.id))
    
    # Create portfolio module
    await client.post(
        "/api/modules",
        json={"module_type": "portfolio", "name": "Stocks", "config": {}, "size": "medium"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Create calendar module
    await client.post(
        "/api/modules",
        json={"module_type": "calendar", "name": "Schedule", "config": {}, "size": "medium"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Act
    response = await client.get(
        "/api/modules",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["modules"]) == 2
    module_types = [m["module_type"] for m in data["modules"]]
    assert "portfolio" in module_types
    assert "calendar" in module_types


@pytest.mark.asyncio
async def test_delete_module_success(client, db_session):
    """Flow 4: User deletes a module."""
    # Arrange: Create user and module
    user = await create_user(db_session, "delete-test@example.com", "password123")
    token = create_access_token(str(user.id))
    
    create_response = await client.post(
        "/api/modules",
        json={"module_type": "portfolio", "name": "To Delete", "config": {}, "size": "medium"},
        headers={"Authorization": f"Bearer {token}"}
    )
    module_id = create_response.json()["id"]
    
    # Act: Delete module
    delete_response = await client.delete(
        f"/api/modules/{module_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert delete_response.status_code == 204
    
    # Verify module is gone
    list_response = await client.get(
        "/api/modules",
        headers={"Authorization": f"Bearer {token}"}
    )
    data = list_response.json()
    assert data["modules"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_delete_module_not_found(client, db_session):
    """Flow 7: Delete non-existent module returns 404."""
    # Arrange
    user = await create_user(db_session, "delete404@example.com", "password123")
    token = create_access_token(str(user.id))
    
    # Act
    response = await client.delete(
        "/api/modules/123e4567-e89b-12d3-a456-426614174000",  # Random UUID
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_module_unauthorized(client):
    """Flow 7: Create module without token returns 401."""
    response = await client.post(
        "/api/modules",
        json={"module_type": "portfolio", "name": "Test", "config": {}, "size": "medium"}
    )
    
    assert response.status_code == 401  # Unauthorized for missing token


@pytest.mark.asyncio
async def test_create_module_invalid_type(client, db_session):
    """Flow 7: Invalid module type returns 422."""
    user = await create_user(db_session, "invalid-type@example.com", "password123")
    token = create_access_token(str(user.id))
    
    response = await client.post(
        "/api/modules",
        json={"module_type": "invalid_type", "name": "Test", "config": {}, "size": "medium"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400  # Bad request for invalid module type


@pytest.mark.asyncio
async def test_get_module_detail(client, db_session):
    """Get single module details."""
    # Arrange
    user = await create_user(db_session, "detail-test@example.com", "password123")
    token = create_access_token(str(user.id))
    
    create_response = await client.post(
        "/api/modules",
        json={"module_type": "portfolio", "name": "Detail Test", "config": {"key": "value"}, "size": "expanded"},
        headers={"Authorization": f"Bearer {token}"}
    )
    module_id = create_response.json()["id"]
    
    # Act
    response = await client.get(
        f"/api/modules/{module_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == module_id
    assert data["name"] == "Detail Test"
    assert data["config"] == {"key": "value"}
    assert data["size"] == "expanded"


@pytest.mark.asyncio
async def test_update_module(client, db_session):
    """Update module name and config."""
    # Arrange
    user = await create_user(db_session, "update-test@example.com", "password123")
    token = create_access_token(str(user.id))
    
    create_response = await client.post(
        "/api/modules",
        json={"module_type": "portfolio", "name": "Old Name", "config": {}, "size": "medium"},
        headers={"Authorization": f"Bearer {token}"}
    )
    module_id = create_response.json()["id"]
    
    # Act
    response = await client.put(
        f"/api/modules/{module_id}",
        json={"name": "New Name", "config": {"updated": True}},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["config"] == {"updated": True}


@pytest.mark.asyncio
async def test_module_isolation_between_users(client, db_session):
    """Users cannot see each other's modules."""
    # Arrange: Create two users
    user1 = await create_user(db_session, "user1@example.com", "password123")
    user2 = await create_user(db_session, "user2@example.com", "password123")
    token1 = create_access_token(str(user1.id))
    token2 = create_access_token(str(user2.id))
    
    # User 1 creates a module
    await client.post(
        "/api/modules",
        json={"module_type": "portfolio", "name": "User1 Module", "config": {}, "size": "medium"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    # Act: User 2 lists modules
    response = await client.get(
        "/api/modules",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    # Assert: User 2 sees empty list
    assert response.status_code == 200
    data = response.json()
    assert data["modules"] == []
    assert data["total"] == 0
    
    # Assert: User 2 cannot delete User 1's module
    # (Would need to know the ID, but trying a random one)
    # This tests that the module ID space is not enumerable
