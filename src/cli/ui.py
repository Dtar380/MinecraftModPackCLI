"""
Terminal UI helpers for stage progress bars and message output
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from enum import Enum
from typing import Iterable, Optional
import sys

# === LOCAL ===
from ..models.config import UIConfig


# ===============================================
#  ENUMS
# ===============================================
class UILevel(str, Enum):

    """
    Enumerates UI message levels
    """

    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    SUCCESS = "success"


# ===============================================
#  UI
# ===============================================
class UI:

    """
    Helper for CLI status output and spinners
    """

    def __init__(self, config: UIConfig) -> None:

        """
        Initializes the UI state

        Parameters:
            config (UIConfig): Configuration for bar widths, labels, and progress
                display settings
        """

        self._config = config

        self._current_stage: Optional[str] = None
        self._bar_active = False
        self._last_progress: float = 0.0
        self._last_render_len = 0
        self._bar_drawn = False

    def _bar(self, progress: float) -> str:

        """
        Builds an ASCII progress bar

        Parameters:
            progress (float): Progress between 0.0 and 1.0

        Returns:
            str: Rendered bar string
        """

        progress = min(max(progress, 0.0), 1.0)
        filled = int(self._config.bar_width * progress)
        empty = self._config.bar_width - filled
        return f"[{'#' * filled}{'-' * empty}] {int(progress * 100)}%"

    def _stage_line(self, label: str, progress: float) -> str:

        """
        Renders a stage line with progress

        Parameters:
            label (str): Stage label
            progress (float): Progress between 0.0 and 1.0

        Returns:
            str: Rendered stage line
        """

        return f"[STAGE] {label.ljust(self._config.label_width)} {self._bar(progress)}"

    def is_bar_active(self) -> bool:

        """
        Returns true when a progress bar is active

        Returns:
            bool: True when a stage progress bar is currently being rendered
        """

        return self._bar_active

    def clear_bar_line(self) -> None:

        """
        Clears the current bar line from the terminal
        """

        if not self._bar_active:
            return
        sys.stdout.write("\r" + (" " * self._last_render_len) + "\r")
        sys.stdout.flush()
        self._bar_drawn = False

    def redraw_bar(self) -> None:

        """
        Reprints the active bar line
        """

        if not self._bar_active:
            return
        label = self._current_stage or "Working"
        line = self._stage_line(label, self._last_progress)
        padding = max(self._last_render_len - len(line), 0)
        sys.stdout.write("\r" + line + (" " * padding))
        sys.stdout.flush()
        self._last_render_len = len(line)
        self._bar_drawn = True

    def _write(self, level: UILevel, text: str) -> None:

        """
        Writes a formatted message to the console or spinner

        Parameters:
            level (UILevel): Message severity level
            text (str): Message text
        """

        # Build a consistent tag prefix for all UI messages.
        tag = f"[{level.name}]"
        msg = f"{tag} {text}" if text else tag
        if self._config.enable_progress and self._bar_active:
            self.clear_bar_line()
            print(msg)
            self.redraw_bar()
        else:
            print(msg)

    def stage(self, name: str) -> None:

        """
        Starts a new stage spinner

        Parameters:
            name (str): Stage label
        """

        # Ensure only one stage is active at a time.
        if self._bar_active:
            self.fail()

        self._current_stage = name
        self._bar_active = True
        self._last_progress = 0.0
        self._last_render_len = 0
        self._bar_drawn = False

    def progress(
        self, current: int, total: int, message: Optional[str] = None
    ) -> None:

        """
        Updates the progress bar for the active stage

        Parameters:
            current (int): Current progress value
            total (int): Total progress value
            message (Optional[str]): Optional label override
        """

        if not self._bar_active or total <= 0:
            return

        progress = min(max(current / total, 0.0), 1.0)
        if progress < self._last_progress:
            progress = self._last_progress

        self._last_progress = progress
        label = message or (self._current_stage or "Working")
        line = self._stage_line(label, progress)
        padding = max(self._last_render_len - len(line), 0)
        sys.stdout.write("\r" + line + (" " * padding))
        sys.stdout.flush()
        self._last_render_len = len(line)
        self._bar_drawn = True

    def done(self, message: Optional[str] = None) -> None:

        """
        Marks the current stage as successful

        Parameters:
            message (Optional[str]): Optional completion message
        """

        # No active stage means there is nothing to finalize.
        if not self._bar_active:
            return

        text = message or (self._current_stage or "Done")
        line = f"[DONE]  {text.ljust(self._config.label_width)} {self._bar(1.0)}"
        padding = max(self._last_render_len - len(line), 0)
        sys.stdout.write("\r" + line + (" " * padding) + "\n")
        self._bar_active = False
        self._current_stage = None
        self._last_render_len = 0
        self._bar_drawn = False

    def fail(self, message: Optional[str] = None) -> None:

        """
        Marks the current stage as failed

        Parameters:
            message (Optional[str]): Optional failure message
        """

        # No active stage means there is nothing to finalize.
        if not self._bar_active:
            return
        text = message or (self._current_stage or "Failed")
        line = f"[FAIL]  {text.ljust(self._config.label_width)} {self._bar(0.0)}"
        padding = max(self._last_render_len - len(line), 0)
        sys.stdout.write("\r" + line + (" " * padding) + "\n")
        self._bar_active = False
        self._current_stage = None
        self._last_render_len = 0
        self._bar_drawn = False

    def info(self, text: str) -> None:

        """
        Writes an info message

        Parameters:
            text (str): Message text
        """

        self._write(UILevel.INFO, text)

    def warn(self, text: str) -> None:

        """
        Writes a warning message

        Parameters:
            text (str): Message text
        """

        self._write(UILevel.WARN, text)

    def error(self, text: str) -> None:

        """
        Writes an error message

        Parameters:
            text (str): Message text
        """

        self._write(UILevel.ERROR, text)

    def success(self, text: str) -> None:

        """
        Writes a success message

        Parameters:
            text (str): Message text
        """

        self._write(UILevel.SUCCESS, text)

    def summary(self, lines: Iterable[str]) -> None:

        """
        Writes a summary header and list of lines

        Parameters:
            lines (Iterable[str]): Summary lines to print
        """

        self._write(UILevel.INFO, "SUMMARY")
        # Emit each summary line as a separate message for clarity.
        for line in lines:
            self._write(UILevel.INFO, f"- {line}")
