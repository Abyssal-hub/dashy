"""Log module handler for system log viewing - Now uses file-based logging."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules import ModuleHandler, register
from app.core.file_logger import read_logs, get_severity_counts, APP_LOG_FILE


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
        
        Now reads from file-based logs for performance.
        
        Size buckets:
        - compact: Last 5 log entries summary
        - standard: Last 20 log entries with severity icons
        - expanded: Full log view with filtering (100 entries + pagination)
        
        Args:
            module_id: The module UUID
            size: Display size (compact, standard, expanded)
            db_session: Database session (kept for compatibility, not used)
            severity: Optional filter by severity (INFO, WARN, ERROR)
            source: Optional filter by source
        
        Returns:
            Log data including entries and metadata
        """
        # Determine limit based on size
        limit = self._get_limit_for_size(size)
        
        # Fetch logs from file
        result = read_logs(
            log_file=APP_LOG_FILE,
            severity=severity.upper() if severity else None,
            source=source,
            limit=limit,
            offset=0,
        )
        
        # Get severity counts from file
        severity_counts = get_severity_counts()
        
        # Add color coding for frontend
        for entry in result["logs"]:
            entry["severity_color"] = self._get_severity_color(entry.get("severity", "INFO"))
            entry["created_at"] = entry.get("timestamp")
            entry["metadata"] = entry.get("metadata", {})
        
        # Build response
        return {
            "module_id": module_id,
            "size": size,
            "logs": result["logs"],
            "total": result["total"],
            "filters_applied": {
                "severity": severity,
                "source": source,
            },
            "severity_counts": severity_counts["counts"],
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
) -> None:
    """Write a system log entry to file.
    
    DEPRECATED: Kept for backwards compatibility.
    Use app.core.file_logger.write_log() directly instead.
    
    This function is kept to avoid breaking existing code that calls it.
    It now writes to file instead of database.
    """
    from app.core.file_logger import write_log
    
    write_log(
        severity=severity.upper(),
        message=message,
        source=source,
        metadata=metadata or {},
        module_id=module_id,
    )
