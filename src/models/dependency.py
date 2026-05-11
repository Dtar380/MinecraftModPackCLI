# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from dataclasses import dataclass

from ..utils import errors

# ===============================================
#  DEPENDENCY
# ===============================================
@dataclass(slots=True)
class Dependency:

    """
    Represents a dependency entry from Modrinth metadata
    """

    project_id: str
    version_id: str
    dependency_type: str

    @classmethod
    def from_dict(cls, dependency_data: dict) -> Dependency:

        """
        Loads a Depdency object from a dictionary

        Parameters:
            dependency_data (dict): Data of a dependency in dict format

        Returns:
            Dependency: Dependency object
        """

        # Map Modrinth dependency fields into the dataclass.
        try:
            return Dependency(
                project_id=dependency_data["project_id"],
                version_id=dependency_data["version_id"],
                dependency_type=dependency_data["dependency_type"],
            )
        except (KeyError, TypeError) as exc:
            raise errors.ModpackError(
                "Invalid dependency data",
                cause=exc,
                code="dependency_parse_failed",
            ) from exc

    @property
    def is_required(self) -> bool:
        """
        Returns true when the dependency is required
        """
        return self.dependency_type == "required"

    def to_dict(self) -> dict:

        """
        Gives a dict with the data of the Dependency object

        Returns:
            dict: Dict with all the Dependency data
        """

        # Serialize to the wire format expected by manifests.
        return {
            "project_id": self.project_id,
            "version_id": self.version_id,
            "dependency_type": self.dependency_type,
        }
