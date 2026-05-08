from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .mod import Mod


@dataclass(slots=True)
class Manifest:
    name: str
    version: str

    mc_version: str
    mc_loader: str

    created_at: datetime

    mods: list[Mod] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "mc_version": self.mc_version,
            "mc_loader": self.mc_loader,
            "created_at": self.created_at,
            "mods": [mod.to_dict() for mod in self.mods]
        }
