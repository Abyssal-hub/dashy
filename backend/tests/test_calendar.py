"""Tests for calendar module."""

import pytest
from httpx import AsyncClient

from app.services.auth.service import create_user, create_access_token


class TestCalendarModuleCRUD:
    """Test Calendar event CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_calendar_module(self, client, db_session):
        """Create a calendar module."""
        user = await create_user(db_session, "calendar-user@example.com", "password123")
        token = create_access_token(str(user.id))
        
        response = await client.post(
            "/api/modules",
            json={
                "module_type": "calendar",
                "name": "My Calendar",
                "config": {"default_view": "month", "show_weekends": True},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["module_type"] == "calendar"
        assert data["name"] == "My Calendar"
        return data["id"]
    
    @pytest.mark.asyncio
    async def test_create_event(self, client, db_session):
        """Test creating a personal calendar event."""
        user = await create_user(db_session, "event-user@example.com", "password123")
        token = create_access_token(str(user.id))
        
        # Create calendar module first
        module_resp = await client.post(
            "/api/modules",
            json={
                "module_type": "calendar",
                "name": "Economic Calendar",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        module_id = module_resp.json()["id"]
        
        # Create event
        from datetime import datetime, timedelta
        start_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
        
        response = await client.post(
            f"/api/modules/{module_id}/calendar/events",
            json={
                "title": "Fed Meeting",
                "description": "FOMC interest rate decision",
                "start_time": start_time,
                "is_all_day": False,
                "event_type": "economic",
                "impact": "high",
                "currency": "USD"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Fed Meeting"
        assert data["event_type"] == "economic"
        assert data["impact"] == "high"
        assert data["source"] == "manual"
    
    @pytest.mark.asyncio
    async def test_list_events(self, client, db_session):
        """Test listing calendar events."""
        user = await create_user(db_session, "list-events@example.com", "password123")
        token = create_access_token(str(user.id))
        
        # Create module
        module_resp = await client.post(
            "/api/modules",
            json={
                "module_type": "calendar",
                "name": "Test Calendar",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        module_id = module_resp.json()["id"]
        
        # Create multiple events
        from datetime import datetime, timedelta
        for i in range(3):
            await client.post(
                f"/api/modules/{module_id}/calendar/events",
                json={
                    "title": f"Event {i+1}",
                    "start_time": (datetime.utcnow() + timedelta(days=i+1)).isoformat(),
                    "event_type": "personal"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
        
        # List events
        response = await client.get(
            f"/api/modules/{module_id}/calendar/events",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["events"]) == 3
    
    @pytest.mark.asyncio
    async def test_update_event(self, client, db_session):
        """Test updating a calendar event."""
        user = await create_user(db_session, "update-event@example.com", "password123")
        token = create_access_token(str(user.id))
        
        # Create module and event
        module_resp = await client.post(
            "/api/modules",
            json={
                "module_type": "calendar",
                "name": "Test Calendar",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        module_id = module_resp.json()["id"]
        
        from datetime import datetime, timedelta
        event_resp = await client.post(
            f"/api/modules/{module_id}/calendar/events",
            json={
                "title": "Original Title",
                "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        event_id = event_resp.json()["id"]
        
        # Update event
        response = await client.put(
            f"/api/modules/{module_id}/calendar/events/{event_id}",
            json={"title": "Updated Title", "impact": "medium"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["impact"] == "medium"
    
    @pytest.mark.asyncio
    async def test_delete_event(self, client, db_session):
        """Test soft-deleting a calendar event."""
        user = await create_user(db_session, "delete-event@example.com", "password123")
        token = create_access_token(str(user.id))
        
        # Create module and event
        module_resp = await client.post(
            "/api/modules",
            json={
                "module_type": "calendar",
                "name": "Test Calendar",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        module_id = module_resp.json()["id"]
        
        from datetime import datetime, timedelta
        event_resp = await client.post(
            f"/api/modules/{module_id}/calendar/events",
            json={
                "title": "To Delete",
                "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        event_id = event_resp.json()["id"]
        
        # Delete event
        response = await client.delete(
            f"/api/modules/{module_id}/calendar/events/{event_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
        
        # Verify event is soft deleted (not in list)
        list_resp = await client.get(
            f"/api/modules/{module_id}/calendar/events",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_resp.json()["total"] == 0


class TestCalendarKeywordFilters:
    """Test keyword filter functionality."""
    
    @pytest.mark.asyncio
    async def test_create_keyword_filter(self, client, db_session):
        """Test creating a keyword filter."""
        user = await create_user(db_session, "filter-user@example.com", "password123")
        token = create_access_token(str(user.id))
        
        # Create module
        module_resp = await client.post(
            "/api/modules",
            json={
                "module_type": "calendar",
                "name": "Filtered Calendar",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        module_id = module_resp.json()["id"]
        
        # Create filter
        response = await client.post(
            f"/api/modules/{module_id}/calendar/filters",
            json={"keyword": "Fed", "is_include": True},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["keyword"] == "Fed"
        assert data["is_include"] is True
    
    @pytest.mark.asyncio
    async def test_list_keyword_filters(self, client, db_session):
        """Test listing keyword filters."""
        user = await create_user(db_session, "list-filters@example.com", "password123")
        token = create_access_token(str(user.id))
        
        # Create module
        module_resp = await client.post(
            "/api/modules",
            json={
                "module_type": "calendar",
                "name": "Filtered Calendar",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        module_id = module_resp.json()["id"]
        
        # Create filters
        for keyword in ["Fed", "ECB", "NFP"]:
            await client.post(
                f"/api/modules/{module_id}/calendar/filters",
                json={"keyword": keyword, "is_include": True},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        # List filters
        response = await client.get(
            f"/api/modules/{module_id}/calendar/filters",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["filters"]) == 3
    
    @pytest.mark.asyncio
    async def test_delete_keyword_filter(self, client, db_session):
        """Test deleting a keyword filter."""
        user = await create_user(db_session, "delete-filter@example.com", "password123")
        token = create_access_token(str(user.id))
        
        # Create module and filter
        module_resp = await client.post(
            "/api/modules",
            json={
                "module_type": "calendar",
                "name": "Filtered Calendar",
                "config": {},
                "size": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        module_id = module_resp.json()["id"]
        
        filter_resp = await client.post(
            f"/api/modules/{module_id}/calendar/filters",
            json={"keyword": "ToRemove", "is_include": False},
            headers={"Authorization": f"Bearer {token}"}
        )
        filter_id = filter_resp.json()["id"]
        
        # Delete filter
        response = await client.delete(
            f"/api/modules/{module_id}/calendar/filters/{filter_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204


class TestCalendarHandler:
    """Test CalendarHandler functionality."""
    
    @pytest.mark.asyncio
    async def test_handler_get_data_placeholder(self, client, db_session):
        """Test handler returns placeholder when no db session."""
        from app.modules.handlers.calendar import CalendarHandler
        
        handler = CalendarHandler()
        data = await handler.get_data("test-module-id", "medium")
        
        assert data["module_id"] == "test-module-id"
        assert data["size"] == "medium"
        assert data["events"] == []
        assert data["total_events"] == 0
    
    @pytest.mark.asyncio
    async def test_handler_validate_config(self, client, db_session):
        """Test config validation."""
        from app.modules.handlers.calendar import CalendarHandler
        
        handler = CalendarHandler()
        
        # Calendar config is optional, should accept anything
        assert handler.validate_config({}) is True
        assert handler.validate_config({"default_view": "month"}) is True
        assert handler.validate_config({"scraped_keywords": ["Fed", "ECB"]}) is True
