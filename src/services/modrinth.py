from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import requests  # type: ignore

from ..models import Mod
from ..utils.logging import Logger


class ModrinthService:

    BASE_URL = "https://api.modrinth.com/v2"

    def __init__(self):
        self.session = requests.Session()

    def resolve_hashes(self, hashes: list[str], logger: Optional[Logger] = None) -> dict:
        r = self.session.post(
            f"{self.BASE_URL}/version_files",
            json={"hashes": hashes, "algorithm": "sha1"},
            timeout=10,
        )
        if not r.ok:
            if logger:
                logger.error(
                    "Modrinth resolve_hashes failed",
                    context={"status": str(r.status_code), "url": r.url},
                )
            raise RuntimeError("Modrinth resolve_hashes failed")
        return r.json()

    def get_project(self, project_id: str, logger: Optional[Logger] = None) -> dict:
        r = self.session.get(f"{self.BASE_URL}/project/{project_id}", timeout=2)
        if not r.ok:
            if logger:
                logger.error(
                    "Modrinth get_project failed",
                    context={
                        "status": str(r.status_code),
                        "project_id": project_id,
                        "url": r.url,
                    },
                )
            raise RuntimeError("Modrinth get_project failed")
        return r.json()

    def get_version(self, version_id: str, logger: Optional[Logger] = None) -> dict:
        r = self.session.get(f"{self.BASE_URL}/version/{version_id}", timeout=2)
        if not r.ok:
            if logger:
                logger.error(
                    "Modrinth get_version failed",
                    context={
                        "status": str(r.status_code),
                        "version_id": version_id,
                        "url": r.url,
                    },
                )
            raise RuntimeError("Modrinth get_version failed")
        return r.json()

    def get_project_versions(
        self,
        project_id: str,
        mc_version: str,
        mc_loader: str,
        logger: Optional[Logger] = None,
    ) -> list[dict]:
        r = self.session.get(
            f"{self.BASE_URL}/project/{project_id}/version",
            params={
                "loaders": json.dumps([mc_loader]),
                "game_versions": json.dumps([mc_version]),
            },
            timeout=5,
        )
        if not r.ok:
            if logger:
                logger.error(
                    "Modrinth get_project_versions failed",
                    context={
                        "status": str(r.status_code),
                        "project_id": project_id,
                        "url": r.url,
                    },
                )
            raise RuntimeError("Modrinth get_project_versions failed")
        return r.json()

    def resolve_mods(
        self, hash_index: dict[str, Path], logger: Optional[Logger] = None
    ) -> list[Mod]:
        result = self.resolve_hashes(list(hash_index.keys()), logger=logger)

        mods: list[Mod] = []

        for file_hash, version_data in result.items():
            project_id = version_data["project_id"]

            project_data = self.get_project(project_id, logger=logger)
            mod = Mod.from_modrinth(
                project_data, version_data, hash_index[file_hash].name
            )
            mods.append(mod)

        return mods

    def download_mod(
        self, mod: Mod, output_dir: Path, logger: Optional[Logger] = None
    ) -> bool:
        if logger:
            logger.debug(
                "Downloading mod",
                context={"file": mod.file_name, "url": mod.url},
            )
        with requests.get(mod.url, stream=True) as r:
            r.raise_for_status()
            with open(output_dir / mod.file_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
