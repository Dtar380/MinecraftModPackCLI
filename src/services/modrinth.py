from __future__ import annotations

from pathlib import Path

import requests  # type: ignore

from ..models import Mod


class ModrinthService:

    BASE_URL = "https://api.modrinth.com/v2"

    def __init__(self):
        self.session = requests.Session()

    def resolve_hashes(self, hashes: list[str]) -> dict:
        return self.session.post(
            f"{self.BASE_URL}/version_files",
            json={"hashes": hashes, "algorithm": "sha1"},
            timeout=10,
        ).json()

    def get_project(self, project_id: str) -> dict:
        return self.session.get(
            f"{self.BASE_URL}/project/{project_id}", timeout=10
        ).json()

    def resolve_mods(self, hash_index: dict[str, Path]) -> list[Mod]:
        result = self.resolve_hashes(list(hash_index.keys()))

        mods: list[Mod] = []

        for file_hash, version_data in result.items():
            project_id = version_data["project_id"]

            project_data = self.get_project(project_id)
            Mod.from_modrinth(
                project_data, version_data, hash_index[file_hash].name
            )

        return mods
