"""
Logging utilities for console and file output
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum, Enum
from pathlib import Path
from typing import Any, Optional

# ===============================================
#  ENUMS
# ===============================================
class LogLevel(IntEnum):

    """
    Log severity levels
    """

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40


class LogTarget(str, Enum):

    """
    Log output targets
    """

    CONSOLE = "console"
    FILE = "file"
    BOTH = "both"

# ===============================================
#  DATACLASS
# ===============================================
@dataclass(slots=True)
class LogRecord:

    """
    Normalized log record container
    """

    level: LogLevel
    message: str
    time: str
    context: dict[str, Any] = field(default_factory=dict)
    exc: Optional[Exception] = None

# ===============================================
#  LOGGER
# ===============================================
class Logger:

    """
    Simple logger that writes to console and/or file
    """

    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        target: LogTarget = LogTarget.BOTH,
        file_path: Optional[Path] = None
    ) -> None:

        """
        Initializes the logger

        Parameters:
            level (LogLevel): Minimum log level
            target (LogTarget): Output target
            file_path (Optional[Path]): Optional log file path
        """

        self.level = level
        self.target = target
        self.file_path = file_path or None
        if self.file_path:
            self.file_path.touch(exist_ok=True)

    def debug(
        self, message: str, *, context: Optional[dict[str, Any]] = None
    ) -> None:

        """
        Writes a debug log entry

        Parameters:
            message (str): Log message
            context (Optional[dict[str, Any]]): Context metadata
        """

        self._log(LogLevel.DEBUG, message, context=context)

    def info(
        self, message: str, *, context: Optional[dict[str, Any]] = None
    ) -> None:

        """
        Writes an info log entry

        Parameters:
            message (str): Log message
            context (Optional[dict[str, Any]]): Context metadata
        """

        self._log(LogLevel.INFO, message, context=context)

    def warning(
        self, message: str, *, context: Optional[dict[str, Any]] = None
    ) -> None:

        """
        Writes a warning log entry

        Parameters:
            message (str): Log message
            context (Optional[dict[str, Any]]): Context metadata
        """

        self._log(LogLevel.WARNING, message, context=context)

    def error(
        self,
        message: str,
        *,
        context: Optional[dict[str, Any]] = None,
        exc: Optional[Exception] = None,
    ) -> None:

        """
        Writes an error log entry

        Parameters:
            message (str): Log message
            context (Optional[dict[str, Any]]): Context metadata
            exc (Optional[Exception]): Optional exception
        """

        self._log(LogLevel.ERROR, message, context=context, exc=exc)

    def _log(
        self,
        level: LogLevel,
        message: str,
        *,
        context: Optional[dict[str, Any]] = None,
        exc: Optional[Exception] = None,
    ) -> None:

        """
        Writes a log entry when it meets the configured threshold

        Parameters:
            level (LogLevel): Log severity level
            message (str): Log message
            context (Optional[dict[str, Any]]): Context metadata
            exc (Optional[Exception]): Optional exception
        """

        if level < self.level:
            return

        record = LogRecord(
            level=level,
            message=message,
            time=datetime.now().strftime("%H-%M-%S"),
            context=context or {},
            exc=exc,
        )
        line = self._format(record)

        if self.target in (LogTarget.CONSOLE, LogTarget.BOTH):
            print(line)

        if self.target in (LogTarget.FILE, LogTarget.BOTH):
            if not self.file_path:
                return
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def _format(self, record: LogRecord) -> str:

        """
        Formats a log record for output

        Parameters:
            record (LogRecord): Log record data

        Returns:
            str: Formatted log line
        """

        context = (
            " " + " ".join(f"{k}={v}" for k, v in record.context.items())
            if record.context
            else ""
        )
        return f"[{record.time}] [{record.level.name}] {record.message}{context}"
