from __future__ import annotations

from dataclasses import dataclass, field

from .dependency import Dependency


@dataclass(slots=True)
class Mod:

    name: str
    hash: str

    mc_version: str
    mc_loader: str

    project_id: str
    version_id: str

    client_side: str
    server_side: str

    file_name: str
    url: str

    is_library: bool

    dependencies: list[Dependency] = field(default_factory=list)

    @classmethod
    def from_modrinth(
        cls, project_data: dict, version_data: dict, file_name: str
    ) -> Mod:
        return cls(
            name=project_data["title"],
            hash=version_data["files"][0]["hashes"]["sha1"],
            mc_version=version_data["game_versions"][0],
            mc_loader=version_data["loaders"][0],
            project_id=project_data["id"],
            version_id=version_data["id"],
            client_side=project_data["client_side"],
            server_side=project_data["server_side"],
            file_name=file_name,
            url=version_data["files"][0]["url"],
            is_library=cls.__is_library(project_data),
            dependencies=[
                Dependency.from_dict(dep)
                for dep in version_data.get("dependencies", [])
            ],
        )

    @classmethod
    def from_dict(cls, mod: dict) -> Mod:
        return cls(
            name=mod["name"],
            hash=mod["hash"],
            mc_version=mod["mc_version"],
            mc_loader=mod["mc_loader"],
            project_id=mod["project_id"],
            version_id=mod["version_id"],
            client_side=mod["client_side"],
            server_side=mod["server_side"],
            file_name=mod["file_name"],
            url=mod["url"],
            is_library=True if mod["source"] == "dependency" else False,
            dependencies=[
                Dependency.from_dict(dep)
                for dep in mod.get("dependencies", [])
            ],
        )

    @classmethod
    def __is_library(cls, project_data: dict) -> bool:
        categories = project_data.get("categories", [])
        return any(c in ["library", "api", "framework"] for c in categories)

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
            "mc_version": self.mc_version,
            "mc_loader": self.mc_loader,
            "project_id": self.project_id,
            "version_id": self.version_id,
            "client_side": self.client_side,
            "server_side": self.server_side,
            "file_name": self.file_name,
            "url": self.url,
            "source": "dependency" if self.is_library else "seed",
            "dependencies": [dep.to_dict() for dep in self.dependencies]
        }
