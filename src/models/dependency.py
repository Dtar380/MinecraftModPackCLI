# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from dataclasses import dataclass

# ===============================================
#  DEPENDENCY
# ===============================================
@dataclass(slots=True)
class Dependency:

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

        return Dependency(
            project_id=dependency_data["project_id"],
            version_id=dependency_data["version_id"],
            dependency_type=dependency_data["dependency_type"],
        )

    @property
    def is_required(self) -> bool:
        return self.dependency_type == "required"

    def to_dict(self) -> dict:

        """
        Gives a dict with the data of the Dependency object

        Returns:
            dict: Dict with all the Dependency data
        """

        return {
            "project_id": self.project_id,
            "version_id": self.version_id,
            "dependency_type": self.dependency_type,
        }
