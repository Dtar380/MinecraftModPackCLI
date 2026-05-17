"""
Filesystem helpers for reading, writing, and hashing modpack files
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
import hashlib
import json
from pathlib import Path
import toml  # type: ignore
from typing import Optional, TYPE_CHECKING
import shutil

# === LOCAL ===
from ..models import Manifest, AppConfig, config_from_dict, config_to_dict
from ..utils import errors
from ..utils.logging import Logger

if TYPE_CHECKING:
    from ..cli.ui import UI


# ===============================================
#  FILESYSTEMSERVICE
# ===============================================
class FilesystemService:

    """
    Filesystem operations for mods and manifests
    """

    def __init__(self, ui: Optional["UI"] = None) -> None:

        """
        Initializes the filesystem service

        Parameters:
            ui (Optional[UI]): Optional UI for progress updates
        """

        self._ui = ui

    def get_mods(
        self, mods_dir: Path, logger: Optional[Logger] = None
    ) -> list[Path]:

        """
        Gets all the .jar files inside a given directory

        Parameters:
            mods_dir (Path): Directory to search jar files in
            logger (Optional[Logger]): Log helper

        Returns:
            list[Path]: List with all jar files paths located

        Raises:
            FilesystemError: If the mods directory does not exist
        """

        if not mods_dir.exists():
            raise errors.FilesystemError(
                "Mods directory does not exist",
                context={"path": str(mods_dir)},
                code="mods_dir_missing",
            )

        mods = list(mods_dir.glob("*.jar"))
        if logger:
            logger.debug(
                "Discovered mods",
                context={"dir": str(mods_dir), "count": str(len(mods))},
            )
        return mods

    def sha1(self, path: Path, logger: Optional[Logger] = None) -> str:

        """
        Gets the hash of the providen file

        Parameters:
            path (Path): Path to the file to generate the Hash from
            logger (Optional[Logger]): Log helper

        Returns:
            str: SHA1 hash of the file

        Raises:
            FilesystemError: If the file cannot be read
        """

        h = hashlib.sha1()
        try:
            with open(path, "rb") as f:
                # Stream in chunks to avoid loading large files into memory.
                while chunk := f.read(8192):
                    h.update(chunk)
        except OSError as exc:
            raise errors.FilesystemError(
                "Failed to hash file",
                cause=exc,
                context={"path": str(path)},
                code="hash_failed",
            ) from exc
        if logger:
            logger.debug("Computed sha1", context={"file": str(path)})
        return h.hexdigest()

    def build_hash_index(
        self,
        mods: list[Path],
        logger: Optional[Logger] = None,
    ) -> dict[str, Path]:

        """
        Builds a dictionary with hashes as keys and paths as values

        Parameters:
            mods (list[Path]): List with the paths to the mods (jar files)
            logger (Optional[Logger]): Log helper

        Returns:
            dict[str, Path]: Dictionary mapping SHA1 hashes to mod file paths

        Raises:
            FilesystemError: If any mod file cannot be hashed
        """

        index: dict[str, Path] = {}
        total = len(mods)
        for idx, mod in enumerate(mods, start=1):
            index[self.sha1(mod, logger=logger)] = mod
            if self._ui:
                self._ui.progress(idx, total)
        if logger:
            logger.debug("Built hash index", context={"count": str(len(index))})
        return index

    def copy_mod(
        self, src: Path, dst: Path, logger: Optional[Logger] = None
    ) -> bool:

        """
        Copies the binaries from src to dst

        Parameters:
            src (Path): Path to the original file
            dst (Path): Path of the new file
            logger (Optional[Logger]): Log helper

        Returns:
            bool: Returns true if succeded

        Raises:
            FilesystemError: If the file copy operation fails
        """

        # Preserve file metadata when copying to the pack directory.
        try:
            shutil.copy2(src, dst)
        except OSError as exc:
            raise errors.FilesystemError(
                "Failed to copy mod file",
                cause=exc,
                context={"src": str(src), "dst": str(dst)},
                code="copy_failed",
            ) from exc
        if logger:
            logger.debug("Copied mod", context={"src": str(src), "dst": str(dst)})
        return True

    def write_manifest(
        self,
        manifest: Manifest,
        output_dir: Path,
        logger: Optional[Logger] = None,
    ) -> bool:

        """
        Writes the manifest to a json formated file

        Parameters:
            manifest (Manifest): Manifest object with all the manifest metadata
            output_dir (Path): Directory where the file will be stored
            logger (Optional[Logger]): Log helper

        Returns:
            bool: Returns true if succeded

        Raises:
            FilesystemError: If the manifest file cannot be written
        """

        file_path = output_dir / "manifest.json"
        # Use a stable JSON format for diffs and readability.
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(manifest.to_dict(), f, indent=2)
        except (OSError, TypeError) as exc:
            raise errors.FilesystemError(
                "Failed to write manifest",
                cause=exc,
                context={"path": str(file_path)},
                code="manifest_write_failed",
            ) from exc
        if logger:
            logger.debug("Wrote manifest", context={"path": str(file_path)})
        return True

    def read_manifest(
        self, manifest_path: Path, logger: Optional[Logger] = None
    ) -> Manifest:

        """
        Reads the manifest from a json formated file

        Parameters:
            manifest_path (Path): Path to the manifest.json file
            logger (Optional[Logger]): Log helper

        Returns:
            Manifest: Manifest object with all the metadata

        Raises:
            FilesystemError: If the manifest file cannot be read or parsed
        """

        file_path = manifest_path
        # Load the on-disk manifest and normalize it into a model.
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise errors.FilesystemError(
                "Failed to read manifest",
                cause=exc,
                context={"path": str(file_path)},
                code="manifest_read_failed",
            ) from exc
        if logger:
            logger.debug("Read manifest", context={"path": str(file_path)})
        return Manifest.from_dict(data)

    def write_config(
        self,
        config: AppConfig,
        ouput_dir: Path,
        logger: Optional[Logger] = None,
    ) -> bool:

        """
        Writes the application config to a TOML-formatted file

        Parameters:
            config (AppConfig): Configuration object to persist
            ouput_dir (Path): Directory where config.toml will be written
            logger (Optional[Logger]): Log helper

        Returns:
            bool: True on success

        Raises:
            FilesystemError: If the config file cannot be written
        """

        file_path = ouput_dir / "config.toml"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                toml.dump(config_to_dict(config), f)
        except (OSError, TypeError) as exc:
            raise errors.FilesystemError(
                "Failed to write config",
                cause=exc,
                context={"path": str(file_path)},
                code="config_write_failed",
            ) from exc
        if logger:
            logger.debug("Wrote config", context={"path": str(file_path)})
        return True

    def read_config(
        self, config_path: Path, logger: Optional[Logger] = None
    ) -> AppConfig:

        """
        Reads and parses an application config from a TOML-formatted file

        Parameters:
            config_path (Path): Path to the config.toml file
            logger (Optional[Logger]): Log helper

        Returns:
            AppConfig: Parsed configuration object

        Raises:
            FilesystemError: If the config file cannot be read or parsed
        """

        file_path = config_path

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = toml.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise errors.FilesystemError(
                "Failed to read config",
                cause=exc,
                context={"path": str(file_path)},
                code="config_read_failed",
            ) from exc
        if logger:
            logger.debug("Read config", context={"path": str(file_path)})
        return config_from_dict(AppConfig, data)
