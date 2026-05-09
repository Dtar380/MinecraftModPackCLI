from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from ..models.manifest import Manifest
from ..models.mod import Mod


class FilesystemService:

    def __init__(self, mods_dir: Path, output_dir: Path) -> None:
        self.mods_dir = mods_dir
        self.output_dir = output_dir

    def get_mods(self) -> list[Path]:
        return list(self.mods_dir.glob("*.jar"))

    def sha1(self, path: Path) -> str:
        h = hashlib.sha1()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def build_hash_index(self, mods: list[Path]) -> dict[str, Path]:
        return {self.sha1(mod): mod for mod in mods}

    def copy_mods(self, mods: list[Mod]) -> None:
        for mod in mods:
            src = self.mods_dir / mod.file_name
            dst = self.output_dir / mod.file_name
            shutil.copy2(src, dst)

    def write_manifest(self, manifest: Manifest) -> None:
        file_path = self.output_dir / "manifest.json"
        with open(file_path, "+w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2)

    def read_manifest(self) -> Manifest:
        file_path = self.output_dir / "manifest.json"
        with open(file_path, "+r", encoding="utf-8") as f:
            data = json.load(f)
        return Manifest.from_dict(data)
