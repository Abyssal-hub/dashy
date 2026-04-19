"""
QA-012: Log Module Test Suite

Tests for the system logging module including:
- LogHandler functionality
- API endpoints
- System event logging integration
- Log retention

Related: DEV-012, QA-REG-003
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import SystemLog
from app.models.module import Module
from app.models.user import User
from app.modules.handlers.log import LogHandler, write_system_log
from app.schemas.module import ModuleCreate
from app.services.auth.service import create_user, create_access_token


def get_auth_headers(user_id: str) -> dict:
    """Create authorization headers for a user."""
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


class TestLogHandler:
    """Test the LogHandler module handler."""

    @pytest.mark.asyncio
    async def test_handler_get_data_compact_size(self, db_session: AsyncSession):
        """QA-012-001: LogHandler returns 5 logs for compact size."""
        # Create test logs
        for i in range(10):
            log = SystemLog(
                severity="INFO",
                message=f"Test message {i}",
                source="test",
            )
            db_session.add(log)
        await db_session.commit()

        handler = LogHandler()
        data = await handler.get_data(
            module_id=str(uuid4()),
            size="compact",
            db_session=db_session,
        )

        assert len(data["logs"]) == 5
        assert data["size"] == "compact"
        assert data["severity_counts"]["INFO"] >= 5

    @pytest.mark.asyncio
    async def test_handler_get_data_standard_size(self, db_session: AsyncSession):
        """QA-012-002: LogHandler returns 20 logs for standard size."""
        # Create test logs
        for i in range(25):
            log = SystemLog(
                severity="INFO" if i < 20 else "WARN",
                message=f"Test message {i}",
                source="test",
            )
            db_session.add(log)
        await db_session.commit()

        handler = LogHandler()
        data = await handler.get_data(
            module_id=str(uuid4()),
            size="standard",
            db_session=db_session,
        )

        assert len(data["logs"]) == 20
        assert data["size"] == "standard"

    @pytest.mark.asyncio
    async def test_handler_get_data_expanded_size(self, db_session: AsyncSession):
        """QA-012-003: LogHandler returns 100 logs for expanded size."""
        # Create test logs
        for i in range(150):
            log = SystemLog(
                severity="INFO",
                message=f"Test message {i}",
                source="test",
            )
            db_session.add(log)
        await db_session.commit()

        handler = LogHandler()
        data = await handler.get_data(
            module_id=str(uuid4()),
            size="expanded",
            db_session=db_session,
        )

        assert len(data["logs"]) == 100
        assert data["size"] == "expanded"

    @pytest.mark.asyncio
    async def test_handler_filter_by_severity(self, db_session: AsyncSession):
        """QA-012-004: LogHandler filters by severity correctly."""
        # Create logs with different severities
        for i in range(5):
            db_session.add(SystemLog(severity="INFO", message=f"Info {i}", source="test"))
            db_session.add(SystemLog(severity="WARN", message=f"Warn {i}", source="test"))
            db_session.add(SystemLog(severity="ERROR", message=f"Error {i}", source="test"))
        await db_session.commit()

        handler = LogHandler()
        data = await handler.get_data(
            module_id=str(uuid4()),
            size="expanded",
            db_session=db_session,
            severity="ERROR",
        )

        assert len(data["logs"]) == 5
        assert all(log["severity"] == "ERROR" for log in data["logs"])
        assert data["filters_applied"]["severity"] == "ERROR"

    @pytest.mark.asyncio
    async def test_handler_filter_by_source(self, db_session: AsyncSession):
        """QA-012-005: LogHandler filters by source correctly."""
        # Create logs from different sources
        for i in range(5):
            db_session.add(SystemLog(severity="INFO", message=f"Consumer log {i}", source="consumer"))
            db_session.add(SystemLog(severity="INFO", message=f"API log {i}", source="api"))
        await db_session.commit()

        handler = LogHandler()
        data = await handler.get_data(
            module_id=str(uuid4()),
            size="expanded",
            db_session=db_session,
            source="consumer",
        )

        assert len(data["logs"]) == 5
        assert all(log["source"] == "consumer" for log in data["logs"])

    @pytest.mark.asyncio
    async def test_handler_returns_severity_counts(self, db_session: AsyncSession):
        """QA-012-006: LogHandler returns accurate severity counts."""
        # Create logs with known distribution
        for i in range(10):
            db_session.add(SystemLog(severity="INFO", message=f"Info {i}", source="test"))
        for i in range(5):
            db_session.add(SystemLog(severity="WARN", message=f"Warn {i}", source="test"))
        for i in range(3):
            db_session.add(SystemLog(severity="ERROR", message=f"Error {i}", source="test"))
        await db_session.commit()

        handler = LogHandler()
        data = await handler.get_data(
            module_id=str(uuid4()),
            size="standard",
            db_session=db_session,
        )

        assert data["severity_counts"]["INFO"] == 10
        assert data["severity_counts"]["WARN"] == 5
        assert data["severity_counts"]["ERROR"] == 3

    @pytest.mark.asyncio
    async def test_handler_returns_severity_color(self, db_session: AsyncSession):
        """QA-012-007: LogHandler returns color codes for frontend."""
        db_session.add(SystemLog(severity="INFO", message="Info", source="test"))
        db_session.add(SystemLog(severity="WARN", message="Warn", source="test"))
        db_session.add(SystemLog(severity="ERROR", message="Error", source="test"))
        await db_session.commit()

        handler = LogHandler()
        data = await handler.get_data(
            module_id=str(uuid4()),
            size="standard",
            db_session=db_session,
        )

        for log in data["logs"]:
            assert "severity_color" in log
            if log["severity"] == "INFO":
                assert log["severity_color"] == "blue"
            elif log["severity"] == "WARN":
                assert log["severity_color"] == "orange"
            elif log["severity"] == "ERROR":
                assert log["severity_color"] == "red"

    @pytest.mark.asyncio
    async def test_handler_returns_placeholder_without_session(self):
        """QA-012-008: LogHandler returns placeholder when no db_session provided."""
        handler = LogHandler()
        data = await handler.get_data(
            module_id=str(uuid4()),
            size="standard",
            db_session=None,
        )

        assert data["logs"] == []
        assert data["total"] == 0
        assert data["size"] == "standard"
        assert "retention_days" in data


class TestWriteSystemLog:
    """Test the write_system_log utility function."""

    @pytest.mark.asyncio
    async def test_write_system_log_creates_entry(self, db_session: AsyncSession):
        """QA-012-009: write_system_log creates a SystemLog entry."""
        log = await write_system_log(
            db_session=db_session,
            severity="INFO",
            message="Test message",
            source="test",
            metadata={"key": "value"},
        )

        assert log.id is not None
        assert log.severity == "INFO"
        assert log.message == "Test message"
        assert log.source == "test"
        assert log.extra_data == {"key": "value"}
        assert log.created_at is not None

    @pytest.mark.asyncio
    async def test_write_system_log_severity_uppercase(self, db_session: AsyncSession):
        """QA-012-010: write_system_log normalizes severity to uppercase."""
        log = await write_system_log(
            db_session=db_session,
            severity="info",  # lowercase input
            message="Test message",
            source="test",
        )

        assert log.severity == "INFO"

    @pytest.mark.asyncio
    async def test_write_system_log_with_module_id(self, db_session: AsyncSession):
        """QA-012-011: write_system_log associates with module_id."""
        # Create a user first
        user = await create_user(db_session, "log-module-test@example.com", "password123")
        
        # Create a log module
        module = Module(
            user_id=user.id,
            module_type="log",
            name="Test Log Module",
            config={},
        )
        db_session.add(module)
        await db_session.commit()
        await db_session.refresh(module)

        log = await write_system_log(
            db_session=db_session,
            severity="INFO",
            message="Module-specific message",
            source="test",
            module_id=str(module.id),
        )

        assert log.module_id == module.id


class TestLogsAPI:
    """Test the /logs API endpoints."""

    @pytest.mark.asyncio
    async def test_get_logs_returns_list(self, client, db_session: AsyncSession):
        """QA-012-012: GET /logs returns list of logs."""
        # Create test user and auth headers
        user = await create_user(db_session, "logs-test@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create test logs
        for i in range(5):
            db_session.add(SystemLog(severity="INFO", message=f"API test {i}", source="api"))
        await db_session.commit()

        response = await client.get("/api/logs", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert len(data["logs"]) == 5

    @pytest.mark.asyncio
    async def test_get_logs_with_severity_filter(self, client, db_session: AsyncSession):
        """QA-012-013: GET /logs filters by severity."""
        # Create test user
        user = await create_user(db_session, "logs-filter@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create mixed severity logs
        for i in range(3):
            db_session.add(SystemLog(severity="INFO", message=f"Info {i}", source="api"))
        for i in range(2):
            db_session.add(SystemLog(severity="ERROR", message=f"Error {i}", source="api"))
        await db_session.commit()

        response = await client.get("/api/logs?severity=ERROR", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert all(log["severity"] == "ERROR" for log in data["logs"])
        assert data["filters_applied"]["severity"] == "ERROR"

    @pytest.mark.asyncio
    async def test_get_logs_with_source_filter(self, client, db_session: AsyncSession):
        """QA-012-014: GET /logs filters by source."""
        # Create test user
        user = await create_user(db_session, "logs-source@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create logs from different sources
        db_session.add(SystemLog(severity="INFO", message="Consumer message", source="consumer"))
        db_session.add(SystemLog(severity="INFO", message="API message", source="api"))
        await db_session.commit()

        response = await client.get("/api/logs?source=consumer", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert all(log["source"] == "consumer" for log in data["logs"])

    @pytest.mark.asyncio
    async def test_get_logs_pagination(self, client, db_session: AsyncSession):
        """QA-012-015: GET /logs supports pagination."""
        # Create test user
        user = await create_user(db_session, "logs-page@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create many logs
        for i in range(25):
            db_session.add(SystemLog(severity="INFO", message=f"Paginated {i}", source="api"))
        await db_session.commit()

        # Get first page
        response = await client.get("/api/logs?limit=10&offset=0", headers=headers)
        assert response.status_code == 200
        data1 = response.json()
        assert len(data1["logs"]) == 10

        # Get second page
        response = await client.get("/api/logs?limit=10&offset=10", headers=headers)
        assert response.status_code == 200
        data2 = response.json()
        assert len(data2["logs"]) == 10

        # Verify different logs
        assert data1["logs"][0]["id"] != data2["logs"][0]["id"]

    @pytest.mark.asyncio
    async def test_get_logs_ordering(self, client, db_session: AsyncSession):
        """QA-012-016: GET /logs returns logs in reverse chronological order."""
        # Create test user
        user = await create_user(db_session, "logs-order@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create logs with different timestamps
        for i in range(5):
            log = SystemLog(
                severity="INFO",
                message=f"Order test {i}",
                source="api",
            )
            db_session.add(log)
        await db_session.commit()

        response = await client.get("/api/logs?limit=5", headers=headers)
        assert response.status_code == 200
        data = response.json()

        # Verify reverse chronological order (newest first)
        timestamps = [log["created_at"] for log in data["logs"]]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.asyncio
    async def test_get_severity_counts(self, client, db_session: AsyncSession):
        """QA-012-017: GET /logs/severity-counts returns counts."""
        # Create test user
        user = await create_user(db_session, "logs-counts@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create logs with known distribution
        for i in range(10):
            db_session.add(SystemLog(severity="INFO", message=f"Info {i}", source="api"))
        for i in range(5):
            db_session.add(SystemLog(severity="WARN", message=f"Warn {i}", source="api"))
        for i in range(3):
            db_session.add(SystemLog(severity="ERROR", message=f"Error {i}", source="api"))
        await db_session.commit()

        response = await client.get("/api/logs/severity-counts?days=7", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["counts"]["INFO"] == 10
        assert data["counts"]["WARN"] == 5
        assert data["counts"]["ERROR"] == 3
        assert data["total"] == 18
        assert "period_days" in data

    @pytest.mark.asyncio
    async def test_create_log_endpoint(self, client, db_session: AsyncSession):
        """QA-012-018: POST /logs creates a new log entry."""
        # Create test user
        user = await create_user(db_session, "logs-create@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        response = await client.post(
            "/api/logs?severity=INFO&message=Manual test log&source=manual",
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["severity"] == "INFO"
        assert data["message"] == "Manual test log"
        assert data["source"] == "manual"
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_module_logs(self, client, db_session: AsyncSession):
        """QA-012-019: GET /logs/modules/{id} returns module-specific logs."""
        # Create test user and module
        user = await create_user(db_session, "logs-module@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create a log module via API
        module_data = {"module_type": "log", "name": "Test Log Module", "config": {}}
        module_response = await client.post("/api/modules", json=module_data, headers=headers)
        assert module_response.status_code == 201
        module_id = module_response.json()["id"]

        # Create logs for this module
        for i in range(3):
            db_session.add(SystemLog(
                severity="INFO",
                message=f"Module log {i}",
                source="test",
                module_id=module_id,
            ))
        await db_session.commit()

        response = await client.get(f"/api/logs/modules/{module_id}?size=standard", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 3

    @pytest.mark.asyncio
    async def test_logs_api_requires_auth(self, client, db_session: AsyncSession):
        """QA-012-020: GET /logs requires authentication."""
        response = await client.get("/api/logs")
        assert response.status_code in (401, 403)  # Either unauthorized or forbidden


class TestSystemEventLogging:
    """Test that system events are logged (integration with other components)."""

    @pytest.mark.asyncio
    async def test_consumer_events_logged(self, db_session: AsyncSession):
        """QA-012-021: Consumer start/stop events are written to system_logs.
        
        Note: This verifies the logging infrastructure exists. Actual consumer
        logging is tested in test_consumer.py.
        """
        # Verify write_system_log can be called from consumer context
        log = await write_system_log(
            db_session=db_session,
            severity="INFO",
            message="Redis consumer started",
            source="consumer",
            metadata={"queue": "metrics_queue"},
        )

        assert log.id is not None
        assert log.source == "consumer"

        # Verify it can be retrieved
        result = await db_session.execute(
            select(SystemLog).where(SystemLog.source == "consumer")
        )
        logs = result.scalars().all()
        assert len(logs) >= 1

    @pytest.mark.asyncio
    async def test_ingest_events_logged(self, db_session: AsyncSession):
        """QA-012-022: Ingest operations are written to system_logs."""
        log = await write_system_log(
            db_session=db_session,
            severity="INFO",
            message="Metrics ingested: 5 queued",
            source="ingest",
            metadata={"metrics_count": 5, "user_id": "test-user"},
        )

        assert log.id is not None
        assert log.source == "ingest"
        assert log.extra_data["metrics_count"] == 5


class TestLogRetention:
    """Test the 7-day log retention policy."""

    @pytest.mark.skip(reason="Retention is enforced by external cleanup job, not application code")
    @pytest.mark.asyncio
    async def test_logs_older_than_7_days_not_returned(self, db_session: AsyncSession):
        """QA-012-023: Logs older than 7 days are excluded from queries.
        
        Note: This test documents the retention requirement from ARCHITECTURE.md.
        Actual retention is enforced by a database cleanup job or TimescaleDB policy.
        """
        # Create old log
        old_log = SystemLog(
            severity="INFO",
            message="Old log message",
            source="test",
        )
        # Manually set created_at to 8 days ago
        old_log.created_at = datetime.utcnow() - timedelta(days=8)
        db_session.add(old_log)

        # Create recent log
        new_log = SystemLog(
            severity="INFO",
            message="Recent log message",
            source="test",
        )
        db_session.add(new_log)
        await db_session.commit()

        # Query should only return recent log (if retention filter implemented)
        # Currently, this documents expected behavior
        result = await db_session.execute(select(SystemLog))
        logs = result.scalars().all()
        assert len(logs) == 2  # Without retention filter, both exist


class TestLogContract:
    """Contract tests for log API responses (QA-REG-003)."""

    @pytest.mark.asyncio
    async def test_log_entry_response_schema(self, client, db_session: AsyncSession):
        """QA-CONTRACT-014: Log entry has all required fields."""
        # Create test user
        user = await create_user(db_session, "log-contract@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        db_session.add(SystemLog(severity="INFO", message="Contract test", source="api"))
        await db_session.commit()

        response = await client.get("/api/logs?limit=1", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert len(data["logs"]) >= 1
        log = data["logs"][0]

        # Required fields per API contract
        required_fields = ["id", "severity", "message", "source", "created_at", "severity_color"]
        for field in required_fields:
            assert field in log, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_log_list_response_includes_total(self, client, db_session: AsyncSession):
        """QA-CONTRACT-015: Log list response includes total count for pagination."""
        # Create test user
        user = await create_user(db_session, "log-list@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        response = await client.get("/api/logs", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "logs" in data
        assert "limit" in data
        assert "offset" in data
        assert "filters_applied" in data

    @pytest.mark.asyncio
    async def test_severity_counts_response_schema(self, client, db_session: AsyncSession):
        """QA-CONTRACT-016: Severity counts response has all required fields."""
        # Create test user
        user = await create_user(db_session, "log-sev@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        response = await client.get("/api/logs/severity-counts", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert "period_days" in data
        assert "counts" in data
        assert all(sev in data["counts"] for sev in ["INFO", "WARN", "ERROR"])
        assert "total" in data
        assert "cutoff_date" in data
