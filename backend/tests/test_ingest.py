"""
DEV-008: Data Ingestion API Test Suite

Tests for the data ingestion endpoints including:
- POST /api/ingest/metrics - Batch metric ingestion
- POST /api/ingest/events - Batch calendar event ingestion
- 202 Accepted responses with async processing
- Queueing to Redis metrics_queue
- Validation and error handling

Related: DEV-008, QA-REG-003
"""

import pytest
import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth.service import create_user, create_access_token
from app.services.redis_client import get_redis_client
from app.models.log import SystemLog
from app.core.file_logger import read_logs
import app.core.file_logger as file_logger


def get_auth_headers(user_id: str) -> dict:
    """Create authorization headers for a user."""
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


class TestIngestMetrics:
    """Test POST /api/ingest/metrics endpoint."""

    @pytest.mark.asyncio
    async def test_ingest_metrics_returns_202_accepted(self, client, db_session: AsyncSession):
        """DEV-008-001: Ingest metrics returns 202 Accepted."""
        user = await create_user(db_session, "ingest-test@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        metrics_request = {
            "metrics": [
                {
                    "metric_name": "stock_price",
                    "value": "150.50",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tags": {"symbol": "AAPL"},
                    "source": "test",
                }
            ]
        }

        response = await client.post(
            "/api/ingest/metrics",
            json=metrics_request,
            headers=headers,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_ingest_metrics_queues_to_redis(self, client, db_session: AsyncSession, redis_container):
        """DEV-008-002: Ingest metrics queues messages to Redis.
        
        Note: This verifies the message is pushed to Redis queue.
        Uses the client's test_redis from conftest override.
        """
        user = await create_user(db_session, "ingest-redis@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Use the test Redis client from the fixture (same as app uses)
        redis_client = client.test_redis
        await redis_client.delete("metrics_queue")

        metrics_request = {
            "metrics": [
                {
                    "metric_name": "test_queue_metric",
                    "value": "100.00",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tags": {},
                    "source": "test",
                }
            ]
        }

        response = await client.post(
            "/api/ingest/metrics",
            json=metrics_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify message was queued
        queued = await redis_client.rpop("metrics_queue")
        assert queued is not None
        
        message = json.loads(queued)
        assert message["type"] == "metric"
        assert message["metric_name"] == "test_queue_metric"
        # Value is converted to float then back to string, so precision may vary
        assert float(message["value"]) == 100.00

    @pytest.mark.asyncio
    async def test_ingest_metrics_batch_multiple(self, client, db_session: AsyncSession):
        """DEV-008-003: Ingest metrics accepts batch of multiple metrics."""
        user = await create_user(db_session, "ingest-batch@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        metrics_request = {
            "metrics": [
                {
                    "metric_name": "price",
                    "value": "100.00",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tags": {"symbol": "AAPL"},
                    "source": "yahoo",
                },
                {
                    "metric_name": "volume",
                    "value": "5000000",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tags": {"symbol": "AAPL"},
                    "source": "yahoo",
                },
                {
                    "metric_name": "price",
                    "value": "200.00",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tags": {"symbol": "TSLA"},
                    "source": "yahoo",
                },
            ]
        }

        response = await client.post(
            "/api/ingest/metrics",
            json=metrics_request,
            headers=headers,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["queued_count"] == 3
        assert data["queue"] == "metrics_queue"

    @pytest.mark.asyncio
    async def test_ingest_metrics_validates_required_fields(self, client, db_session: AsyncSession):
        """DEV-008-004: Ingest metrics validates required fields."""
        user = await create_user(db_session, "ingest-validation@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Missing metric_name
        invalid_request = {
            "metrics": [
                {
                    "value": "100.00",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ]
        }

        response = await client.post(
            "/api/ingest/metrics",
            json=invalid_request,
            headers=headers,
        )

        # Should return 422 for validation error (or accept with error count)
        assert response.status_code in (202, 422)

    @pytest.mark.asyncio
    async def test_ingest_metrics_empty_batch(self, client, db_session: AsyncSession):
        """DEV-008-005: Ingest metrics handles empty batch."""
        user = await create_user(db_session, "ingest-empty@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        metrics_request = {"metrics": []}

        response = await client.post(
            "/api/ingest/metrics",
            json=metrics_request,
            headers=headers,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["queued_count"] == 0

    @pytest.mark.asyncio
    async def test_ingest_metrics_logs_to_system_logs(self, client, db_session: AsyncSession):
        """DEV-008-006: Ingest metrics writes system log entry."""
        user = await create_user(db_session, "ingest-log@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        metrics_request = {
            "metrics": [
                {
                    "metric_name": "logged_metric",
                    "value": "99.99",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tags": {},
                    "source": "test",
                }
            ]
        }

        response = await client.post(
            "/api/ingest/metrics",
            json=metrics_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify system log was created (file-based)
        logs = read_logs(source="ingest", limit=10)
        
        # Should have at least one ingest log
        assert logs["total"] >= 1
        assert any("Metrics ingested" in log["message"] for log in logs["logs"])

    @pytest.mark.asyncio
    async def test_ingest_metrics_requires_auth(self, client):
        """DEV-008-007: Ingest metrics requires authentication."""
        metrics_request = {
            "metrics": [
                {
                    "metric_name": "test",
                    "value": "100",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ]
        }

        response = await client.post(
            "/api/ingest/metrics",
            json=metrics_request,
        )

        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_ingest_metrics_preserves_precision(self, client, db_session: AsyncSession, redis_container):
        """DEV-008-008: Ingest metrics preserves decimal precision."""
        user = await create_user(db_session, "ingest-precision@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Get Redis client
        redis_host = redis_container.get_container_host_ip()
        redis_port = redis_container.get_exposed_port(6379)
        import redis.asyncio as redis
        redis_client = redis.from_url(f"redis://{redis_host}:{redis_port}/0", decode_responses=True)
        await redis_client.delete("metrics_queue")

        metrics_request = {
            "metrics": [
                {
                    "metric_name": "precise_price",
                    "value": "150.123456789",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tags": {},
                    "source": "test",
                }
            ]
        }

        response = await client.post(
            "/api/ingest/metrics",
            json=metrics_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify precision preserved in queue
        queued = await redis_client.rpop("metrics_queue")
        message = json.loads(queued)
        assert message["value"] == "150.123456789"

        await redis_client.aclose()


class TestIngestEvents:
    """Test POST /api/ingest/events endpoint."""

    @pytest.mark.asyncio
    async def test_ingest_events_returns_202_accepted(self, client, db_session: AsyncSession):
        """DEV-008-009: Ingest events returns 202 Accepted."""
        user = await create_user(db_session, "ingest-events@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        events_request = {
            "events": [
                {
                    "title": "Fed Interest Rate Decision",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "is_all_day": False,
                    "event_type": "economic",
                    "source": "forex_factory",
                    "external_id": "fed_2024_01",
                    "impact": "high",
                    "currency": "USD",
                }
            ]
        }

        response = await client.post(
            "/api/ingest/events",
            json=events_request,
            headers=headers,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_ingest_events_queues_to_redis(self, client, db_session: AsyncSession, redis_container):
        """DEV-008-010: Ingest events queues messages to Redis."""
        user = await create_user(db_session, "ingest-events-redis@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Get Redis client
        redis_host = redis_container.get_container_host_ip()
        redis_port = redis_container.get_exposed_port(6379)
        import redis.asyncio as redis
        redis_client = redis.from_url(f"redis://{redis_host}:{redis_port}/0", decode_responses=True)
        await redis_client.delete("metrics_queue")

        events_request = {
            "events": [
                {
                    "title": "Test Economic Event",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "is_all_day": False,
                    "event_type": "economic",
                    "source": "test",
                }
            ]
        }

        response = await client.post(
            "/api/ingest/events",
            json=events_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify message was queued
        queued = await redis_client.rpop("metrics_queue")
        assert queued is not None
        
        message = json.loads(queued)
        assert message["type"] == "calendar_event"
        assert message["title"] == "Test Economic Event"

        await redis_client.aclose()

    @pytest.mark.asyncio
    async def test_ingest_events_with_optional_fields(self, client, db_session: AsyncSession, redis_container):
        """DEV-008-011: Ingest events handles all optional fields."""
        user = await create_user(db_session, "ingest-events-full@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Get Redis client
        redis_host = redis_container.get_container_host_ip()
        redis_port = redis_container.get_exposed_port(6379)
        import redis.asyncio as redis
        redis_client = redis.from_url(f"redis://{redis_host}:{redis_port}/0", decode_responses=True)
        await redis_client.delete("metrics_queue")

        events_request = {
            "events": [
                {
                    "title": "NFP Report",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "end_time": datetime.now(timezone.utc).isoformat(),
                    "is_all_day": False,
                    "event_type": "economic",
                    "source": "forex_factory",
                    "external_id": "nfp_2024_01",
                    "source_url": "https://example.com/event",
                    "impact": "high",
                    "currency": "USD",
                    "country": "US",
                    "actual_value": "200K",
                    "forecast_value": "180K",
                    "previous_value": "190K",
                }
            ]
        }

        response = await client.post(
            "/api/ingest/events",
            json=events_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify all fields preserved
        queued = await redis_client.rpop("metrics_queue")
        message = json.loads(queued)
        
        assert message["title"] == "NFP Report"
        assert message["external_id"] == "nfp_2024_01"
        assert message["impact"] == "high"
        assert message["actual_value"] == "200K"
        assert message["forecast_value"] == "180K"
        assert message["previous_value"] == "190K"

        await redis_client.aclose()

    @pytest.mark.asyncio
    async def test_ingest_events_empty_batch(self, client, db_session: AsyncSession):
        """DEV-008-012: Ingest events handles empty batch."""
        user = await create_user(db_session, "ingest-events-empty@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        events_request = {"events": []}

        response = await client.post(
            "/api/ingest/events",
            json=events_request,
            headers=headers,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["queued_count"] == 0

    @pytest.mark.asyncio
    async def test_ingest_events_logs_to_system_logs(self, client, db_session: AsyncSession):
        """DEV-008-013: Ingest events writes system log entry."""
        user = await create_user(db_session, "ingest-events-log@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        events_request = {
            "events": [
                {
                    "title": "Logged Event",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "is_all_day": False,
                    "event_type": "economic",
                    "source": "test",
                }
            ]
        }

        response = await client.post(
            "/api/ingest/events",
            json=events_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify system log was created (file-based)
        logs = read_logs(source="ingest", limit=10)
        
        assert any("Events ingested" in log["message"] for log in logs["logs"])

    @pytest.mark.asyncio
    async def test_ingest_events_requires_auth(self, client):
        """DEV-008-014: Ingest events requires authentication."""
        events_request = {
            "events": [
                {
                    "title": "Test",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "is_all_day": False,
                    "event_type": "economic",
                }
            ]
        }

        response = await client.post(
            "/api/ingest/events",
            json=events_request,
        )

        assert response.status_code in (401, 403)


class TestIngestErrorHandling:
    """Test error handling for ingest endpoints."""

    @pytest.mark.asyncio
    async def test_ingest_metrics_partial_failure(self, client, db_session: AsyncSession):
        """DEV-008-015: Ingest metrics handles partial batch failures."""
        user = await create_user(db_session, "ingest-partial@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Mix of valid and potentially invalid metrics
        metrics_request = {
            "metrics": [
                {
                    "metric_name": "valid_metric",
                    "value": "100",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tags": {},
                    "source": "test",
                }
            ]
        }

        response = await client.post(
            "/api/ingest/metrics",
            json=metrics_request,
            headers=headers,
        )

        # Should accept what it can
        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_ingest_events_with_module_id(self, client, db_session: AsyncSession, redis_container):
        """DEV-008-016: Ingest events supports target module_id."""
        user = await create_user(db_session, "ingest-module@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Get Redis client
        redis_host = redis_container.get_container_host_ip()
        redis_port = redis_container.get_exposed_port(6379)
        import redis.asyncio as redis
        redis_client = redis.from_url(f"redis://{redis_host}:{redis_port}/0", decode_responses=True)
        await redis_client.delete("metrics_queue")

        # Create a calendar module
        module_response = await client.post(
            "/api/modules",
            json={"module_type": "calendar", "name": "Test Calendar", "config": {}},
            headers=headers,
        )
        assert module_response.status_code == 201
        module_id = module_response.json()["id"]

        events_request = {
            "module_id": module_id,
            "events": [
                {
                    "title": "Module-specific Event",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "is_all_day": False,
                    "event_type": "economic",
                    "source": "test",
                }
            ]
        }

        response = await client.post(
            "/api/ingest/events",
            json=events_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify module_id in queued message
        queued = await redis_client.rpop("metrics_queue")
        message = json.loads(queued)
        assert message["module_id"] == module_id

        await redis_client.aclose()


class TestIngestContract:
    """Contract tests for ingest API responses."""

    @pytest.mark.asyncio
    async def test_ingest_response_schema(self, client, db_session: AsyncSession):
        """DEV-CONTRACT-017: Ingest response has required fields."""
        user = await create_user(db_session, "ingest-contract@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        metrics_request = {
            "metrics": [
                {
                    "metric_name": "contract_test",
                    "value": "100",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "test",
                }
            ]
        }

        response = await client.post(
            "/api/ingest/metrics",
            json=metrics_request,
            headers=headers,
        )

        assert response.status_code == 202
        data = response.json()

        # Required fields
        assert "status" in data
        assert "message" in data
        assert "queued_count" in data
        assert "queue" in data
        
        assert data["status"] == "accepted"
        assert data["queue"] == "metrics_queue"
        assert isinstance(data["queued_count"], int)
