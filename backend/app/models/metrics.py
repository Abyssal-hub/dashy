import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Float, Numeric, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models import Base


class Metric(Base):
    __tablename__ = "metrics"
    __table_args__ = {"timescaledb_hypertable": {"time_column_name": "time", "chunk_time_interval": "7 days"}}

    time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    metric_name = Column(String(255), nullable=False)
    value = Column(Numeric(24, 8), nullable=False)
    tags = Column(JSONB, default=dict, nullable=False)
    source = Column(String(100), nullable=True)


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    condition_type = Column(String(10), nullable=False)  # gt, lt, gte, lte, eq
    threshold_value = Column(Numeric(24, 8), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    email_override = Column(String(255), nullable=True)

    user = relationship("User", back_populates="alert_rules")
    alert_history = relationship("AlertHistory", back_populates="alert_rule", cascade="all, delete-orphan")


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    triggered_value = Column(Numeric(24, 8), nullable=False)
    message = Column(Text, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    email_sent = Column(Boolean, default=False, nullable=False)
    email_sent_at = Column(DateTime(timezone=True), nullable=True)

    alert_rule = relationship("AlertRule", back_populates="alert_history")


class ScraperConfig(Base):
    __tablename__ = "scraper_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scraper_name = Column(String(100), unique=True, nullable=False)
    keywords = Column(JSONB, default=list, nullable=False)
    schedule_interval = Column(String(50), nullable=False)  # e.g., "5m", "1h"
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_error_message = Column(Text, nullable=True)


class MetricLog(Base):
    __tablename__ = "metric_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    metadata = Column(JSONB, default=dict, nullable=False)
