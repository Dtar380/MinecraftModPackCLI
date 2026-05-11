# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from dataclasses import dataclass, field

# === LOCAL ===
from .dependency import Dependency

# ===============================================
#  MOD
# ===============================================
@dataclass(slots=True)
class Mod:

    """
    Represents a Modrinth mod with compatibility metadata
    """

    name: str
    hash: str

    mc_versions: set[str]
    mc_loaders: set[str]

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

        """
        Builds a Mod object from a modrinth retrieved serialized project and version data

        Parameters:
            project_data (dict): Dict with the project data
            version_data (dict): Dict with the version data
            file_name (str): String with the filename of the mod
        """

        # Translate Modrinth project/version payloads into local fields.
        return cls(
            name=project_data["title"],
            hash=version_data["files"][0]["hashes"]["sha1"],
            mc_versions=set(version_data.get("game_versions", [])),
            mc_loaders=set(version_data.get("loaders", [])),
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

        """
        Creates a Mod object from a dict

        Parameters:
            mod (dict): dict containing data for a mod

        Returns:
            Mod: Mod object
        """

        # Manifest data uses a "source" field to mark dependencies.
        return cls(
            name=mod["name"],
            hash=mod["hash"],
            mc_versions=set(mod.get("mc_versions", [])),
            mc_loaders=set(mod.get("mc_loaders", [])),
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

        """
        Determines whether a project is classified as a library

        Parameters:
            project_data (dict): Modrinth project data

        Returns:
            bool: True when the project is a library
        """

        # Treat common library categories as non-seed mods.
        categories = project_data.get("categories", [])
        return any(c in ["library", "api", "framework"] for c in categories)

    @property
    def client_required(self) -> bool:

        """
        Returns true when the mod supports the client side
        """

        return self.client_side != "unsupported"

    @property
    def server_required(self) -> bool:

        """
        Returns true when the mod requires server installation
        """

        return self.server_side == "required"

    def __str__(self) -> str:

        """
        Returns a readable identifier for the mod
        """

        return f"{self.name}: version_id={self.version_id}"

    def to_dict(self) -> dict:

        """
        Gives a dict with the data of the Mod object

        Returns:
            dict: Dict with all the Mod data
        """

        # Sort sets to keep JSON output deterministic.
        return {
            "name": self.name,
            "hash": self.hash,
            "mc_versions": sorted(self.mc_versions),
            "mc_loaders": sorted(self.mc_loaders),
            "project_id": self.project_id,
            "version_id": self.version_id,
            "client_side": self.client_side,
            "server_side": self.server_side,
            "file_name": self.file_name,
            "url": self.url,
            "source": "dependency" if self.is_library else "seed",
            "dependencies": [dep.to_dict() for dep in self.dependencies]
        }
