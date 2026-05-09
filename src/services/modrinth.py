from __future__ import annotations

import requests  # type: ignore


class ModrinthService:

    BASE_URL = "https://api.modrinth.com/v2"

    def resolve_hasehs(self, hashes: list[str]) -> dict:
        return requests.post(
            f"{self.BASE_URL}/version_files",
            json={"hashes": hashes, "algorithm": "sha1"},
            timeout=10,
        ).json()

    def get_project(self, project_id: str) -> dict:
        return requests.get(
            f"{self.BASE_URL}/project/{project_id}", timeout=10
        ).json()
