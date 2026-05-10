# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from enum import Enum
from typing import Iterable, Optional

# === EXTERNAL ===
from yaspin import yaspin  # type: ignore
from yaspin.core import Yaspin  # type: ignore

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

    def __init__(self) -> None:

        """
        Initializes the UI state
        """

        self._spinner: Optional[Yaspin] = None
        self._current_stage: Optional[str] = None

    def _write(self, level: UILevel, text: str) -> None:

        """
        Writes a formatted message to the console or spinner

        Parameters:
            level (UILevel): Message severity level
            text (str): Message text
        """

        tag = f"[{level.name}]"
        msg = f"{tag} {text}" if text else tag

        if self._spinner:
            self._spinner.write(msg)
        else:
            print(msg)

    def stage(self, name: str) -> None:

        """
        Starts a new stage spinner

        Parameters:
            name (str): Stage label
        """

        if self._spinner:
            self._spinner.stop()

        self._current_stage = name
        self._spinner = yaspin(color="cyan", text=f"[STAGE] {name}")
        self._spinner.start()

    def done(self, message: Optional[str] = None) -> None:

        """
        Marks the current stage as successful

        Parameters:
            message (Optional[str]): Optional completion message
        """

        if not self._spinner:
            return

        text = message or (self._current_stage or "Done")
        self._spinner.ok("✔")
        self._spinner.write(f"[DONE] {text}")
        self._spinner.stop()
        self._spinner = None
        self._current_stage = None

    def fail(self, message: Optional[str] = None) -> None:

        """
        Marks the current stage as failed

        Parameters:
            message (Optional[str]): Optional failure message
        """

        if not self._spinner:
            return
        text = message or (self._current_stage or "Failed")
        self._spinner.fail("✗")
        self._spinner.write(f"[FAIL] {text}")
        self._spinner.stop()
        self._spinner = None
        self._current_stage = None

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
        for line in lines:
            self._write(UILevel.INFO, f"- {line}")
