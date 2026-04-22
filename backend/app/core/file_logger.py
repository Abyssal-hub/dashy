"""File-based logging utility for application logs.

Provides structured JSON line logging to files with automatic rotation.
Replaces database logging for performance and simplicity.

SECURITY FIXES APPLIED (2026-04-22):
- File locking prevents race conditions between workers
- Message sanitization prevents log injection
- Path traversal protection on LOG_DIR
- Max message length prevents disk fill
- Atomic cleanup prevents data loss
- Async wrappers prevent event loop blocking
"""

import asyncio
import fcntl
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Any
from uuid import uuid4
import contextvars

# Context variable for correlation ID tracking across async calls
correlation_id_var = contextvars.ContextVar("correlation_id", default=None)

# ── Configuration ──────────────────────────────────────────────────────────

# Default log directory - use project-local path for CI compatibility
# Override with LOG_DIR env var if needed
_LOG_DIR_RAW = os.getenv("LOG_DIR", "./logs")
_LOG_DIR = Path(_LOG_DIR_RAW).resolve()

# Security: Restrict log directory to project root or /var/log
_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
_ALLOWED_LOG_PREFIXES = [
    str(_PROJECT_ROOT),
    "/var/log",
    "/tmp",  # Allow tmp for testing
]

# Validate LOG_DIR is within allowed paths
def _resolve_log_dir() -> Path:
    """Resolve and validate log directory path."""
    path = _LOG_DIR
    path_str = str(path)
    for prefix in _ALLOWED_LOG_PREFIXES:
        if path_str.startswith(prefix):
            return path
    # Security fallback: force to project-local logs
    return _PROJECT_ROOT / "logs"

LOG_DIR = _resolve_log_dir()

# Log files
APP_LOG_FILE = LOG_DIR / "app.log"
INTERACTION_LOG_FILE = LOG_DIR / "interactions.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"

# Retention days
RETENTION_DAYS = 7

# Size-based rotation
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
MAX_BACKUP_COUNT = 5

# Message limits
MAX_MESSAGE_LENGTH = 10000  # 10KB max per message

# Log level filtering
MIN_LOG_LEVEL = os.getenv("MIN_LOG_LEVEL", "INFO")
LEVEL_ORDER = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}

# Structured logging context
SERVICE_NAME = os.getenv("SERVICE_NAME", "dashy")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
HOSTNAME = os.getenv("HOSTNAME", "localhost")


# ── Internal Helpers ───────────────────────────────────────────────────────

def _ensure_log_dir():
    """Ensure log directory exists (called before writing, not at import)."""
    global LOG_DIR, APP_LOG_FILE, INTERACTION_LOG_FILE, ERROR_LOG_FILE
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    APP_LOG_FILE = LOG_DIR / "app.log"
    INTERACTION_LOG_FILE = LOG_DIR / "interactions.log"
    ERROR_LOG_FILE = LOG_DIR / "errors.log"


def _sanitize_message(message: str) -> str:
    """Remove newlines and control characters to prevent log injection.
    
    Prevents attackers from injecting fake log entries by including
    newline characters in the message.
    """
    if not isinstance(message, str):
        message = str(message)
    # Replace newlines with spaces to maintain single-line JSON format
    sanitized = message.replace('\n', ' ').replace('\r', ' ').replace('\x00', '')
    return sanitized


def _truncate_message(message: str) -> str:
    """Truncate message to prevent oversized log entries."""
    if len(message) > MAX_MESSAGE_LENGTH:
        return message[:MAX_MESSAGE_LENGTH] + "... [truncated]"
    return message


def _check_log_level(severity: str) -> bool:
    """Check if severity meets minimum log level threshold."""
    return LEVEL_ORDER.get(severity, 1) >= LEVEL_ORDER.get(MIN_LOG_LEVEL, 1)


def _rotate_if_needed(log_file: Path):
    """Rotate log file if it exceeds MAX_LOG_SIZE."""
    if not log_file.exists():
        return
    if log_file.stat().st_size <= MAX_LOG_SIZE:
        return
    
    # Rotate: app.log → app.log.1 → app.log.2, etc.
    for i in range(MAX_BACKUP_COUNT - 1, 0, -1):
        old = Path(f"{log_file}.{i}")
        new = Path(f"{log_file}.{i + 1}")
        if old.exists():
            old.rename(new)
    
    log_file.rename(Path(f"{log_file}.1"))


def _write_json_line(log_file: Path, entry: dict[str, Any]):
    """Write a JSON line to log file with file locking.
    
    Uses fcntl for exclusive file locking to prevent race conditions
    between multiple Uvicorn workers writing to the same file.
    """
    _rotate_if_needed(log_file)
    
    with open(log_file, "a") as f:
        # Acquire exclusive lock
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(json.dumps(entry, default=str) + "\n")
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


# ── Public API ─────────────────────────────────────────────────────────────

