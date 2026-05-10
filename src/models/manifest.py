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

    created_at: datetime = field(default=datetime.now())

    mods: list[Mod] = field(default_factory=list)

    @staticmethod
    def _pick_version(versions: list[str]) -> str:
        if not versions:
            raise RuntimeError("No compatible versions found")
        return sorted(versions, key=lambda v: [int(p) for p in v.split(".") if p.isdigit()])[-1]

    @staticmethod
    def _pick_loader(loaders: list[str]) -> str:
        if not loaders:
            raise RuntimeError("No compatible loaders found")
        if "fabric" in loaders:
            return "fabric"
        return sorted(loaders)[0]

    @classmethod
    def from_dict(cls, manifest: dict) -> Manifest:
        return cls(
            name=manifest["name"],
            version=manifest["version"],
            side=manifest["side"],
            mc_version=manifest.get("mc_version")
            or cls._pick_version(manifest.get("mc_versions", [])),
            mc_loader=manifest.get("mc_loader")
            or cls._pick_loader(manifest.get("mc_loaders", [])),
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
