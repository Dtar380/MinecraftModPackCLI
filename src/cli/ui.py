from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from click import secho, style  # type: ignore


class UILevel(str, Enum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    SUCCESS = "success"


@dataclass(slots=True)
class UIMessage:
    level: UILevel
    text: str


class UI:

    def _tag(self, level: UILevel) -> str:
        color = {
            UILevel.INFO: "blue",
            UILevel.WARN: "yellow",
            UILevel.ERROR: "red",
            UILevel.SUCCESS: "green",
        }[level]
        return style(f"[{level.name}]", fg=color, bold=True)

    def info(self, text: str) -> None:
        secho(f"{self._tag(UILevel.INFO)} {text}", nl=True)

    def warn(self, text: str) -> None:
        secho(f"{self._tag(UILevel.WARN)} {text}", nl=True)

    def error(self, text: str) -> None:
        secho(f"{self._tag(UILevel.ERROR)} {text}", nl=True)

    def success(self, text: str) -> None:
        secho(f"{self._tag(UILevel.SUCCESS)} {text}", nl=True)

    def stage(self, name: str) -> None:
        secho(f"{style('[STAGE]', fg='cyan', bold=True)} {name}")

    def done(self, name: str) -> None:
        secho(f"{style('[DONE]', fg='green', bold=True)} {name}")

    def summary(self, lines: Iterable[str]) -> None:
        secho("")
        for line in lines:
            secho(f"{style('[SUMMARY]', fg='white', bold=True)} {line}")
