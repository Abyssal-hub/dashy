"""Schemas for data ingestion endpoints."""

from datetime import datetime
from typing import Literal, Any

from pydantic import BaseModel, Field


class MetricIngest(BaseModel):
    """Single metric data point for ingestion."""
    metric_name: str = Field(..., description="Metric identifier", max_length=255)
    value: float = Field(..., description="Metric value")
    timestamp: datetime = Field(..., description="Measurement timestamp (ISO 8601)")
    tags: dict[str, Any] = Field(default_factory=dict, description="Additional labels")
    source: str = Field(default="scraper", description="Data source identifier", max_length=100)


class MetricBatchRequest(BaseModel):
    """Batch request for metric ingestion."""
    metrics: list[MetricIngest] = Field(..., description="List of metrics to ingest")


class CalendarEventIngest(BaseModel):
    """Calendar event for ingestion (scraped events)."""
    title: str = Field(..., description="Event title", max_length=255)
    description: str | None = Field(None, description="Event description")
    start_time: datetime = Field(..., description="Event start time (ISO 8601)")
    end_time: datetime | None = Field(None, description="Event end time (ISO 8601)")
    is_all_day: bool = Field(default=False, description="All-day event flag")
    
    # Event classification
    event_type: Literal["economic", "earnings", "holiday", "personal"] = Field(
        default="economic", description="Type of calendar event"
    )
    source: str = Field(default="forex_factory", description="Data source")
    external_id: str | None = Field(None, description="Deduplication key from source")
    source_url: str | None = Field(None, description="Original source URL")
    
    # Economic event details
    impact: Literal["low", "medium", "high"] | None = Field(None, description="Impact level")
    currency: str | None = Field(None, description="Related currency (ISO 4217)", max_length=3)
    country: str | None = Field(None, description="Related country")
    
    # Values for economic indicators
    actual_value: str | None = Field(None, description="Actual/released value")
    forecast_value: str | None = Field(None, description="Forecast/consensus value")
    previous_value: str | None = Field(None, description="Previous period value")


class EventBatchRequest(BaseModel):
    """Batch request for calendar event ingestion."""
    module_id: str | None = Field(None, description="Target calendar module ID (optional)")
    events: list[CalendarEventIngest] = Field(..., description="List of events to ingest")


class IngestResponse(BaseModel):
    """Response from ingest endpoints (202 Accepted)."""
    status: Literal["accepted"] = Field(default="accepted")
    message: str = Field(default="Data queued for processing")
    queued_count: int = Field(..., description="Number of items queued")
    queue: str = Field(default="metrics_queue", description="Queue name")


class IngestErrorResponse(BaseModel):
    """Error response for ingest endpoints."""
    detail: str
    errors: list[dict[str, Any]] | None = None
