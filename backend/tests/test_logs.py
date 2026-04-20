"""
QA-012: Log Module Test Suite - Updated for File-Based Logging

Tests for the system logging module including:
- LogHandler functionality (now file-based)
- API endpoints (now file-based)
- System event logging integration (now file-based)
- Log retention (file-based cleanup)

Related: DEV-012, QA-REG-003
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from pathlib import Path

from app.core.file_logger import (
    write_log,
    write_interaction_log,
    read_logs,
    get_severity_counts,
    cleanup_old_logs,
    APP_LOG_FILE,
)
from app.modules.handlers.log import LogHandler, write_system_log
from app.services.auth.service import create_user, create_access_token


@pytest.fixture(autouse=True)
def temp_log_dir(monkeypatch):
    """Use temporary directory for log files during tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("LOG_DIR", tmpdir)
        # Reset the file_logger module's LOG_DIR
        import app.core.file_logger as fl
        fl.LOG_DIR = Path(tmpdir)
        fl.APP_LOG_FILE = fl.LOG_DIR / "app.log"
        fl.INTERACTION_LOG_FILE = fl.LOG_DIR / "interactions.log"
        fl.ERROR_LOG_FILE = fl.LOG_DIR / "errors.log"
        fl.LOG_DIR.mkdir(parents=True, exist_ok=True)
        yield tmpdir


def get_auth_headers(user_id: str) -> dict:
    """Create authorization headers for a user."""
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def create_test_logs(count: int, severity: str = "INFO", source: str = "test") -> None:
    """Helper to create test log entries in file."""
    for i in range(count):
        write_log(severity=severity, message=f"Test message {i}", source=source)


class TestLogHandler:
    """Test the LogHandler module handler (now file-based)."""

    @pytest.mark.asyncio
    async def test_handler_get_data_compact_size(self, db_session):
        """QA-012-001: LogHandler returns 5 logs for compact size."""
        # Create test logs in file
        create_test_logs(10)

        handler = LogHandler()
        data = await handler.get_data(
            module_id=str(uuid4()),
            size="compact",
            db_session=db_session,
        )

        assert len(data["logs"]) == 5
        assert data["size"] == "compact"

    @pytest.mark.asyncio
    async def test_handler_get_data_standard_size(self, db_session):
        """QA-012-002: LogHandler returns 20 logs for standard size."""
        create_test_logs(25, severity="INFO")

        handler = LogHandler()
        data = await handler.get_data(
            module_id=str(uuid4()),
            size="standard",
            db_session=db_session,
        )

        assert len(data["logs"]) == 20
        assert data["size"] == "standard"

    @pytest.mark.asyncio
    async def test_handler_get_data_expanded_size(self, db_session):
        """QA-012-003: LogHandler returns up to 100 logs for expanded size."""
        create_test_logs(150)

        handler = LogHandler()
        data = await handler.get_data(
            module_id=str(uuid4()),
            size="expanded",
            db_session=db_session,
        )

        assert len(data["logs"]) == 100
        assert data["size"] == "expanded"

    @pytest.mark.asyncio
    async def test_handler_filter_by_severity(self, db_session):
        """QA-012-004: LogHandler filters by severity correctly."""
        # Create logs with different severities
        for i in range(5):
            write_log(severity="INFO", message=f"Info {i}", source="test")
            write_log(severity="WARN", message=f"Warn {i}", source="test")
            write_log(severity="ERROR", message=f"Error {i}", source="test")

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
    async def test_handler_filter_by_source(self, db_session):
        """QA-012-005: LogHandler filters by source correctly."""
        # Create logs from different sources
        for i in range(5):
            write_log(severity="INFO", message=f"Consumer log {i}", source="consumer")
            write_log(severity="INFO", message=f"API log {i}", source="api")

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
    async def test_handler_returns_severity_counts(self, db_session):
        """QA-012-006: LogHandler returns accurate severity counts."""
        # Create logs with known distribution
        for i in range(10):
            write_log(severity="INFO", message=f"Info {i}", source="test")
        for i in range(5):
            write_log(severity="WARN", message=f"Warn {i}", source="test")
        for i in range(3):
            write_log(severity="ERROR", message=f"Error {i}", source="test")

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
    async def test_handler_returns_severity_color(self, db_session):
        """QA-012-007: LogHandler returns color codes for frontend."""
        write_log(severity="INFO", message="Info", source="test")
        write_log(severity="WARN", message="Warn", source="test")
        write_log(severity="ERROR", message="Error", source="test")

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
    """Test the write_system_log utility function (now file-based)."""

    @pytest.mark.asyncio
    async def test_write_system_log_creates_entry(self, db_session):
        """QA-012-009: write_system_log creates a log entry in file."""
        log = await write_system_log(
            db_session=db_session,  # Kept for backwards compat, not used
            severity="INFO",
            message="Test message",
            source="test",
            metadata={"key": "value"},
        )

        assert log["severity"] == "INFO"
        assert log["message"] == "Test message"
        assert log["source"] == "test"
        assert log["metadata"] == {"key": "value"}
        assert "timestamp" in log

    @pytest.mark.asyncio
    async def test_write_system_log_severity_uppercase(self, db_session):
        """QA-012-010: write_system_log normalizes severity to uppercase."""
        log = await write_system_log(
            db_session=db_session,
            severity="info",  # lowercase input
            message="Test message",
            source="test",
        )

        assert log["severity"] == "INFO"

    @pytest.mark.asyncio
    async def test_write_system_log_with_module_id(self, db_session):
        """QA-012-011: write_system_log includes module_id in metadata."""
        module_id = str(uuid4())

        log = await write_system_log(
            db_session=db_session,
            severity="INFO",
            message="Module-specific message",
            source="test",
            module_id=module_id,
        )

        assert log["metadata"]["module_id"] == module_id


