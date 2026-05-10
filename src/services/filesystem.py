from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional
import shutil

from ..models import Manifest
from ..utils.logging import Logger


class FilesystemService:

    def get_mods(self, mods_dir: Path, logger: Optional[Logger] = None) -> list[Path]:
        mods = list(mods_dir.glob("*.jar"))
        if logger:
            logger.debug(
                "Discovered mods",
                context={"dir": str(mods_dir), "count": str(len(mods))},
            )
        return mods

    def sha1(self, path: Path, logger: Optional[Logger] = None) -> str:
        h = hashlib.sha1()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        if logger:
            logger.debug("Computed sha1", context={"file": str(path)})
        return h.hexdigest()

    def build_hash_index(
        self, mods: list[Path], logger: Optional[Logger] = None
    ) -> dict[str, Path]:
        index = {self.sha1(mod, logger=logger): mod for mod in mods}
        if logger:
            logger.debug("Built hash index", context={"count": str(len(index))})
        return index

    def copy_mod(
        self, src: Path, dst: Path, logger: Optional[Logger] = None
    ) -> None:
        shutil.copy2(src, dst)
        if logger:
            logger.debug("Copied mod", context={"src": str(src), "dst": str(dst)})

    def write_manifest(
        self, manifest: Manifest, output_dir: Path, logger: Optional[Logger] = None
    ) -> bool:
        file_path = output_dir / "manifest.json"
        with open(file_path, "+w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2)
        if logger:
            logger.debug("Wrote manifest", context={"path": str(file_path)})
        return True

    def read_manifest(
        self, manifest_path: Path, logger: Optional[Logger] = None
    ) -> Manifest:
        file_path = manifest_path
        with open(file_path, "+r", encoding="utf-8") as f:
            data = json.load(f)
        if logger:
            logger.debug("Read manifest", context={"path": str(file_path)})
        return Manifest.from_dict(data)
