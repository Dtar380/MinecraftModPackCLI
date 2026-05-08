from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .dependency import Dependency


@dataclass(slots=True)
class Mod:
    name: str
    hash: str

    project_id: str
    version_id: str

    client_side: bool
    server_side: bool

    file_path: Path

    dependencies: list[Dependency] = field(default_factory=list)

    is_library: bool = False

    @classmethod
    def from_modrinth(
        cls, project_data: dict, version_data: dict, file_path: Path
    ) -> Mod:
        return cls(
            name=project_data["title"],
            hash=version_data["files"][0]["hashes"]["sha1"],
            project_id=project_data["id"],
            version_id=version_data["id"],
            client_side=project_data["client_side"],
            server_side=project_data["server_side"],
            file_path=file_path,
            dependencies=[
                Dependency.from_dict(dep)
                for dep in version_data.get("dependencies", [])
            ],
        )

    @property
    def client_required(self) -> bool:
        return self.client_side != "unsupported"

    @property
    def server_required(self) -> bool:
        return self.server_side == "required"

    def __str__(self) -> str:
        return f"{self.name}: version_id={self.version_id}"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "hash": self.hash,
            "project_id": self.project_id,
            "version_id": self.version_id,
            "client_side": self.client_side,
            "sever": self.server_side,
            "source": "dependency" if self.is_library else "seed",
            "dependencies": [dep.to_dict() for dep in self.dependencies]
        }
