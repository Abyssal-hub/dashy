import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    source = Column(String(50), default="manual", nullable=False)  # manual | scraped | imported
    external_id = Column(String(255), nullable=True, index=True)
    scraped_keywords = Column(JSONB, default=list, nullable=False)

    user = relationship("User", back_populates="calendar_events")


class AssetType(Base):
    __tablename__ = "asset_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type_name = Column(String(50), unique=True, nullable=False)

    portfolio_positions = relationship("PortfolioPosition", back_populates="asset_type")


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type_id = Column(UUID(as_uuid=True), ForeignKey("asset_types.id", ondelete="RESTRICT"), nullable=False, index=True)
    symbol = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    quantity = Column(Numeric(24, 8), nullable=False, default=0)
    avg_cost_basis = Column(Numeric(24, 8), nullable=True)
    current_price = Column(Numeric(24, 8), nullable=True)
    current_value = Column(Numeric(24, 8), nullable=True)
    currency = Column(String(3), default="SGD", nullable=False)
    tags = Column(JSONB, default=list, nullable=False)
    last_updated = Column(DateTime(timezone=True), nullable=True)

    module = relationship("Module", back_populates="portfolio_positions")
    asset_type = relationship("AssetType", back_populates="portfolio_positions")


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    __table_args__ = (
        # Each module can have only one snapshot per day
        {"postgresql_include": ["module_id", "snapshot_date"]},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date = Column(DateTime(timezone=True), nullable=False)
    total_value = Column(Numeric(24, 8), nullable=False)
    display_currency = Column(String(3), default="SGD", nullable=False)

    module = relationship("Module", back_populates="portfolio_snapshots")


class FXRate(Base):
    __tablename__ = "fx_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(24, 8), nullable=False)
    effective_date = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="fx_rates")
