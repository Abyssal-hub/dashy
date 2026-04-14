import pytest


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client):
    """Test health endpoint returns 200 with valid structure."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert data["database"] in ["healthy", "unhealthy"]
    assert data["redis"] in ["healthy", "unhealthy"]
    assert data["status"] in ["healthy", "degraded"]
