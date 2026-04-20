"""File-based logging utility for application logs.

Provides structured JSON line logging to files with automatic rotation.
Replaces database logging for performance and simplicity.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Any
from uuid import uuid4

# Default log directory - use project-local path for CI compatibility
# Override with LOG_DIR env var if needed
LOG_DIR = Path(os.getenv("LOG_DIR", "./logs"))

# Log files
APP_LOG_FILE = LOG_DIR / "app.log"
INTERACTION_LOG_FILE = LOG_DIR / "interactions.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"

# Retention days
RETENTION_DAYS = 7


def _ensure_log_dir():
    """Ensure log directory exists (called before writing, not at import)."""
    global LOG_DIR, APP_LOG_FILE, INTERACTION_LOG_FILE, ERROR_LOG_FILE
    # Ensure LOG_DIR is a Path object
    if isinstance(LOG_DIR, str):
        LOG_DIR = Path(LOG_DIR)
        APP_LOG_FILE = LOG_DIR / "app.log"
        INTERACTION_LOG_FILE = LOG_DIR / "interactions.log"
        ERROR_LOG_FILE = LOG_DIR / "errors.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def write_log(
    severity: Literal["INFO", "WARN", "ERROR"],
    message: str,
    source: str = "system",
    metadata: dict[str, Any] | None = None,
    module_id: str | None = None,
) -> dict[str, Any]:
    """Write a log entry to the application log file.
    
    Args:
        severity: Log level (INFO, WARN, ERROR)
        message: Log message
        source: Source of the log (api, frontend, scheduler, etc.)
        metadata: Optional additional data
        module_id: Optional associated module ID
    
    Returns:
        The log entry that was written
    """
    _ensure_log_dir()
    
    entry = {
        "id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "message": message,
        "source": source,
        "metadata": metadata or {},
        "module_id": module_id,
    }
    
    # Write to main app log
    with open(APP_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    # Also write to severity-specific log for quick access
    if severity == "ERROR":
        with open(ERROR_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    return entry


def write_interaction_log(
    interaction_id: str,
    session_id: str,
    user_id: str,
    interaction_type: str,
    element: str,
    component: str,
    duration_ms: int | None,
    success: bool,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write a frontend interaction log.
    
    Args:
        interaction_id: Unique interaction identifier
        session_id: User session identifier
        user_id: User identifier
        interaction_type: Type of interaction (click, hover, etc.)
        element: Target element
        component: Target component
        duration_ms: Interaction duration in milliseconds
        success: Whether the interaction succeeded
        error: Optional error message
        metadata: Optional additional data
    
    Returns:
        The log entry that was written
    """
    _ensure_log_dir()
    
    # Determine severity based on outcome
    if not success:
        severity = "ERROR"
    elif duration_ms and duration_ms > 5000:
        severity = "WARN"
    else:
        severity = "INFO"
    
    entry = {
        "id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "interaction_id": interaction_id,
        "session_id": session_id,
        "user_id": user_id,
        "type": interaction_type,
        "target": {
            "element": element,
            "component": component,
        },
        "duration_ms": duration_ms,
        "success": success,
        "error": error,
        "metadata": metadata or {},
    }
    
    # Write to interaction log file
    with open(INTERACTION_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    # Also write to main app log with simplified message
    message = f"UI {interaction_type}: {element} in {component}"
    if duration_ms:
        message += f" - {duration_ms}ms"
    if error:
        message += f" - Error: {error}"
    
    write_log(
        severity=severity,
        message=message,
        source="frontend",
        metadata={
            "interaction_id": interaction_id,
            "session_id": session_id,
            "duration_ms": duration_ms,
            "success": success,
        },
    )
    
    return entry


def read_logs(
    log_file: Path | None = None,
    severity: Literal["INFO", "WARN", "ERROR"] | None = None,
    source: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """Read logs from a log file with optional filtering.
    
    Args:
        log_file: Path to the log file to read (defaults to current APP_LOG_FILE)
        severity: Filter by severity level
        source: Filter by source
        limit: Maximum number of logs to return
        offset: Number of logs to skip
    
    Returns:
        Dict with logs list, total count, and pagination info
    """
    # Resolve default at call time to respect test fixtures
    if log_file is None:
        log_file = APP_LOG_FILE
    
    if not log_file.exists():
        return {
            "logs": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
        }
    
    logs = []
    with open(log_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                # Apply filters
                if severity and entry.get("severity") != severity:
                    continue
                if source and entry.get("source") != source:
                    continue
                logs.append(entry)
            except json.JSONDecodeError:
                continue
    
    # Reverse to get newest first
    logs.reverse()
    
    total = len(logs)
    
    # Apply pagination
    paginated = logs[offset:offset + limit]
    
    return {
        "logs": paginated,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def get_severity_counts(days: int = 7) -> dict[str, Any]:
    """Get count of logs by severity for the specified period.
    
    Args:
        days: Number of days to look back
    
    Returns:
        Dict with period info and severity counts
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    counts = {"INFO": 0, "WARN": 0, "ERROR": 0}
    
    if Path(APP_LOG_FILE).exists():
        with open(APP_LOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                    if entry_time >= cutoff:
                        severity = entry.get("severity")
                        if severity in counts:
                            counts[severity] += 1
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue
    
    return {
        "period_days": days,
        "cutoff_date": cutoff.isoformat(),
        "counts": counts,
        "total": sum(counts.values()),
    }


def cleanup_old_logs():
    """Remove log entries older than RETENTION_DAYS."""
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    
    for log_file in [APP_LOG_FILE, INTERACTION_LOG_FILE, ERROR_LOG_FILE]:
        if not Path(log_file).exists():
            continue
        
        # Read all entries
        valid_entries = []
        with open(log_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                    if entry_time >= cutoff:
                        valid_entries.append(line)
                except (json.JSONDecodeError, ValueError, KeyError):
                    # Keep malformed lines just in case
                    valid_entries.append(line)
        
        # Rewrite file with only valid entries
        with open(log_file, "w") as f:
            for entry in valid_entries:
                f.write(entry + "\n")


def _get_severity_color(severity: str) -> str:
    """Get color code for severity level."""
    colors = {
        "INFO": "blue",
        "WARN": "orange",
        "ERROR": "red",
    }
    return colors.get(severity, "gray")
