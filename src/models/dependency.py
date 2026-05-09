from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Dependency:

    project_id: str
    version_id: str
    dependency_type: str

    @classmethod
    def from_dict(cls, dependency_data: dict) -> Dependency:
        return Dependency(
            project_id=dependency_data["project_id"],
            version_id=dependency_data["version_id"],
            dependency_type=dependency_data["dependency_type"],
        )

    @property
    def is_required(self) -> bool:
        return self.dependency_type == "required"

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "version_id": self.version_id,
            "dependency_type": self.dependency_type,
        }