def write_log(
    severity: Literal["INFO", "WARN", "ERROR"],
    message: str,
    source: str = "system",
    metadata: dict[str, Any] | None = None,
    module_id: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any] | None:
    """Write a log entry to the application log file.
    
    Args:
        severity: Log level (INFO, WARN, ERROR)
        message: Log message (will be sanitized and truncated)
        source: Source of the log (api, frontend, scheduler, etc.)
        metadata: Optional additional data
        module_id: Optional associated module ID
        correlation_id: Optional request correlation ID
    
    Returns:
        The log entry that was written, or None if filtered by level
    """
    # Filter by log level
    if not _check_log_level(severity):
        return None
    
    _ensure_log_dir()
    
    # Sanitize and truncate message
    safe_message = _truncate_message(_sanitize_message(message))
    
    entry = {
        "id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "message": safe_message,
        "source": source,
        "metadata": metadata or {},
        "module_id": module_id,
        "correlation_id": correlation_id or correlation_id_var.get(),
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "environment": ENVIRONMENT,
        "host": HOSTNAME,
    }
    
    # Write to main app log with locking
    _write_json_line(APP_LOG_FILE, entry)
    
    # Also write to severity-specific log for quick access
    if severity == "ERROR":
        _write_json_line(ERROR_LOG_FILE, entry)
    
    return entry


async def write_log_async(
    severity: Literal["INFO", "WARN", "ERROR"],
    message: str,
    source: str = "system",
    metadata: dict[str, Any] | None = None,
    module_id: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any] | None:
    """Async wrapper for write_log — runs I/O in thread pool.
    
    Use this in FastAPI async endpoints to avoid blocking the event loop.
    """
    return await asyncio.to_thread(
        write_log, severity, message, source, metadata, module_id, correlation_id
    )


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
    
    # Sanitize all string inputs
    safe_element = _sanitize_message(element)
    safe_component = _sanitize_message(component)
    safe_error = _sanitize_message(error) if error else None
    
    entry = {
        "id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "interaction_id": _sanitize_message(interaction_id),
        "session_id": _sanitize_message(session_id),
        "user_id": _sanitize_message(user_id),
        "type": _sanitize_message(interaction_type),
        "target": {
            "element": safe_element,
            "component": safe_component,
        },
        "duration_ms": duration_ms,
        "success": success,
        "error": safe_error,
        "metadata": metadata or {},
    }
    
    # Write to interaction log file with locking
    _write_json_line(INTERACTION_LOG_FILE, entry)
    
    # Also write to main app log with simplified message
    message = f"UI {interaction_type}: {safe_element} in {safe_component}"
    if duration_ms:
        message += f" - {duration_ms}ms"
    if safe_error:
        message += f" - Error: {safe_error}"
    
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


async def write_interaction_log_async(
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
    """Async wrapper for write_interaction_log."""
    return await asyncio.to_thread(
        write_interaction_log,
        interaction_id, session_id, user_id, interaction_type,
        element, component, duration_ms, success, error, metadata
    )


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


async def read_logs_async(
    log_file: Path | None = None,
    severity: Literal["INFO", "WARN", "ERROR"] | None = None,
    source: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """Async wrapper for read_logs."""
    return await asyncio.to_thread(read_logs, log_file, severity, source, limit, offset)


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
                        sev = entry.get("severity")
                        if sev in counts:
                            counts[sev] += 1
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue
    
    return {
        "period_days": days,
        "cutoff_date": cutoff.isoformat(),
        "counts": counts,
        "total": sum(counts.values()),
    }


async def get_severity_counts_async(days: int = 7) -> dict[str, Any]:
    """Async wrapper for get_severity_counts."""
    return await asyncio.to_thread(get_severity_counts, days)


def cleanup_old_logs():
    """Remove log entries older than RETENTION_DAYS.
    
    Uses atomic file replacement to prevent data loss if process crashes
    during cleanup.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    
    for log_file in [APP_LOG_FILE, INTERACTION_LOG_FILE, ERROR_LOG_FILE]:
        if not Path(log_file).exists():
            continue
        
        # Read all valid entries
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
        
        # Atomic replacement: write to temp, then rename
        if valid_entries:
            temp_fd, temp_path = tempfile.mkstemp(dir=log_file.parent)
            try:
                with os.fdopen(temp_fd, 'w') as temp_f:
                    for entry in valid_entries:
                        temp_f.write(entry + "\n")
                os.replace(temp_path, log_file)
            except Exception:
                # Clean up temp file on failure
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise
        else:
            # No valid entries, truncate file
            log_file.write_text("")


async def cleanup_old_logs_async():
    """Async wrapper for cleanup_old_logs."""
    return await asyncio.to_thread(cleanup_old_logs)


def check_log_health() -> dict[str, Any]:
    """Check if log directory is writable.
    
    Returns health status for monitoring/health checks.
    """
    try:
        _ensure_log_dir()
        test_file = LOG_DIR / ".healthcheck"
        test_file.write_text("ok")
        test_file.unlink()
        
        # Check disk space (warn if < 1GB free)
        stat = os.statvfs(LOG_DIR)
        free_bytes = stat.f_bavail * stat.f_frsize
        free_gb = free_bytes / (1024 ** 3)
        
        return {
            "status": "healthy",
            "log_dir": str(LOG_DIR),
            "writable": True,
            "disk_free_gb": round(free_gb, 2),
            "disk_warning": free_gb < 1.0,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "writable": False,
        }


async def check_log_health_async() -> dict[str, Any]:
    """Async wrapper for check_log_health."""
    return await asyncio.to_thread(check_log_health)


def _get_severity_color(severity: str) -> str:
    """Get color code for severity level."""
    colors = {
        "INFO": "blue",
        "WARN": "orange",
        "ERROR": "red",
    }
    return colors.get(severity, "gray")
