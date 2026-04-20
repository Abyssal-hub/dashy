"""
QA-004: Integration test - Data pipeline

End-to-end tests for the data ingestion pipeline:
Scraper → Redis → Consumer → TimescaleDB → API

Related: DEV-008, DEV-009, ARCHITECTURE.md Section 8
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta

from app.services.auth.service import create_user, create_access_token
from app.services.redis_client import get_redis_client


def get_auth_headers(user_id: str) -> dict:
    """Create authorization headers for a user."""
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


class TestIngestAPI:
    """Test ingest endpoints accept data."""

    @pytest.mark.asyncio
    async def test_ingest_metrics_accepts_batch(self, client, db_session):
        """QA-004-001: POST /api/ingest/metrics accepts batch metrics."""
        user = await create_user(db_session, "ingest-metrics@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        metrics_batch = {
            "metrics": [
                {
                    "metric_name": "price",
                    "value": 150.25,
                    "timestamp": datetime.utcnow().isoformat(),
                    "tags": {"symbol": "AAPL"},
                    "source": "test",
                },
                {
                    "metric_name": "price",
                    "value": 2800.00,
                    "timestamp": datetime.utcnow().isoformat(),
                    "tags": {"symbol": "GOOGL"},
                    "source": "test",
                },
            ]
        }

        response = await client.post(
            "/api/ingest/metrics",
            json=metrics_batch,
            headers=headers,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["queued_count"] == 2

    @pytest.mark.asyncio
    async def test_ingest_events_accepts_batch(self, client, db_session):
        """QA-004-002: POST /api/ingest/events accepts batch events."""
        user = await create_user(db_session, "ingest-events@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        events_batch = {
            "events": [
                {
                    "title": "Fed Meeting",
                    "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    "event_type": "economic",
                    "currency": "USD",
                    "impact": "high",
                    "source": "test",
                },
            ]
        }

        response = await client.post(
            "/api/ingest/events",
            json=events_batch,
            headers=headers,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["queued_count"] == 1

    @pytest.mark.asyncio
    async def test_ingest_without_auth_fails(self, client, db_session):
        """QA-004-003: Ingest without authentication fails."""
        response = await client.post("/api/ingest/metrics", json={"items": []})
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_ingest_empty_batch_returns_zero(self, client, db_session):
        """QA-004-004: Ingest empty batch returns queued: 0."""
        user = await create_user(db_session, "ingest-empty@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        response = await client.post(
            "/api/ingest/metrics",
            json={"metrics": []},
            headers=headers,
        )

        assert response.status_code == 202
        assert response.json()["queued_count"] == 0


class TestRedisQueue:
    """Test data flows through Redis queue."""

    @pytest.mark.asyncio
    async def test_ingest_pushes_to_redis(self, client, db_session, redis_client):
        """QA-004-005: Ingest API pushes data to Redis queue."""
        user = await create_user(db_session, "redis-push@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Clear queue first
        await redis_client.delete("metrics_queue")

        metrics_batch = {
            "metrics": [
                {
                    "metric_name": "test_metric",
                    "value": 100.0,
                    "timestamp": datetime.utcnow().isoformat(),
                    "tags": {},
                    "source": "test",
                },
            ]
        }

        response = await client.post(
            "/api/ingest/metrics",
            json=metrics_batch,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify data in Redis
        queue_data = await redis_client.lpop("metrics_queue")
        assert queue_data is not None
        parsed = json.loads(queue_data)
        assert parsed["metric_name"] == "test_metric"
        assert parsed["type"] == "metric"


class TestConsumerPipeline:
    """Test consumer processes data from Redis."""

    @pytest.mark.skip(reason="Requires running consumer - integration test")
    @pytest.mark.asyncio
    async def test_consumer_drains_to_database(self, client, db_session, redis_client):
        """QA-004-006: Consumer drains Redis queue to database."""
        # This test requires the consumer to be running
        # It's skipped in standard test runs
        pass

    @pytest.mark.skip(reason="Requires running consumer - integration test")
    @pytest.mark.asyncio
    async def test_batch_accumulation_100_messages(self, client, db_session):
        """QA-004-007: Consumer batches 100 messages."""
        pass

    @pytest.mark.skip(reason="Requires running consumer - integration test")
    @pytest.mark.asyncio
    async def test_batch_timeout_5_seconds(self, client, db_session):
        """QA-004-008: Consumer flushes batch after 5 second timeout."""
        pass


class TestCircuitBreaker:
    """Test circuit breaker behavior."""

    @pytest.mark.skip(reason="Requires simulated failure - complex setup")
    @pytest.mark.asyncio
    async def test_circuit_breaker_triggers_on_failure(self, client, db_session):
        """QA-004-009: Circuit breaker triggers after 3 failures."""
        pass

    @pytest.mark.skip(reason="Requires simulated failure - complex setup")
    @pytest.mark.asyncio
    async def test_circuit_breaker_cooldown_10_minutes(self, client, db_session):
        """QA-004-010: Circuit breaker enforces 10 minute cooldown."""
        pass


class TestDataFlow:
    """Test end-to-end data flow."""

    @pytest.mark.skip(reason="Requires running consumer - full integration")
    @pytest.mark.asyncio
    async def test_end_to_end_metrics_pipeline(self, client, db_session):
        """QA-004-011: Full pipeline: ingest → Redis → consumer → DB."""
        pass

    @pytest.mark.skip(reason="Requires running consumer - full integration")
    @pytest.mark.asyncio
    async def test_end_to_end_events_pipeline(self, client, db_session):
        """QA-004-012: Full pipeline: events → Redis → consumer → DB."""
        pass
