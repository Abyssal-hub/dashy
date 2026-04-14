"""Calendar event models for economic calendar module."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, DateTime, Text, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.module import Module


class CalendarEvent(Base):
    """Calendar event - can be personal or scraped from external sources."""
    
    __tablename__ = "calendar_events"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Event details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timing
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Event type and source
    event_type: Mapped[str] = mapped_column(String(20), nullable=False, default="personal")
    # personal, scraped, earnings, economic, holiday
    
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    # manual, forex_factory, user_import, etc.
    
    # For scraped events
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Impact level for economic events (low, medium, high)
    impact: Mapped[str | None] = mapped_column(String(10), nullable=True)
    
    # Currency/country for economic events
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Actual/forecast/previous values for economic indicators
    actual_value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    forecast_value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    previous_value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Recurring event support (iCal RRULE)
    recurrence_rule: Mapped[str | None] = mapped_column(String(500), nullable=True)
    parent_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calendar_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    module = relationship("Module", back_populates="calendar_events")
    
    def __repr__(self) -> str:
        return f"<CalendarEvent(title={self.title}, start={self.start_time})>"


class CalendarKeywordFilter(Base):
    """Keywords for filtering scraped calendar events."""
    
    __tablename__ = "calendar_keyword_filters"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    keyword: Mapped[str] = mapped_column(String(100), nullable=False)
    is_include: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # True = include events matching keyword, False = exclude
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    
    def __repr__(self) -> str:
        action = "include" if self.is_include else "exclude"
        return f"<CalendarKeywordFilter({action}={self.keyword})>"
