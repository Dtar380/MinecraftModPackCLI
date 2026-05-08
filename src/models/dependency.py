from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Dependency:
    project_id: str | None
    dependency_type: str
