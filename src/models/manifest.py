from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .mod import Mod


@dataclass(slots=True)
class Manifest:
    name: str
    version: str

    side: str

    mc_version: str
    mc_loader: str

    created_at: datetime

    mods: list[Mod] = field(default_factory=list)

    @classmethod
    def from_dict(cls, manifest: dict) -> Manifest:
        return cls(
            name=manifest["name"],
            version=manifest["version"],
            side=manifest["side"],
            mc_version=manifest["mc_version"],
            mc_loader=manifest["mc_loader"],
            created_at=datetime.fromisoformat(manifest["created_at"]),
            mods=[Mod.from_dict(mod) for mod in manifest.get("mods", [])],
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "side": self.side,
            "mc_version": self.mc_version,
            "mc_loader": self.mc_loader,
            "created_at": self.created_at.isoformat(),
            "mods": [mod.to_dict() for mod in self.mods]
        }
