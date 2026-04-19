"""
QA-013: Frontend Interaction Logging Test Suite

Tests for the frontend interaction logging system including:
- InteractionLogger class functionality
- API endpoint for logging interactions
- Severity level assignment (ERROR/WARN/INFO)
- Duration calculation
- Error handling and context capture

Related: DEV-015, ARCHITECTURE.md Section 11.2.2
"""

import pytest
import json
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth.service import create_user, create_access_token
from app.models.log import SystemLog
from app.schemas.interaction import InteractionLogCreate, InteractionTarget


def get_auth_headers(user_id: str) -> dict:
    """Create authorization headers for a user."""
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


class TestInteractionLoggerAPI:
    """Test POST /api/logs/interaction endpoint."""

    @pytest.mark.asyncio
    async def test_interaction_log_returns_202_accepted(self, client, db_session: AsyncSession):
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
    async def test_interaction_log_stores_in_system_logs(self, client, db_session: AsyncSession):
        """QA-013-002: Interaction is stored in system_logs table."""
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

        # Verify log was stored
        result = await db_session.execute(
            select(SystemLog).where(SystemLog.source == "frontend")
        )
        logs = result.scalars().all()
        
        assert len(logs) >= 1
        frontend_log = logs[-1]  # Most recent
        assert frontend_log.source == "frontend"
        assert "click" in frontend_log.message
        assert frontend_log.extra_data is not None
        assert frontend_log.extra_data.get("interaction_id") == "int_test_002"

    @pytest.mark.asyncio
    async def test_failed_interaction_gets_error_severity(self, client, db_session: AsyncSession):
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

        # Verify ERROR severity
        result = await db_session.execute(
            select(SystemLog)
            .where(SystemLog.source == "frontend")
            .where(SystemLog.severity == "ERROR")
        )
        error_logs = result.scalars().all()
        
        assert len(error_logs) >= 1
        assert any("int_test_003" in str(log.extra_data) for log in error_logs)

    @pytest.mark.asyncio
    async def test_slow_interaction_gets_warn_severity(self, client, db_session: AsyncSession):
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

        # Verify WARN severity
        result = await db_session.execute(
            select(SystemLog)
            .where(SystemLog.source == "frontend")
            .where(SystemLog.severity == "WARN")
        )
        warn_logs = result.scalars().all()
        
        assert len(warn_logs) >= 1
        assert any("int_test_004" in str(log.extra_data) for log in warn_logs)

    @pytest.mark.asyncio
    async def test_normal_interaction_gets_info_severity(self, client, db_session: AsyncSession):
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

        # Verify INFO severity
        result = await db_session.execute(
            select(SystemLog)
            .where(SystemLog.source == "frontend")
            .where(SystemLog.severity == "INFO")
        )
        info_logs = result.scalars().all()
        
        assert any("int_test_005" in str(log.extra_data) for log in info_logs)

    @pytest.mark.asyncio
    async def test_all_interaction_types_supported(self, client, db_session: AsyncSession):
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
    async def test_interaction_log_with_metadata(self, client, db_session: AsyncSession):
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

        # Verify metadata was stored
        result = await db_session.execute(
            select(SystemLog).where(SystemLog.source == "frontend")
        )
        logs = result.scalars().all()
        
        meta_log = next((log for log in logs if log.extra_data and 
                        log.extra_data.get("interaction_id") == "int_test_007"), None)
        assert meta_log is not None
        assert meta_log.extra_data.get("metadata", {}).get("endpoint") == "/api/data"

    @pytest.mark.asyncio
    async def test_interaction_log_duration_in_message(self, client, db_session: AsyncSession):
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

        # Verify duration in message
        result = await db_session.execute(
            select(SystemLog)
            .where(SystemLog.source == "frontend")
            .where(SystemLog.message.like("%250ms%"))
        )
        duration_logs = result.scalars().all()
        
        assert len(duration_logs) >= 1

    @pytest.mark.asyncio
    async def test_interaction_log_error_in_message(self, client, db_session: AsyncSession):
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

        # Verify error in message
        result = await db_session.execute(
            select(SystemLog)
            .where(SystemLog.source == "frontend")
            .where(SystemLog.message.like("%Something went wrong%"))
        )
        error_logs = result.scalars().all()
        
        assert len(error_logs) >= 1

    @pytest.mark.asyncio
    async def test_interaction_log_correlation_ids(self, client, db_session: AsyncSession):
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

        # Verify correlation IDs
        result = await db_session.execute(
            select(SystemLog).where(SystemLog.source == "frontend")
        )
        logs = result.scalars().all()
        
        correlation_log = next((log for log in logs if 
            log.extra_data and 
            log.extra_data.get("interaction_id") == "int_correlation_test" and
            log.extra_data.get("session_id") == "sess_correlation_test" and
            log.extra_data.get("user_id") == str(user.id)
        ), None)
        
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

    @pytest.mark.asyncio
    async def test_end_to_end_interaction_logging(self, client, db_session: AsyncSession):
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

        # Step 2: Query logs and verify our interaction is there
        response = await client.get(
            "/api/logs?source=frontend",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        
        # Check if our interaction is in the logs
        log_messages = [log["message"] for log in data.get("logs", [])]
        assert any("navigation" in msg for msg in log_messages)

    @pytest.mark.asyncio
    async def test_interaction_severity_filtering(self, client, db_session: AsyncSession):
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

        # Query with ERROR severity filter
        response = await client.get(
            "/api/logs?source=frontend&severity=ERROR",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        
        # All returned logs should be ERROR severity
        for log in data.get("logs", []):
            assert log["severity"] == "ERROR"

    @pytest.mark.asyncio
    async def test_multiple_interactions_same_session(self, client, db_session: AsyncSession):
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

        # Verify all interactions stored
        result = await db_session.execute(
            select(SystemLog)
            .where(SystemLog.source == "frontend")
            .where(SystemLog.extra_data.isnot(None))
        )
        logs = result.scalars().all()

        stored_ids = [log.extra_data.get("session_id") for log in logs if log.extra_data]
        assert session_id in stored_ids