class TestLogsAPI:
    """Test the /logs API endpoints (now file-based)."""

    @pytest.mark.asyncio
    async def test_get_logs_returns_list(self, client, db_session):
        """QA-012-012: GET /logs returns list of logs."""
        # Create test user and auth headers
        user = await create_user(db_session, "logs-test@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create test logs in file
        for i in range(5):
            write_log(severity="INFO", message=f"API test {i}", source="api")

        response = await client.get("/api/logs", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert len(data["logs"]) >= 5

    @pytest.mark.asyncio
    async def test_get_logs_with_severity_filter(self, client, db_session):
        """QA-012-013: GET /logs filters by severity."""
        # Create test user
        user = await create_user(db_session, "logs-filter@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create mixed severity logs
        for i in range(3):
            write_log(severity="INFO", message=f"Info {i}", source="api")
        for i in range(2):
            write_log(severity="ERROR", message=f"Error {i}", source="api")

        response = await client.get("/api/logs?severity=ERROR", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert all(log["severity"] == "ERROR" for log in data["logs"])
        assert data["filters_applied"]["severity"] == "ERROR"

    @pytest.mark.asyncio
    async def test_get_logs_with_source_filter(self, client, db_session):
        """QA-012-014: GET /logs filters by source."""
        # Create test user
        user = await create_user(db_session, "logs-source@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create logs from different sources
        write_log(severity="INFO", message="Consumer message", source="consumer")
        write_log(severity="INFO", message="API message", source="api")

        response = await client.get("/api/logs?source=consumer", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert all(log["source"] == "consumer" for log in data["logs"])

    @pytest.mark.asyncio
    async def test_get_logs_pagination(self, client, db_session):
        """QA-012-015: GET /logs supports pagination."""
        # Create test user
        user = await create_user(db_session, "logs-page@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create many logs
        for i in range(25):
            write_log(severity="INFO", message=f"Paginated {i}", source="api")

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
    async def test_get_logs_ordering(self, client, db_session):
        """QA-012-016: GET /logs returns logs in reverse chronological order."""
        # Create test user
        user = await create_user(db_session, "logs-order@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create logs with delays
        for i in range(5):
            write_log(severity="INFO", message=f"Order test {i}", source="api")

        response = await client.get("/api/logs?limit=5", headers=headers)
        assert response.status_code == 200
        data = response.json()

        # Verify reverse chronological order (newest first)
        timestamps = [log["created_at"] for log in data["logs"]]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.asyncio
    async def test_get_severity_counts(self, client, db_session):
        """QA-012-017: GET /logs/severity-counts returns counts."""
        # Create test user
        user = await create_user(db_session, "logs-counts@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        # Create logs with known distribution
        for i in range(10):
            write_log(severity="INFO", message=f"Info {i}", source="api")
        for i in range(5):
            write_log(severity="WARN", message=f"Warn {i}", source="api")
        for i in range(3):
            write_log(severity="ERROR", message=f"Error {i}", source="api")

        response = await client.get("/api/logs/severity-counts?days=7", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["counts"]["INFO"] == 10
        assert data["counts"]["WARN"] == 5
        assert data["counts"]["ERROR"] == 3
        assert data["total"] == 18
        assert "period_days" in data

    @pytest.mark.asyncio
    async def test_create_log_endpoint(self, client, db_session):
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
    async def test_get_module_logs(self, client, db_session):
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
            write_log(
                severity="INFO",
                message=f"Module log {i}",
                source="test",
                module_id=module_id,
            )

        response = await client.get(f"/api/logs/modules/{module_id}?size=standard", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 3

    @pytest.mark.asyncio
    async def test_logs_api_requires_auth(self, client, db_session):
        """QA-012-020: GET /logs requires authentication."""
        response = await client.get("/api/logs")
        assert response.status_code in (401, 403)  # Either unauthorized or forbidden


class TestSystemEventLogging:
    """Test that system events are logged to file (integration with other components)."""

    @pytest.mark.asyncio
    async def test_consumer_events_logged(self, db_session):
        """QA-012-021: Consumer start/stop events are written to file logs.
        
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

        assert log["source"] == "consumer"

        # Verify it can be retrieved from file
        logs = read_logs(source="consumer", limit=10)
        assert logs["total"] >= 1

    @pytest.mark.asyncio
    async def test_ingest_events_logged(self, db_session):
        """QA-012-022: Ingest operations are written to file logs."""
        log = await write_system_log(
            db_session=db_session,
            severity="INFO",
            message="Metrics ingested: 5 queued",
            source="ingest",
            metadata={"metrics_count": 5, "user_id": "test-user"},
        )

        assert log["source"] == "ingest"
        assert log["metadata"]["metrics_count"] == 5


class TestLogRetention:
    """Test the 7-day log retention policy (file-based)."""

    @pytest.mark.asyncio
    async def test_cleanup_old_logs(self, db_session):
        """QA-012-023: cleanup_old_logs removes logs older than retention period."""
        import json
        
        # Create recent logs
        for i in range(5):
            write_log(severity="INFO", message=f"Recent {i}", source="test")
        
        # Manually create old log entries in file
        old_timestamp = (datetime.utcnow() - timedelta(days=10)).isoformat()
        old_entry = {
            "id": str(uuid4()),
            "timestamp": old_timestamp,
            "severity": "INFO",
            "message": "Old log message",
            "source": "test",
            "metadata": {},
        }
        
        # Write old entry directly to file
        import app.core.file_logger as fl
        with open(fl.APP_LOG_FILE, "a") as f:
            f.write(json.dumps(old_entry) + "\n")
        
        # Verify old entry exists
        all_logs = read_logs(limit=100)
        assert len([l for l in all_logs["logs"] if l["message"] == "Old log message"]) == 1
        
        # Run cleanup
        removed = cleanup_old_logs()
        
        # Old log should be removed
        cleaned_logs = read_logs(limit=100)
        assert len([l for l in cleaned_logs["logs"] if l["message"] == "Old log message"]) == 0
        # Recent logs should remain
        assert len([l for l in cleaned_logs["logs"] if l["message"].startswith("Recent")]) == 5


class TestLogContract:
    """Contract tests for log API responses (QA-REG-003)."""

    @pytest.mark.asyncio
    async def test_log_entry_response_schema(self, client, db_session):
        """QA-CONTRACT-014: Log entry has all required fields."""
        # Create test user
        user = await create_user(db_session, "log-contract@example.com", "password123")
        headers = get_auth_headers(str(user.id))
        
        write_log(severity="INFO", message="Contract test", source="api")

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
    async def test_log_list_response_includes_total(self, client, db_session):
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
    async def test_severity_counts_response_schema(self, client, db_session):
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
