"""
QA-013: Frontend Interaction Logging Test Suite

Tests for the frontend interaction logging system including:
- InteractionLogger class functionality
- API endpoint for logging interactions
- Severity level assignment (ERROR/WARN/INFO)
- Duration calculation
- Error handling and context capture

Updated for file-based logging (no DB dependency for logs).
"""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from app.core.file_logger import (
    write_log,
    write_interaction_log,
    read_logs,
)
import app.core.file_logger as file_logger
from app.services.auth.service import create_user, create_access_token
from app.schemas.interaction import InteractionLogCreate, InteractionTarget


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


class TestInteractionLoggerAPI:
    """Test POST /api/logs/interaction endpoint."""

    @pytest.mark.asyncio
    async def test_interaction_log_returns_202_accepted(self, client, db_session):
        """QA-013-001: Interaction logging returns 202 Accepted."""
        user = await create_user(db_session, "interaction-test@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        interaction_request = {
            "interactionId": "int_test_001",
            "userId": str(user.id),
            "sessionId": "sess_test_001",
            "type": "click",
            "target": {
                "element": "button",
                "component": "TestComponent",
                "route": "/test"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "endedAt": datetime.utcnow().isoformat(),
            "duration": 150,
            "success": True,
        }

        response = await client.post(
            "/api/logs/interaction",
            json=interaction_request,
            headers=headers,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "logged"
        assert data["interactionId"] == "int_test_001"

    @pytest.mark.asyncio
    async def test_interaction_log_stores_in_file(self, client, db_session):
        """QA-013-002: Interaction is stored in file-based logs."""
        user = await create_user(db_session, "interaction-store@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        interaction_request = {
            "interactionId": "int_test_002",
            "userId": str(user.id),
            "sessionId": "sess_test_002",
            "type": "click",
            "target": {
                "element": "submit-btn",
                "component": "Form",
                "route": "/form"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "success": True,
        }

        response = await client.post(
            "/api/logs/interaction",
            json=interaction_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify log was written to app.log (interactions are written to both)
        logs = read_logs(source="frontend", limit=10)
        assert logs["total"] >= 1
        
        frontend_logs = [l for l in logs["logs"] if l["source"] == "frontend"]
        assert len(frontend_logs) >= 1
        
        # Check that interaction_id is in metadata
        recent_log = frontend_logs[0]
        assert "interaction_id" in recent_log.get("metadata", {})

    @pytest.mark.asyncio
    async def test_failed_interaction_gets_error_severity(self, client, db_session):
        """QA-013-003: Failed interaction gets ERROR severity."""
        user = await create_user(db_session, "interaction-error@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        interaction_request = {
            "interactionId": "int_test_003",
            "userId": str(user.id),
            "sessionId": "sess_test_003",
            "type": "api_call",
            "target": {
                "element": "fetch-btn",
                "component": "DataLoader",
                "route": "/data"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "endedAt": datetime.utcnow().isoformat(),
            "duration": 500,
            "success": False,
            "error": "Network timeout",
        }

        response = await client.post(
            "/api/logs/interaction",
            json=interaction_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify ERROR severity in file
        logs = read_logs(severity="ERROR", limit=10)
        error_logs = [l for l in logs["logs"] if l["severity"] == "ERROR"]
        
        assert len(error_logs) >= 1
        # Check that our interaction_id is in one of the error logs' metadata
        interaction_ids = [l.get("metadata", {}).get("interaction_id") for l in error_logs]
        assert "int_test_003" in interaction_ids

    @pytest.mark.asyncio
    async def test_slow_interaction_gets_warn_severity(self, client, db_session):
        """QA-013-004: Slow interaction (>5000ms) gets WARN severity."""
        user = await create_user(db_session, "interaction-slow@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        interaction_request = {
            "interactionId": "int_test_004",
            "userId": str(user.id),
            "sessionId": "sess_test_004",
            "type": "navigation",
            "target": {
                "element": "page",
                "component": "Dashboard",
                "route": "/dashboard"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "endedAt": datetime.utcnow().isoformat(),
            "duration": 6000,  # Slow!
            "success": True,
        }

        response = await client.post(
            "/api/logs/interaction",
            json=interaction_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify WARN severity in file
        logs = read_logs(severity="WARN", limit=10)
        warn_logs = [l for l in logs["logs"] if l["severity"] == "WARN"]
        
        assert len(warn_logs) >= 1
        # Check that our interaction_id is in one of the warn logs' metadata
        interaction_ids = [l.get("metadata", {}).get("interaction_id") for l in warn_logs]
        assert "int_test_004" in interaction_ids

    @pytest.mark.asyncio
    async def test_normal_interaction_gets_info_severity(self, client, db_session):
        """QA-013-005: Normal interaction gets INFO severity."""
        user = await create_user(db_session, "interaction-normal@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        interaction_request = {
            "interactionId": "int_test_005",
            "userId": str(user.id),
            "sessionId": "sess_test_005",
            "type": "click",
            "target": {
                "element": "btn",
                "component": "Button",
                "route": "/"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "endedAt": datetime.utcnow().isoformat(),
            "duration": 100,  # Fast
            "success": True,
        }

        response = await client.post(
            "/api/logs/interaction",
            json=interaction_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify INFO severity in file
        logs = read_logs(severity="INFO", limit=10)
        info_logs = [l for l in logs["logs"] if l["severity"] == "INFO"]
        
        # Check that our interaction_id is in one of the info logs' metadata
        interaction_ids = [l.get("metadata", {}).get("interaction_id") for l in info_logs]
        assert "int_test_005" in interaction_ids

    @pytest.mark.asyncio
    async def test_all_interaction_types_supported(self, client, db_session):
        """QA-013-006: All interaction types (click, hover, scroll, input, navigation, api_call) work."""
        user = await create_user(db_session, "interaction-types@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        interaction_types = ["click", "hover", "scroll", "input", "navigation", "api_call"]

        for idx, int_type in enumerate(interaction_types):
            interaction_request = {
                "interactionId": f"int_type_{idx}",
                "userId": str(user.id),
                "sessionId": f"sess_type_{idx}",
                "type": int_type,
                "target": {
                    "element": "test",
                    "component": "Test",
                    "route": "/test"
                },
                "startedAt": datetime.utcnow().isoformat(),
                "success": True,
            }

            response = await client.post(
                "/api/logs/interaction",
                json=interaction_request,
                headers=headers,
            )

            assert response.status_code == 202, f"Failed for type: {int_type}"

    @pytest.mark.asyncio
    async def test_interaction_log_with_metadata(self, client, db_session):
        """QA-013-007: Interaction logs can include custom metadata."""
        user = await create_user(db_session, "interaction-meta@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        interaction_request = {
            "interactionId": "int_test_007",
            "userId": str(user.id),
            "sessionId": "sess_test_007",
            "type": "api_call",
            "target": {
                "element": "api-btn",
                "component": "DataFetcher",
                "route": "/data"
            },
            "metadata": {
                "endpoint": "/api/data",
                "params": {"limit": 10},
                "cache_hit": False,
            },
            "startedAt": datetime.utcnow().isoformat(),
            "success": True,
        }

        response = await client.post(
            "/api/logs/interaction",
            json=interaction_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify metadata via API
        api_response = await client.get("/api/logs?source=frontend", headers=headers)
        assert api_response.status_code == 200
        data = api_response.json()
        
        # Find log with our interaction
        found = False
        for log in data.get("logs", []):
            meta = log.get("metadata", {})
            if meta.get("interaction_id") == "int_test_007":
                # Metadata is stored in the metadata field
                found = True
                break
        assert found, "Interaction with metadata not found in logs"

    @pytest.mark.asyncio
    async def test_interaction_log_duration_in_message(self, client, db_session):
        """QA-013-008: Duration is included in the log message."""
        user = await create_user(db_session, "interaction-duration@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        interaction_request = {
            "interactionId": "int_test_008",
            "userId": str(user.id),
            "sessionId": "sess_test_008",
            "type": "click",
            "target": {
                "element": "btn",
                "component": "Button",
                "route": "/"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "endedAt": datetime.utcnow().isoformat(),
            "duration": 250,
            "success": True,
        }

        response = await client.post(
            "/api/logs/interaction",
            json=interaction_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify duration in message via API
        api_response = await client.get("/api/logs?source=frontend", headers=headers)
        assert api_response.status_code == 200
        data = api_response.json()
        
        log_messages = [log["message"] for log in data.get("logs", [])]
        assert any("250ms" in msg for msg in log_messages)

    @pytest.mark.asyncio
    async def test_interaction_log_error_in_message(self, client, db_session):
        """QA-013-009: Error message is included in the log message."""
        user = await create_user(db_session, "interaction-errmsg@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        interaction_request = {
            "interactionId": "int_test_009",
            "userId": str(user.id),
            "sessionId": "sess_test_009",
            "type": "api_call",
            "target": {
                "element": "api",
                "component": "API",
                "route": "/api"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "endedAt": datetime.utcnow().isoformat(),
            "duration": 500,
            "success": False,
            "error": "Something went wrong",
        }

        response = await client.post(
            "/api/logs/interaction",
            json=interaction_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify error in message via API
        api_response = await client.get("/api/logs?source=frontend&severity=ERROR", headers=headers)
        assert api_response.status_code == 200
        data = api_response.json()
        
        log_messages = [log["message"] for log in data.get("logs", [])]
        assert any("Something went wrong" in msg for msg in log_messages)

    @pytest.mark.asyncio
    async def test_interaction_log_correlation_ids(self, client, db_session):
        """QA-013-010: InteractionId, userId, sessionId are stored in metadata."""
        user = await create_user(db_session, "interaction-correlation@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        interaction_request = {
            "interactionId": "int_correlation_test",
            "userId": str(user.id),
            "sessionId": "sess_correlation_test",
            "type": "click",
            "target": {
                "element": "btn",
                "component": "Test",
                "route": "/"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "success": True,
        }

        response = await client.post(
            "/api/logs/interaction",
            json=interaction_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Verify correlation IDs via API
        api_response = await client.get("/api/logs?source=frontend", headers=headers)
        assert api_response.status_code == 200
        data = api_response.json()
        
        # Find log with our correlation IDs
        correlation_log = None
        for log in data.get("logs", []):
            meta = log.get("metadata", {})
            if (meta.get("interaction_id") == "int_correlation_test" and
                meta.get("session_id") == "sess_correlation_test"):
                correlation_log = log
                break
        
        assert correlation_log is not None


class TestInteractionSchemas:
    """Test InteractionLogCreate schema validation."""

    def test_valid_interaction_log_create(self):
        """QA-013-011: Valid interaction data passes schema validation."""
        data = {
            "interactionId": "int_valid",
            "userId": "user123",
            "sessionId": "sess123",
            "type": "click",
            "target": {
                "element": "button",
                "component": "Form",
                "route": "/form"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "success": True,
        }
        
        log = InteractionLogCreate(**data)
        assert log.interactionId == "int_valid"
        assert log.type == "click"
        assert log.target.element == "button"

    def test_invalid_type_rejected(self):
        """QA-013-012: Invalid interaction type is rejected."""
        data = {
            "interactionId": "int_invalid",
            "userId": "user123",
            "sessionId": "sess123",
            "type": "invalid_type",
            "target": {
                "element": "button",
                "component": "Form",
                "route": "/form"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "success": True,
        }
        
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            InteractionLogCreate(**data)

    def test_missing_required_fields_rejected(self):
        """QA-013-013: Missing required fields are rejected."""
        data = {
            "interactionId": "int_missing",
            # Missing userId, sessionId, type, target
            "startedAt": datetime.utcnow().isoformat(),
            "success": True,
        }
        
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            InteractionLogCreate(**data)

    def test_duration_must_be_non_negative(self):
        """QA-013-014: Negative duration is rejected."""
        data = {
            "interactionId": "int_negative",
            "userId": "user123",
            "sessionId": "sess123",
            "type": "click",
            "target": {
                "element": "button",
                "component": "Form",
                "route": "/form"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "endedAt": datetime.utcnow().isoformat(),
            "duration": -100,
            "success": True,
        }
        
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            InteractionLogCreate(**data)

    def test_optional_fields_allowed(self):
        """QA-013-015: Optional fields (endedAt, duration, error, metadata) are allowed."""
        data = {
            "interactionId": "int_optional",
            "userId": "user123",
            "sessionId": "sess123",
            "type": "click",
            "target": {
                "element": "button",
                "component": "Form",
                "route": "/form"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "endedAt": datetime.utcnow().isoformat(),
            "duration": 150,
            "success": False,
            "error": "Error message",
            "metadata": {"key": "value"},
        }
        
        log = InteractionLogCreate(**data)
        assert log.duration == 150
        assert log.error == "Error message"
        assert log.metadata == {"key": "value"}


class TestInteractionIntegration:
    """Integration tests for frontend interaction logging."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_end_to_end_interaction_logging(self, client, db_session):
        """QA-013-016: End-to-end: Log interaction and verify it appears in query."""
        user = await create_user(db_session, "interaction-e2e@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Step 1: Log an interaction
        interaction_request = {
            "interactionId": "int_e2e_test",
            "userId": str(user.id),
            "sessionId": "sess_e2e_test",
            "type": "navigation",
            "target": {
                "element": "page",
                "component": "Dashboard",
                "route": "/dashboard"
            },
            "startedAt": datetime.utcnow().isoformat(),
            "endedAt": datetime.utcnow().isoformat(),
            "duration": 500,
            "success": True,
        }

        response = await client.post(
            "/api/logs/interaction",
            json=interaction_request,
            headers=headers,
        )

        assert response.status_code == 202

        # Step 2: Query logs via API and verify our interaction is there
        response = await client.get(
            "/api/logs?source=frontend",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        
        # Check if our interaction is in the logs
        log_messages = [log["message"] for log in data.get("logs", [])]
        assert any("navigation" in msg for msg in log_messages)

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_interaction_severity_filtering(self, client, db_session):
        """QA-013-017: Interaction logs can be filtered by severity."""
        user = await create_user(db_session, "interaction-filter@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Log an ERROR interaction
        error_request = {
            "interactionId": "int_error_filter",
            "userId": str(user.id),
            "sessionId": "sess_filter",
            "type": "api_call",
            "target": {"element": "api", "component": "API", "route": "/"},
            "startedAt": datetime.utcnow().isoformat(),
            "success": False,
            "error": "Filter test error",
        }

        await client.post("/api/logs/interaction", json=error_request, headers=headers)

        # Query with ERROR severity filter via API
        response = await client.get(
            "/api/logs?source=frontend&severity=ERROR",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        
        # All returned logs should be ERROR severity
        for log in data.get("logs", []):
            assert log["severity"] == "ERROR"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_multiple_interactions_same_session(self, client, db_session):
        """QA-013-018: Multiple interactions in same session are tracked separately."""
        user = await create_user(db_session, "interaction-multi@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        session_id = "sess_multi_test"
        interaction_ids = []

        # Log multiple interactions
        for i in range(3):
            interaction_request = {
                "interactionId": f"int_multi_{i}",
                "userId": str(user.id),
                "sessionId": session_id,
                "type": "click",
                "target": {"element": f"btn-{i}", "component": "Test", "route": "/"},
                "startedAt": datetime.utcnow().isoformat(),
                "success": True,
            }

            response = await client.post(
                "/api/logs/interaction",
                json=interaction_request,
                headers=headers,
            )

            assert response.status_code == 202
            interaction_ids.append(f"int_multi_{i}")

        # Verify all interactions stored in file via API
        api_response = await client.get("/api/logs?source=frontend&limit=50", headers=headers)
        assert api_response.status_code == 200
        data = api_response.json()
        
        stored_session_ids = [l.get("metadata", {}).get("session_id") for l in data.get("logs", [])]
        assert session_id in stored_session_ids
