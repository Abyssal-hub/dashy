"""System logs API endpoints."""

from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.services.auth.deps import get_current_user
from app.models.log import SystemLog
from app.models.module import Module
from app.modules.handlers.log import LogHandler, write_system_log
from app.schemas.interaction import InteractionLogCreate, InteractionLogResponse

router = APIRouter(prefix="/logs", tags=["logs"])


async def _verify_module_access(
    module_id: UUID,
    user_id: str,
    db_session: AsyncSession,
) -> Module:
    """Verify user has access to the log module."""
    result = await db_session.execute(
        select(Module).where(
            and_(
                Module.id == module_id,
                Module.user_id == user_id,
                Module.module_type == "log",
                Module.is_active == True,
            )
        )
    )
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log module not found",
        )
    
    return module


@router.get("")
async def list_logs(
    module_id: UUID | None = None,
    severity: Literal["INFO", "WARN", "ERROR"] | None = Query(None, description="Filter by severity level"),
    source: str | None = Query(None, description="Filter by log source"),
    limit: int = Query(20, ge=1, le=100, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    user_id: str = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List system logs with optional filtering.
    
    Query parameters:
    - module_id: Filter by specific log module (optional)
    - severity: Filter by severity (INFO, WARN, ERROR)
    - source: Filter by source (e.g., "ingest", "api", "scheduler")
    - limit: Number of logs to return (1-100, default 20)
    - offset: Pagination offset (default 0)
    
    Returns logs in reverse chronological order (newest first).
    """
    # If module_id provided, verify access
    if module_id:
        await _verify_module_access(module_id, user_id, db_session)
    
    # Build query
    query = select(SystemLog)
    
    # Apply filters
    if severity:
        query = query.where(SystemLog.severity == severity.upper())
    if source:
        query = query.where(SystemLog.source == source)
    if module_id:
        query = query.where(SystemLog.module_id == module_id)
    
    # Get total count before pagination
    count_query = query
    count_result = await db_session.execute(count_query)
    total = len(count_result.scalars().all())
    
    # Order by created_at descending (newest first)
    query = query.order_by(desc(SystemLog.created_at))
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    result = await db_session.execute(query)
    logs = result.scalars().all()
    
    # Convert to response format
    log_entries = [
        {
            "id": str(log.id),
            "severity": log.severity,
            "message": log.message,
            "source": log.source,
            "metadata": log.extra_data,
            "module_id": str(log.module_id) if log.module_id else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "severity_color": _get_severity_color(log.severity),
        }
        for log in logs
    ]
    
    return {
        "logs": log_entries,
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters_applied": {
            "severity": severity,
            "source": source,
            "module_id": str(module_id) if module_id else None,
        },
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_log(
    severity: Literal["INFO", "WARN", "ERROR"],
    message: str,
    source: str = "api",
    metadata: dict | None = None,
    module_id: UUID | None = None,
    user_id: str = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new system log entry.
    
    This endpoint is primarily for testing and manual log creation.
    Most logs should be created internally by the application.
    """
    # If module_id provided, verify access
    if module_id:
        await _verify_module_access(module_id, user_id, db_session)
    
    log_entry = await write_system_log(
        db_session=db_session,
        severity=severity,
        message=message,
        source=source,
        metadata={**metadata, "created_by": user_id} if metadata else {"created_by": user_id},
        module_id=str(module_id) if module_id else None,
    )
    
    return {
        "id": str(log_entry.id),
        "severity": log_entry.severity,
        "message": log_entry.message,
        "source": log_entry.source,
        "created_at": log_entry.created_at.isoformat(),
    }


@router.get("/severity-counts")
async def get_severity_counts(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    user_id: str = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get count of logs by severity level for the specified period."""
    from datetime import datetime, timedelta
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Query all logs in the period
    query = select(SystemLog).where(SystemLog.created_at >= cutoff)
    result = await db_session.execute(query)
    logs = result.scalars().all()
    
    # Count by severity
    counts = {"INFO": 0, "WARN": 0, "ERROR": 0}
    for log in logs:
        if log.severity in counts:
            counts[log.severity] += 1
    
    return {
        "period_days": days,
        "cutoff_date": cutoff.isoformat(),
        "counts": counts,
        "total": sum(counts.values()),
    }


@router.post(
    "/interaction",
    response_model=InteractionLogResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Log frontend interaction",
    description="Log a user interaction event from the frontend UI for debugging and analytics.",
)
async def log_interaction(
    log: InteractionLogCreate,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Log a frontend interaction event.
    
    Accepts interaction logs from the frontend UI, assigns appropriate severity
    based on outcome and duration, and stores in system_logs table.
    
    Severity Assignment:
    - ERROR: Failed interaction (success=false)
    - WARN: Slow interaction (duration > 5000ms)
    - INFO: Normal interaction (< 5000ms, success=true)
    """
    from app.schemas.interaction import InteractionLogResponse
    
    # Determine severity based on outcome and duration
    if not log.success:
        severity = "ERROR"
    elif log.duration and log.duration > 5000:
        severity = "WARN"
    else:
        severity = "INFO"
    
    # Build message
    message = f"UI {log.type}: {log.target.element} in {log.target.component}"
    if log.duration:
        message += f" - {log.duration}ms"
    if log.error:
        message += f" - Error: {log.error}"
    
    # Write to system logs
    await write_system_log(
        db_session=db_session,
        severity=severity,
        message=message,
        source="frontend",
        module_id=None,
        metadata={
            "interaction_id": log.interactionId,
            "session_id": log.sessionId,
            "user_id": log.userId,
            "type": log.type,
            "target": log.target.model_dump(),
            "duration_ms": log.duration,
            "success": log.success,
            "error": log.error,
            "metadata": log.metadata,
        },
    )
    
    return InteractionLogResponse(
        status="logged",
        message="Interaction logged successfully",
        interactionId=log.interactionId,
    )


def _get_severity_color(severity: str) -> str:
    """Get color code for severity level."""
    colors = {
        "INFO": "blue",
        "WARN": "orange",
        "ERROR": "red",
    }
    return colors.get(severity, "gray")


# Module-specific endpoints

@router.get("/modules/{module_id}")
async def get_module_logs(
    module_id: UUID,
    size: Literal["compact", "standard", "expanded"] = Query("standard", description="Size preset for log display"),
    severity: Literal["INFO", "WARN", "ERROR"] | None = Query(None, description="Filter by severity"),
    source: str | None = Query(None, description="Filter by source"),
    user_id: str = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get logs for a specific log module using the handler.
    
    This endpoint returns formatted log data ready for module display,
    using the LogHandler to apply size-specific formatting.
    """
    await _verify_module_access(module_id, user_id, db_session)
    
    handler = LogHandler()
    data = await handler.get_data(
        module_id=str(module_id),
        size=size,
        db_session=db_session,
        severity=severity,
        source=source,
    )
    
    return data
