"""Calendar module handler."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules import ModuleHandler, register
from app.models.calendar import CalendarEvent, CalendarKeywordFilter
from app.schemas.calendar import (
    CalendarEventResponse,
    CalendarKeywordFilterResponse,
    CalendarDataResponse,
)


@register("calendar")
class CalendarHandler(ModuleHandler):
    """Handler for economic calendar modules."""
    
    @property
    def module_type(self) -> str:
        return "calendar"
    
    async def get_data(
        self, 
        module_id: str, 
        size: str,
        db_session: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Return calendar events with optional filtering.
        
        Args:
            module_id: The module UUID
            size: Display size (compact, medium, expanded)
            db_session: Database session for queries
        
        Returns:
            Calendar data including events and metadata
        """
        if db_session is None:
            # Return placeholder if no session available
            return {
                "module_id": module_id,
                "size": size,
                "events": [],
                "date_range": {"start": None, "end": None},
                "total_events": 0,
                "keyword_filters": None,
            }
        
        # Get date range based on size
        start_date, end_date = self._get_date_range(size)
        
        # Fetch events
        events = await self._fetch_events(
            db_session, 
            module_id, 
            start_date, 
            end_date
        )
        
        # Fetch keyword filters
        filters = await self._fetch_keyword_filters(db_session, module_id)
        
        # Build response
        return {
            "module_id": module_id,
            "size": size,
            "events": [self._event_to_dict(e) for e in events],
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "total_events": len(events),
            "keyword_filters": [self._filter_to_dict(f) for f in filters],
        }
    
    def _get_date_range(self, size: str) -> tuple[datetime | None, datetime | None]:
        """Get date range for calendar view based on size."""
        now = datetime.utcnow()
        
        if size == "compact":
            # Show next 7 days
            return now, now + timedelta(days=7)
        elif size == "medium":
            # Show next 30 days
            return now, now + timedelta(days=30)
        else:  # expanded
            # Show full year
            return now, now + timedelta(days=365)
    
    async def _fetch_events(
        self,
        db_session: AsyncSession,
        module_id: str,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> list[CalendarEvent]:
        """Fetch calendar events for a module within date range."""
        query = select(CalendarEvent).where(
            and_(
                CalendarEvent.module_id == module_id,
                CalendarEvent.is_active == True,
            )
        )
        
        if start_date:
            query = query.where(CalendarEvent.start_time >= start_date)
        if end_date:
            query = query.where(CalendarEvent.start_time <= end_date)
        
        query = query.order_by(CalendarEvent.start_time)
        
        result = await db_session.execute(query)
        return list(result.scalars().all())
    
    async def _fetch_keyword_filters(
        self,
        db_session: AsyncSession,
        module_id: str,
    ) -> list[CalendarKeywordFilter]:
        """Fetch keyword filters for a module."""
        query = select(CalendarKeywordFilter).where(
            CalendarKeywordFilter.module_id == module_id
        )
        
        result = await db_session.execute(query)
        return list(result.scalars().all())
    
    def _event_to_dict(self, event: CalendarEvent) -> dict[str, Any]:
        """Convert CalendarEvent to dictionary."""
        return {
            "id": str(event.id),
            "module_id": str(event.module_id),
            "title": event.title,
            "description": event.description,
            "start_time": event.start_time.isoformat() if event.start_time else None,
            "end_time": event.end_time.isoformat() if event.end_time else None,
            "is_all_day": event.is_all_day,
            "event_type": event.event_type,
            "source": event.source,
            "external_id": event.external_id,
            "source_url": event.source_url,
            "impact": event.impact,
            "currency": event.currency,
            "country": event.country,
            "actual_value": event.actual_value,
            "forecast_value": event.forecast_value,
            "previous_value": event.previous_value,
            "recurrence_rule": event.recurrence_rule,
            "parent_event_id": str(event.parent_event_id) if event.parent_event_id else None,
            "is_active": event.is_active,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "updated_at": event.updated_at.isoformat() if event.updated_at else None,
        }
    
    def _filter_to_dict(self, filter_obj: CalendarKeywordFilter) -> dict[str, Any]:
        """Convert CalendarKeywordFilter to dictionary."""
        return {
            "id": str(filter_obj.id),
            "module_id": str(filter_obj.module_id),
            "keyword": filter_obj.keyword,
            "is_include": filter_obj.is_include,
            "created_at": filter_obj.created_at.isoformat() if filter_obj.created_at else None,
        }
    
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate calendar config has required fields."""
        # Calendar module has optional config
        # scraped_keywords, default_view, show_weekends
        return True
