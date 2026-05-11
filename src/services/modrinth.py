"""
Modrinth API client for resolving and downloading mods
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import requests  # type: ignore

from ..models import Mod
from ..utils import errors
from ..utils.logging import Logger

# ===============================================
#  MODRINTH SERVICE
# ===============================================
class ModrinthService:

    """
    ModrinthAPI wrapper for performing requests
    """

    BASE_URL = "https://api.modrinth.com/v2"

    def __init__(self):

        """
        Initializes a Modrinth session client
        """

        self.session = requests.Session()

    def resolve_hashes(
        self, hashes: list[str], logger: Optional[Logger] = None
    ) -> dict:

        """
        Resolve the versions response using the hashes of the files

        Parameters:
            hashesh (list[str]): List of file hashes
            logger (Optional[Logger]): Log helper

        Returns:
            dict: Json serialized response with all files version data

        Raises:
            RuntimeError: if the POST request failed
        """

        try:
            r = self.session.post(
                f"{self.BASE_URL}/version_files",
                json={"hashes": hashes, "algorithm": "sha1"},
                timeout=10,
            )
        except requests.RequestException as exc:
            raise errors.ModrinthError(
                "Modrinth resolve_hashes request failed",
                cause=exc,
                context={"url": f"{self.BASE_URL}/version_files"},
                code="request_failed",
            ) from exc

        if not r.ok:
            raise errors.ModrinthError(
                "Modrinth resolve_hashes failed",
                context={"status": str(r.status_code), "url": r.url},
                code="bad_response",
            )

        try:
            data = r.json()
        except ValueError as exc:
            raise errors.ModrinthError(
                "Modrinth resolve_hashes returned invalid JSON",
                cause=exc,
                context={"url": r.url},
                code="invalid_response",
            ) from exc
        if logger:
            logger.debug(
                "Modrinth resolve_hashes ok",
                context={"count": str(len(data))},
            )
        return data

    def get_project(
        self, project_id: str, logger: Optional[Logger] = None
    ) -> dict:

        """
        Retrives the project data from the ModrinthAPI

        Parameters:
            project_id (str): Modrinth ID of the project
            logger (Optional[Logger]): Log helper

        Returns:
            dict: Json serialized response with the project data

        Raises:
            RuntimeError: if the GET request failed
        """

        try:
            r = self.session.get(
                f"{self.BASE_URL}/project/{project_id}", timeout=2
            )
        except requests.RequestException as exc:
            raise errors.ModrinthError(
                "Modrinth get_project request failed",
                cause=exc,
                context={"project_id": project_id},
                code="request_failed",
            ) from exc

        if not r.ok:
            raise errors.ModrinthError(
                "Modrinth get_project failed",
                context={
                    "status": str(r.status_code),
                    "project_id": project_id,
                    "url": r.url,
                },
                code="bad_response",
            )

        try:
            data = r.json()
        except ValueError as exc:
            raise errors.ModrinthError(
                "Modrinth get_project returned invalid JSON",
                cause=exc,
                context={"project_id": project_id, "url": r.url},
                code="invalid_response",
            ) from exc
        if logger:
            logger.debug(
                "Modrinth get_project ok",
                context={"project_id": project_id},
            )
        return data

    def get_version(
        self, version_id: str, logger: Optional[Logger] = None
    ) -> dict:

        """
        Retrives the version data from the ModrinthAPI

        Parameters:
            version_id (str): Modrinth ID of the version
            logger (Optional[Logger]): Log helper

        Returns:
            dict: Json serialized response with the version data

        Raises:
            RuntimeError: if the GET request failed
        """

        try:
            r = self.session.get(
                f"{self.BASE_URL}/version/{version_id}", timeout=2
            )
        except requests.RequestException as exc:
            raise errors.ModrinthError(
                "Modrinth get_version request failed",
                cause=exc,
                context={"version_id": version_id},
                code="request_failed",
            ) from exc

        if not r.ok:
            raise errors.ModrinthError(
                "Modrinth get_version failed",
                context={
                    "status": str(r.status_code),
                    "version_id": version_id,
                    "url": r.url,
                },
                code="bad_response",
            )

        try:
            data = r.json()
        except ValueError as exc:
            raise errors.ModrinthError(
                "Modrinth get_version returned invalid JSON",
                cause=exc,
                context={"version_id": version_id, "url": r.url},
                code="invalid_response",
            ) from exc
        if logger:
            logger.debug(
                "Modrinth get_version ok",
                context={"version_id": version_id},
            )
        return data

    def get_project_versions(
        self,
        project_id: str,
        mc_version: str,
        mc_loader: str,
        logger: Optional[Logger] = None,
    ) -> list[dict]:

        """
        Retrives all of the project versions from the ModrinthAPI that matches
        the given loader and version

        Parameters:
            project_id (str): Modrinth ID of the project
            mc_version (str): Minecraft version filter
            mc_loader (str): Minecraft loader filter
            logger (Optional[Logger]): Log helper

        Returns:
            dict: Json serialized response with the versions of the project

        Raises:
            RuntimeError: if the GET request failed
        """

        try:
            r = self.session.get(
                f"{self.BASE_URL}/project/{project_id}/version",
                params={
                    "loaders": json.dumps([mc_loader]),
                    "game_versions": json.dumps([mc_version]),
                },
                timeout=5,
            )
        except requests.RequestException as exc:
            raise errors.ModrinthError(
                "Modrinth get_project_versions request failed",
                cause=exc,
                context={
                    "project_id": project_id,
                    "mc_version": mc_version,
                    "mc_loader": mc_loader,
                },
                code="request_failed",
            ) from exc

        if not r.ok:
            raise errors.ModrinthError(
                "Modrinth get_project_versions failed",
                context={
                    "status": str(r.status_code),
                    "project_id": project_id,
                    "url": r.url,
                },
                code="bad_response",
            )

        try:
            data = r.json()
        except ValueError as exc:
            raise errors.ModrinthError(
                "Modrinth get_project_versions returned invalid JSON",
                cause=exc,
                context={"project_id": project_id, "url": r.url},
                code="invalid_response",
            ) from exc
        if logger:
            logger.debug(
                "Modrinth get_project_versions ok",
                context={"project_id": project_id, "count": str(len(data))},
            )
        return data

    def resolve_mods(
        self, hash_index: dict[str, Path], logger: Optional[Logger] = None
    ) -> list[Mod]:

        """
        Resolves a list of hashes and returns mod objects

        Parameters:
            hash_index (dict[str, Path]):Dictionary with hashes as Keys and paths to the files as values
            logger (Optional[Logger]): Log helper

        Returns:
            list[Mod]: List with all the resolved mods
        """

        result = self.resolve_hashes(list(hash_index.keys()), logger=logger)

        mods: list[Mod] = []

        # Each hash maps to a version payload with project metadata ids.
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
    ) -> None:

        """
        Downloads the mod into an output directory.

        Parameters:
            mod (Mod): Mod object containing all the metadata of the mod
            output_dir (Path): Path where the file will be downloaded to
            logger (Optional[Logger]): Log helper

        Raises:
            RuntimeError: if the GET request failed
        """

        if logger:
            logger.info(
                "Downloading mod",
                context={"file": mod.file_name, "url": mod.url},
            )

        # Stream large files to disk without buffering into memory.
        try:
            with requests.get(mod.url, stream=True, timeout=10) as r:
                if not r.ok:
                    raise errors.ModrinthError(
                        "Modrinth download_mod failed",
                        context={
                            "status": str(r.status_code),
                            "project_id": mod.project_id,
                            "url": r.url,
                        },
                        code="bad_response",
                    )

                try:
                    with open(output_dir / mod.file_name, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                except OSError as exc:
                    raise errors.FilesystemError(
                        "Failed to write downloaded mod",
                        cause=exc,
                        context={"path": str(output_dir / mod.file_name)},
                        code="mod_write_failed",
                    ) from exc
        except requests.RequestException as exc:
            raise errors.ModrinthError(
                "Modrinth download_mod request failed",
                cause=exc,
                context={"url": mod.url, "project_id": mod.project_id},
                code="request_failed",
            ) from exc
