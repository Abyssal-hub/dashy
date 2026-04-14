import pytest
from httpx import AsyncClient

from app.services.auth.service import (
    get_password_hash,
    verify_password,
    create_access_token,
    hash_token,
    create_user,
    authenticate_user,
)
from app.schemas.auth import LoginRequest


# --- Unit tests for auth service functions ---

def test_password_hashing():
    password = "testpassword123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    import uuid
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id)
    assert isinstance(token, str)
    assert len(token) > 0


def test_hash_token():
    token = "mysecrettoken"
    hashed = hash_token(token)
    assert isinstance(hashed, str)
    assert len(hashed) == 64  # SHA-256 hex length


# --- Integration tests for auth endpoints with real database ---

@pytest.mark.asyncio
async def test_login_success(client, db_session):
    """Test successful login returns tokens."""
    # Create a user directly in DB
    user = await create_user(db_session, "test@example.com", "password123")
    
    response = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client, db_session):
    """Test login with invalid credentials returns 401."""
    # Create user first
    await create_user(db_session, "test2@example.com", "password123")
    
    response = await client.post("/auth/login", json={
        "email": "test2@example.com",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Test login with non-existent user returns 401."""
    response = await client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "password123"
    })
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_success(client, db_session):
    """Test refresh endpoint with valid token returns new tokens."""
    from app.services.auth.service import create_refresh_token
    
    # Create user and get refresh token
    user = await create_user(db_session, "test3@example.com", "password123")
    refresh_token_str, _ = await create_refresh_token(db_session, str(user.id))
    
    response = await client.post("/auth/refresh", json={
        "refresh_token": refresh_token_str
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(client):
    """Test refresh with invalid token returns 401."""
    response = await client.post("/auth/refresh", json={
        "refresh_token": "invalid_token"
    })
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_reuse(client, db_session):
    """Test that refresh token rotation prevents reuse."""
    from app.services.auth.service import create_refresh_token
    
    # Create user and get refresh token
    user = await create_user(db_session, "test4@example.com", "password123")
    refresh_token_str, _ = await create_refresh_token(db_session, str(user.id))
    
    # Use refresh token once
    response1 = await client.post("/auth/refresh", json={
        "refresh_token": refresh_token_str
    })
    assert response1.status_code == 200
    
    # Try to reuse the same refresh token - should fail
    response2 = await client.post("/auth/refresh", json={
        "refresh_token": refresh_token_str
    })
    assert response2.status_code == 401


@pytest.mark.asyncio
async def test_logout_success(client, db_session):
    """Test logout with valid access token succeeds."""
    from app.services.auth.service import create_refresh_token
    
    # Create user
    user = await create_user(db_session, "test5@example.com", "password123")
    access_token = create_access_token(str(user.id))
    refresh_token_str, _ = await create_refresh_token(db_session, str(user.id))
    
    response = await client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token_str},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 204
    
    # Verify refresh token is revoked
    response2 = await client.post("/auth/refresh", json={
        "refresh_token": refresh_token_str
    })
    assert response2.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    """Test protected endpoint rejects unauthenticated requests."""
    response = await client.get("/protected/me")
    assert response.status_code == 403 or response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token(client, db_session):
    """Test protected endpoint accepts valid access token."""
    import uuid
    
    # Create user
    user = await create_user(db_session, "test6@example.com", "password123")
    access_token = create_access_token(str(user.id))
    
    response = await client.get(
        "/protected/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(user.id)


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(client):
    """Test protected endpoint rejects invalid token."""
    response = await client.get(
        "/protected/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401 or response.status_code == 403
