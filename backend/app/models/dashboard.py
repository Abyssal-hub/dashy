import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class DashboardLayout(Base):
    """Dashboard layout configuration for a user."""
    
    __tablename__ = "dashboard_layouts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One layout per user
    )
    
    # Grid configuration
    columns: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    row_height: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    
    # Module positions as JSON array
    # [{"module_id": "...", "x": 0, "y": 0, "w": 3, "h": 2}, ...]
    positions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    
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
    user = relationship("User", back_populates="dashboard_layout")
    
    def __repr__(self) -> str:
        return f"<DashboardLayout(user_id={self.user_id}, modules={len(self.positions)})>"
