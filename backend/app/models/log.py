"""System log model for log module."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, DateTime, Text, Enum, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.module import Module


class SystemLog(Base):
    """System log entry - stores application logs with severity levels.
    
    Retention: 7 days (per ARCHITECTURE.md Section 7.4, 11.2)
    """
    
    __tablename__ = "system_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Log entry details
    severity: Mapped[str] = mapped_column(
        String(10), 
        nullable=False,
        index=True,
    )
    # INFO, WARN, ERROR
    
    message: Mapped[str] = mapped_column(
        Text, 
        nullable=False
    )
    
    source: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        default="system"
    )
    # e.g., "ingest", "api", "scheduler", "database", "auth"
    
    # Optional metadata as JSON (stored as extra_data to avoid reserved name)
    extra_data: Mapped[dict | None] = mapped_column(
        JSON, 
        nullable=True
    )
    # Additional context like user_id, request_id, stack_trace, etc.
    
    # Optional module_id if log is associated with a specific module
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    
    # Relationships
    module = relationship("Module", back_populates="system_logs")
    
    def __repr__(self) -> str:
        return f"<SystemLog(severity={self.severity}, source={self.source}, message={self.message[:50]}...)>"


class LogEntry(Base):
    """Alias for SystemLog for backwards compatibility with API schemas."""
    
    __table__ = SystemLog.__table__
