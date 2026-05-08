from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .mod import Mod


@dataclass(slots=True)
class Manifest:
    name: str
    version: str

    mc_version: str
    mc_loader: str

    created_at: datetime

    mods: list[Mod]
