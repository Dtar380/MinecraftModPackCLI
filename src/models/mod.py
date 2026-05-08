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
