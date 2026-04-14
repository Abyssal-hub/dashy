"""Calendar module schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CalendarEventBase(BaseModel):
    """Base calendar event schema."""
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    is_all_day: bool = False
    event_type: Literal["personal", "scraped", "earnings", "economic", "holiday"] = "personal"
    impact: Literal["low", "medium", "high"] | None = None
    currency: str | None = None
    country: str | None = None
    actual_value: str | None = None
    forecast_value: str | None = None
    previous_value: str | None = None
    recurrence_rule: str | None = None


class CalendarEventCreate(CalendarEventBase):
    """Schema for creating a calendar event."""
    pass


class CalendarEventUpdate(BaseModel):
    """Schema for updating a calendar event."""
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_all_day: bool | None = None
    event_type: Literal["personal", "scraped", "earnings", "economic", "holiday"] | None = None
    impact: Literal["low", "medium", "high"] | None = None
    currency: str | None = None
    country: str | None = None
    actual_value: str | None = None
    forecast_value: str | None = None
    previous_value: str | None = None
    recurrence_rule: str | None = None
    is_active: bool | None = None


class CalendarEventResponse(CalendarEventBase):
    """Schema for calendar event response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    module_id: UUID
    source: str
    external_id: str | None = None
    source_url: str | None = None
    parent_event_id: UUID | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CalendarEventListResponse(BaseModel):
    """Schema for list of calendar events."""
    events: list[CalendarEventResponse]
    total: int
    start_date: datetime | None = None
    end_date: datetime | None = None


class CalendarKeywordFilterBase(BaseModel):
    """Base keyword filter schema."""
    keyword: str
    is_include: bool = True


class CalendarKeywordFilterCreate(CalendarKeywordFilterBase):
    """Schema for creating a keyword filter."""
    pass


class CalendarKeywordFilterResponse(CalendarKeywordFilterBase):
    """Schema for keyword filter response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    module_id: UUID
    created_at: datetime


class CalendarKeywordFilterListResponse(BaseModel):
    """Schema for list of keyword filters."""
    filters: list[CalendarKeywordFilterResponse]


class CalendarDataResponse(BaseModel):
    """Schema for calendar module data (returned by handler)."""
    module_id: str
    size: str
    events: list[CalendarEventResponse]
    date_range: dict[str, datetime | None]
    total_events: int
    keyword_filters: list[CalendarKeywordFilterResponse] | None = None
