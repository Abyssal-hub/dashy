"""System log model for log module."""

# NOTE: System logging has been migrated to file-based logging.
# This file is kept for backwards compatibility but the SystemLog and LogEntry
# database models have been removed. All logging is now handled by
# app.core.file_logger which writes structured JSON lines to files.
# 
# See: app.core.file_logger for the new logging architecture.

# Deprecated imports kept for backwards compatibility if any code still imports
# from this module. These will be removed in a future release.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

