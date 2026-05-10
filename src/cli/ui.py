from __future__ import annotations

from enum import Enum
from typing import Iterable, Optional

from yaspin import yaspin  # type: ignore
from yaspin.core import Yaspin  # type: ignore


class UILevel(str, Enum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    SUCCESS = "success"


class UI:

    def __init__(self) -> None:
        self._spinner: Optional[Yaspin] = None
        self._current_stage: Optional[str] = None

    def _write(self, level: UILevel, text: str) -> None:
        tag = f"[{level.name}]"
        msg = f"{tag} {text}" if text else tag

        if self._spinner:
            self._spinner.write(msg)
        else:
            print(msg)

    def stage(self, name: str) -> None:
        if self._spinner:
            self._spinner.stop()

        self._current_stage = name
        self._spinner = yaspin(color="cyan", text=f"[STAGE] {name}")
        self._spinner.start()

    def done(self, message: Optional[str] = None) -> None:
        if not self._spinner:
            return

        text = message or (self._current_stage or "Done")
        self._spinner.ok("✔")
        self._spinner.write(f"[DONE] {text}")
        self._spinner.stop()
        self._spinner = None
        self._current_stage = None

    def fail(self, message: Optional[str] = None) -> None:
        if not self._spinner:
            return
        text = message or (self._current_stage or "Failed")
        self._spinner.fail("✗")
        self._spinner.write(f"[FAIL] {text}")
        self._spinner.stop()
        self._spinner = None
        self._current_stage = None

    def info(self, text: str) -> None:
        self._write(UILevel.INFO, text)

    def warn(self, text: str) -> None:
        self._write(UILevel.WARN, text)

    def error(self, text: str) -> None:
        self._write(UILevel.ERROR, text)

    def success(self, text: str) -> None:
        self._write(UILevel.SUCCESS, text)

    def summary(self, lines: Iterable[str]) -> None:
        self._write(UILevel.INFO, "SUMMARY")
        for line in lines:
            self._write(UILevel.INFO, f"- {line}")
