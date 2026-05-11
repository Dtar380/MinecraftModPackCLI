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
from typing import Optional
import shutil

# === LOCAL ===
from ..models import Manifest
from ..utils.logging import Logger

# ===============================================
#  FILESYSTEMSERVICE
# ===============================================
class FilesystemService:

    """
    Filesystem operations for mods and manifests
    """

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
        """

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
        """

        h = hashlib.sha1()
        with open(path, "rb") as f:
            # Stream in chunks to avoid loading large files into memory.
            while chunk := f.read(8192):
                h.update(chunk)
        if logger:
            logger.debug("Computed sha1", context={"file": str(path)})
        return h.hexdigest()

    def build_hash_index(
        self, mods: list[Path], logger: Optional[Logger] = None
    ) -> dict[str, Path]:

        """
        Builds a dictionary with hashes as keys and paths as values

        Parameters:
            mods (list[Path]): List with the paths to the mods (jar files)
            logger (Optional[Logger]): Log helper

        Returns:
            dict[str, Path]: List with all jar files paths located
        """

        index = {self.sha1(mod, logger=logger): mod for mod in mods}
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
        """

        # Preserve file metadata when copying to the pack directory.
        shutil.copy2(src, dst)
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
        """

        file_path = output_dir / "manifest.json"
        # Use a stable JSON format for diffs and readability.
        with open(file_path, "+w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2)
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
        """

        file_path = manifest_path
        # Load the on-disk manifest and normalize it into a model.
        with open(file_path, "+r", encoding="utf-8") as f:
            data = json.load(f)
        if logger:
            logger.debug("Read manifest", context={"path": str(file_path)})
        return Manifest.from_dict(data)
