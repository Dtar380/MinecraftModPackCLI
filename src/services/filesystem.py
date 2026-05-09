from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from ..models import Manifest, Mod


class FilesystemService:

    def get_mods(self, mods_dir: Path) -> list[Path]:
        return list(mods_dir.glob("*.jar"))

    def sha1(self, path: Path) -> str:
        h = hashlib.sha1()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def build_hash_index(self, mods: list[Path]) -> dict[str, Path]:
        return {self.sha1(mod): mod for mod in mods}

    def copy_mods(
        self, mods: list[Mod], mods_dir: Path, output_dir: Path
    ) -> None:
        for mod in mods:
            src = mods_dir / mod.file_name
            dst = output_dir / mod.file_name
            shutil.copy2(src, dst)

    def write_manifest(self, manifest: Manifest, output_dir: Path) -> None:
        file_path = output_dir / "manifest.json"
        with open(file_path, "+w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2)

    def read_manifest(self, manifest_path: Path) -> Manifest:
        file_path = manifest_path
        with open(file_path, "+r", encoding="utf-8") as f:
            data = json.load(f)
        return Manifest.from_dict(data)
