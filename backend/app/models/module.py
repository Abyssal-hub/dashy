import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Integer, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.portfolio import Asset
    from app.models.calendar import CalendarEvent


class Module(Base):
    """Module instance model for dashboard widgets."""
    
    __tablename__ = "modules"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    module_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Visual layout
    size: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    position_x: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    position_y: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Behavior
    refresh_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Timestamps
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
    user = relationship("User", back_populates="modules")
    assets = relationship("Asset", back_populates="module", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="module", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Module(id={self.id}, type={self.module_type}, name={self.name})>"
