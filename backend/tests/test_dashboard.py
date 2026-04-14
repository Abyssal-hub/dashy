"""
Backend integration tests for Dashboard Layout API endpoints.
Covers Flow 3 from MVP-UX-FLOWS.md (layout persistence)
"""

import pytest

from app.services.auth.service import create_user, create_access_token


@pytest.mark.asyncio
async def test_get_layout_creates_default(client, db_session):
    """Flow 3: New user gets default layout auto-created."""
    # Arrange
    user = await create_user(db_session, "layout-new@example.com", "password123")
    token = create_access_token(str(user.id))
    
    # Act
    response = await client.get(
        "/api/dashboard/layout",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["columns"] == 12  # Default
    assert data["row_height"] == 100  # Default
    assert data["positions"] == []  # Empty
    assert data["user_id"] == str(user.id)


@pytest.mark.asyncio
async def test_update_layout(client, db_session):
    """Update layout columns, row_height, and positions."""
    # Arrange
    user = await create_user(db_session, "layout-update@example.com", "password123")
    token = create_access_token(str(user.id))
    
    # Act
    response = await client.put(
        "/api/dashboard/layout",
        json={
            "columns": 16,
            "row_height": 80,
            "positions": [
                {"module_id": "test-module-1", "x": 0, "y": 0, "w": 6, "h": 2}
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["columns"] == 16
    assert data["row_height"] == 80
    assert len(data["positions"]) == 1
    assert data["positions"][0]["module_id"] == "test-module-1"


@pytest.mark.asyncio
async def test_layout_persistence_across_requests(client, db_session):
    """Flow 3: Layout persists across multiple requests (session persistence)."""
    # Arrange
    user = await create_user(db_session, "layout-persist@example.com", "password123")
    token = create_access_token(str(user.id))
    
    # Set layout
    await client.put(
        "/api/dashboard/layout",
        json={
            "columns": 8,
            "row_height": 120,
            "positions": [
                {"module_id": "mod-1", "x": 0, "y": 0, "w": 4, "h": 2},
                {"module_id": "mod-2", "x": 4, "y": 0, "w": 4, "h": 2}
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Act: Get layout again (simulates refresh)
    response = await client.get(
        "/api/dashboard/layout",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert: Data persisted
    assert response.status_code == 200
    data = response.json()
    assert data["columns"] == 8
    assert data["row_height"] == 120
    assert len(data["positions"]) == 2


@pytest.mark.asyncio
async def test_update_layout_partial(client, db_session):
    """Update only specific fields."""
    # Arrange
    user = await create_user(db_session, "layout-partial@example.com", "password123")
    token = create_access_token(str(user.id))
    
    # Set initial layout
    await client.put(
        "/api/dashboard/layout",
        json={"columns": 12, "row_height": 100, "positions": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Act: Update only columns
    response = await client.put(
        "/api/dashboard/layout",
        json={"columns": 24},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["columns"] == 24
    assert data["row_height"] == 100  # Unchanged


@pytest.mark.asyncio
async def test_layout_position_validation_overlap(client, db_session):
    """Flow 7: Overlapping positions return 400 error."""
    # Arrange
    user = await create_user(db_session, "layout-overlap@example.com", "password123")
    token = create_access_token(str(user.id))
    
    # Act: Try to create overlapping positions
    response = await client.put(
        "/api/dashboard/layout",
        json={
            "positions": [
                {"module_id": "mod-1", "x": 0, "y": 0, "w": 4, "h": 2},
                {"module_id": "mod-2", "x": 2, "y": 0, "w": 4, "h": 2}  # Overlaps with mod-1
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 400
    assert "overlap" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_add_module_to_layout(client, db_session):
    """Add single module to existing layout."""
    # Arrange
    user = await create_user(db_session, "layout-add-mod@example.com", "password123")
    token = create_access_token(str(user.id))
    
    # Create initial layout
    await client.put(
        "/api/dashboard/layout",
        json={"positions": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Act: Add module
    response = await client.post(
        "/api/dashboard/modules/new-module-id",
        json={"x": 0, "y": 0, "w": 6, "h": 2},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["positions"]) == 1
    assert data["positions"][0]["module_id"] == "new-module-id"


@pytest.mark.asyncio
async def test_remove_module_from_layout(client, db_session):
    """Remove module from layout."""
    # Arrange
    user = await create_user(db_session, "layout-remove@example.com", "password123")
    token = create_access_token(str(user.id))
    
    # Create layout with module
    await client.put(
        "/api/dashboard/layout",
        json={
            "positions": [
                {"module_id": "to-remove", "x": 0, "y": 0, "w": 6, "h": 2}
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Act: Remove module
    response = await client.delete(
        "/api/dashboard/modules/to-remove",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["positions"]) == 0


@pytest.mark.asyncio
async def test_remove_nonexistent_module_from_layout(client, db_session):
    """Flow 7: Remove module not in layout returns 404."""
    # Arrange
    user = await create_user(db_session, "layout-remove404@example.com", "password123")
    token = create_access_token(str(user.id))
    
    # Create empty layout
    await client.get("/api/dashboard/layout", headers={"Authorization": f"Bearer {token}"})
    
    # Act
    response = await client.delete(
        "/api/dashboard/modules/does-not-exist",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_layout_isolation_between_users(client, db_session):
    """Users have separate layouts."""
    # Arrange
    user1 = await create_user(db_session, "layout-u1@example.com", "password123")
    user2 = await create_user(db_session, "layout-u2@example.com", "password123")
    token1 = create_access_token(str(user1.id))
    token2 = create_access_token(str(user2.id))
    
    # User 1 sets custom layout
    await client.put(
        "/api/dashboard/layout",
        json={"columns": 24, "row_height": 50},
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    # Act: User 2 gets their layout
    response = await client.get(
        "/api/dashboard/layout",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    # Assert: User 2 has default layout, not User 1's
    assert response.status_code == 200
    data = response.json()
    assert data["columns"] == 12  # Default, not 24
    assert data["row_height"] == 100  # Default, not 50
