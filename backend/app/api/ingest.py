"""Data ingestion endpoints for scraper workers.

Routes:
    POST /ingest/metrics - Batch metric ingestion
    POST /ingest/events - Batch calendar event ingestion

Both endpoints return 202 Accepted immediately and queue data for async processing.
"""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.schemas.ingest import (
    MetricBatchRequest,
    EventBatchRequest,
    IngestResponse,
    IngestErrorResponse,
)
from app.services.redis_client import get_redis_client
from app.services.auth.deps import get_current_user
from app.modules.handlers.log import write_system_log
from app.db.database import get_db_session


router = APIRouter(prefix="/api/ingest", tags=["ingest"])

# Redis queue name per ARCHITECTURE.md Section 8.2
QUEUE_NAME = "metrics_queue"


def serialize_datetime(obj: Any) -> str:
    """Helper to serialize datetime objects to ISO format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


@router.post(
    "/metrics",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"model": IngestResponse, "description": "Metrics queued for processing"},
        400: {"model": IngestErrorResponse, "description": "Validation error"},
        422: {"model": IngestErrorResponse, "description": "Unprocessable entity"},
    },
    summary="Batch ingest metrics",
    description="Accepts a batch of metrics and queues them for async processing. Returns 202 Accepted immediately.",
)
async def ingest_metrics(
    request: MetricBatchRequest,
    current_user: str = Depends(get_current_user),
    db_session = Depends(get_db_session),
) -> IngestResponse:
    """Queue batch of metrics for async processing.
    
    Metrics are queued to Redis and will be processed by the background consumer
    which handles batching (100 messages or 5s timeout) and writes to TimescaleDB.
    """
    redis = get_redis_client()
    
    # Validate and queue each metric
    queued = 0
    errors = []
    
    for idx, metric in enumerate(request.metrics):
        try:
            # Build message with type discriminator
            message = {
                "type": "metric",
                "metric_name": metric.metric_name,
                "value": str(metric.value),  # Numeric as string to preserve precision
                "timestamp": metric.timestamp.isoformat(),
                "tags": metric.tags,
                "source": metric.source,
                "user_id": current_user,
            }
            
            # Push to Redis queue (LPUSH for producer)
            await redis.lpush(QUEUE_NAME, json.dumps(message, default=serialize_datetime))
            queued += 1
            
        except (ValidationError, TypeError, ValueError) as e:
            errors.append({"index": idx, "error": str(e)})
    
    # Partial failure handling
    if errors and queued == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "All metrics failed validation",
                "errors": errors,
            },
        )
    
    # Log successful ingest to system logs
    await write_system_log(
        db_session=db_session,
        severity="INFO",
        message=f"Metrics ingested: {queued} queued for user {current_user}",
        source="ingest",
        metadata={
            "user_id": current_user,
            "metrics_count": queued,
            "errors_count": len(errors),
            "queue": QUEUE_NAME,
        },
    )
    
    return IngestResponse(
        status="accepted",
        message="Metrics queued for processing" + (f" ({len(errors)} failed)" if errors else ""),
        queued_count=queued,
        queue=QUEUE_NAME,
    )


@router.post(
    "/events",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"model": IngestResponse, "description": "Events queued for processing"},
        400: {"model": IngestErrorResponse, "description": "Validation error"},
        422: {"model": IngestErrorResponse, "description": "Unprocessable entity"},
    },
    summary="Batch ingest calendar events",
    description="Accepts a batch of calendar events and queues them for async processing. Returns 202 Accepted immediately.",
)
async def ingest_events(
    request: EventBatchRequest,
    current_user: str = Depends(get_current_user),
    db_session = Depends(get_db_session),
) -> IngestResponse:
    """Queue batch of calendar events for async processing.
    
    Events are queued to Redis and will be processed by the background consumer.
    Scraped events are deduplicated via external_id and written to calendar_events table.
    """
    redis = get_redis_client()
    
    # Determine target module (optional - consumer can auto-assign)
    module_id = request.module_id
    
    # Validate and queue each event
    queued = 0
    errors = []
    
    for idx, event in enumerate(request.events):
        try:
            # Build message with type discriminator
            message: dict[str, Any] = {
                "type": "calendar_event",
                "title": event.title,
                "start_time": event.start_time.isoformat(),
                "is_all_day": event.is_all_day,
                "event_type": event.event_type,
                "source": event.source,
                "user_id": current_user,
            }
            
            # Optional fields - only include if not None
            if event.description:
                message["description"] = event.description
            if event.end_time:
                message["end_time"] = event.end_time.isoformat()
            if event.external_id:
                message["external_id"] = event.external_id
            if event.source_url:
                message["source_url"] = event.source_url
            if event.impact:
                message["impact"] = event.impact
            if event.currency:
                message["currency"] = event.currency
            if event.country:
                message["country"] = event.country
            if event.actual_value:
                message["actual_value"] = event.actual_value
            if event.forecast_value:
                message["forecast_value"] = event.forecast_value
            if event.previous_value:
                message["previous_value"] = event.previous_value
            if module_id:
                message["module_id"] = module_id
            
            # Push to Redis queue (LPUSH for producer)
            await redis.lpush(QUEUE_NAME, json.dumps(message, default=serialize_datetime))
            queued += 1
            
        except (ValidationError, TypeError, ValueError) as e:
            errors.append({"index": idx, "error": str(e)})
    
    # Partial failure handling
    if errors and queued == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "All events failed validation",
                "errors": errors,
            },
        )
    
    # Log successful ingest to system logs
    await write_system_log(
        db_session=db_session,
        severity="INFO",
        message=f"Events ingested: {queued} queued for user {current_user}",
        source="ingest",
        metadata={
            "user_id": current_user,
            "events_count": queued,
            "errors_count": len(errors),
            "queue": QUEUE_NAME,
            "module_id": str(module_id) if module_id else None,
        },
    )
    
    return IngestResponse(
        status="accepted",
        message="Events queued for processing" + (f" ({len(errors)} failed)" if errors else ""),
        queued_count=queued,
        queue=QUEUE_NAME,
    )
