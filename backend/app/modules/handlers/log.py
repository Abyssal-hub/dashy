"""Log module handler for system log viewing."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules import ModuleHandler, register
from app.models.log import SystemLog


@register("log")
class LogHandler(ModuleHandler):
    """Handler for system log viewing modules."""
    
    @property
    def module_type(self) -> str:
        return "log"
    
    async def get_data(
        self, 
        module_id: str, 
        size: str,
        db_session: AsyncSession | None = None,
        severity: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        """Return system log entries based on size preset.
        
        Size buckets:
        - compact: Last 5 log entries summary
        - standard: Last 20 log entries with severity icons
        - expanded: Full log view with filtering (100 entries + pagination)
        
        Args:
            module_id: The module UUID
            size: Display size (compact, standard, expanded)
            db_session: Database session for queries
            severity: Optional filter by severity (INFO, WARN, ERROR)
            source: Optional filter by source
        
        Returns:
            Log data including entries and metadata
        """
        if db_session is None:
            # Return placeholder if no session available
            return {
                "module_id": module_id,
                "size": size,
                "logs": [],
                "total": 0,
                "filters_applied": {
                    "severity": severity,
                    "source": source,
                },
                "severity_counts": {"INFO": 0, "WARN": 0, "ERROR": 0},
                "retention_days": 7,
            }
        
        # Determine limit based on size
        limit = self._get_limit_for_size(size)
        
        # Fetch logs
        logs = await self._fetch_logs(
            db_session,
            limit=limit,
            severity=severity,
            source=source,
        )
        
        # Get severity counts
        severity_counts = await self._get_severity_counts(db_session)
        
        # Build response
        return {
            "module_id": module_id,
            "size": size,
            "logs": [self._log_to_dict(log) for log in logs],
            "total": len(logs),
            "filters_applied": {
                "severity": severity,
                "source": source,
            },
            "severity_counts": severity_counts,
            "retention_days": 7,  # Per ARCHITECTURE.md
        }
    
    def _get_limit_for_size(self, size: str) -> int:
        """Get the number of log entries to fetch based on size."""
        size_limits = {
            "compact": 5,
            "small": 5,
            "standard": 20,
            "medium": 20,
            "expanded": 100,
            "large": 100,
        }
        return size_limits.get(size, 20)
    
    async def _fetch_logs(
        self,
        db_session: AsyncSession,
        limit: int,
        severity: str | None = None,
        source: str | None = None,
    ) -> list[SystemLog]:
        """Fetch system logs with optional filtering.
        
        Returns logs in reverse chronological order (newest first).
        """
        query = select(SystemLog)
        
        # Apply severity filter if provided
        if severity:
            query = query.where(SystemLog.severity == severity.upper())
        
        # Apply source filter if provided
        if source:
            query = query.where(SystemLog.source == source)
        
        # Order by created_at descending (newest first)
        query = query.order_by(desc(SystemLog.created_at))
        
        # Apply limit
        query = query.limit(limit)
        
        result = await db_session.execute(query)
        return list(result.scalars().all())
    
    async def _get_severity_counts(self, db_session: AsyncSession) -> dict[str, int]:
        """Get count of logs by severity level."""
        # Calculate cutoff for 7-day retention
        cutoff = datetime.utcnow() - timedelta(days=7)
        
        query = select(SystemLog.severity, SystemLog.id).where(SystemLog.created_at >= cutoff)
        result = await db_session.execute(query)
        logs = result.scalars().all()
        
        # Count by severity using a simple query
        severity_query = select(SystemLog.severity).where(SystemLog.created_at >= cutoff)
        severity_result = await db_session.execute(severity_query)
        severities = severity_result.scalars().all()
        
        counts = {"INFO": 0, "WARN": 0, "ERROR": 0}
        for sev in severities:
            if sev in counts:
                counts[sev] += 1
        
        return counts
    
    def _log_to_dict(self, log: SystemLog) -> dict[str, Any]:
        """Convert SystemLog to dictionary."""
        return {
            "id": str(log.id),
            "severity": log.severity,
            "message": log.message,
            "source": log.source,
            "metadata": log.extra_data,
            "module_id": str(log.module_id) if log.module_id else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            # Add color coding hint for frontend
            "severity_color": self._get_severity_color(log.severity),
        }
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color code for severity level (for frontend display)."""
        colors = {
            "INFO": "blue",
            "WARN": "orange",
            "ERROR": "red",
        }
        return colors.get(severity, "gray")
    
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate log module config.
        
        Log module supports optional config for:
        - default_severity: Filter logs by severity by default
        - default_source: Filter logs by source by default
        - auto_refresh: Enable/disable auto refresh
        """
        # All config is optional for log module
        valid_keys = {"default_severity", "default_source", "auto_refresh", "max_entries"}
        
        # Check for invalid keys
        for key in config.keys():
            if key not in valid_keys:
                return False
        
        # Validate severity if provided
        if "default_severity" in config:
            severity = config["default_severity"]
            if severity not in {"INFO", "WARN", "ERROR", None}:
                return False
        
        return True


async def write_system_log(
    db_session: AsyncSession,
    severity: str,
    message: str,
    source: str = "system",
    metadata: dict | None = None,
    module_id: str | None = None,
) -> SystemLog:
    """Write a system log entry to the database.
    
    This function is used by other parts of the application to log
    critical events that should be viewable in the log module.
    
    Args:
        db_session: Database session
        severity: Log severity (INFO, WARN, ERROR)
        message: Log message
        source: Log source (e.g., "ingest", "api", "scheduler")
        metadata: Optional JSON-serializable metadata
        module_id: Optional associated module ID
    
    Returns:
        The created SystemLog entry
    """
    log_entry = SystemLog(
        severity=severity.upper(),
        message=message,
        source=source,
        extra_data=metadata or {},
        module_id=module_id,
    )
    
    db_session.add(log_entry)
    await db_session.commit()
    await db_session.refresh(log_entry)
    
    return log_entry
