from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import Dependency, Manifest, Mod
from ..services import FilesystemService, ModrinthService
from ..utils.logging import Logger


@dataclass(slots=True)
class ExportResult:
    mods: list[Mod] = field(default_factory=list)
    exported_mods: list[Mod] = field(default_factory=list)
    manifest: Optional[Manifest] = None


@dataclass(slots=True)
class ValidationResult:
    missing: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BuildResult:
    mods: list[Mod] = field(default_factory=list)
    downloaded_mods: list[Mod] = field(default_factory=list)


class Builder:

    def __init__(self) -> None:
        self._fs = FilesystemService()
        self._modrinth = ModrinthService()
        self._now = datetime.now

    def discover_mods(
        self, mods_dir: Path, logger: Optional[Logger] = None
    ) -> list[Path]:
        mods = self._fs.get_mods(mods_dir, logger=logger)
        if logger:
            logger.info(
                "Mods discovered",
                context={"count": str(len(mods)), "dir": str(mods_dir)},
            )
        return mods

    def build_hash_index(
        self, mods: list[Path], logger: Optional[Logger] = None
    ) -> dict[str, Path]:
        index = self._fs.build_hash_index(mods, logger=logger)
        if logger:
            logger.info("Hash index built", context={"count": str(len(index))})
        return index

    def resolve_mods(
        self, hash_index: dict[str, Path], logger: Optional[Logger] = None
    ) -> list[Mod]:
        mods = self._modrinth.resolve_mods(hash_index, logger=logger)
        if logger:
            logger.info("Mods resolved", context={"count": str(len(mods))})
        return mods

    def get_common_compatibility(
        self, mods: list[Mod]
    ) -> tuple[set[str], set[str]]:
        if not mods:
            return set(), set()

        common_versions = set(mods[0].mc_versions)
        common_loaders = set(mods[0].mc_loaders)

        for mod in mods[1:]:
            common_versions &= mod.mc_versions
            common_loaders &= mod.mc_loaders

        return common_versions, common_loaders

    def get_unique_compatibility(self, mods: list[Mod]) -> tuple[str, str]:
        common_versions, common_loaders = self.get_common_compatibility(mods)
        return self._pick_version(common_versions), self._pick_loader(common_loaders)

    def _pick_version(self, versions: set[str]) -> str:
        if not versions:
            raise RuntimeError("No compatible versions found")
        return sorted(versions, key=lambda v: [int(p) for p in v.split(".") if p.isdigit()])[-1]

    def _pick_loader(self, loaders: set[str]) -> str:
        if not loaders:
            raise RuntimeError("No compatible loaders found")
        if "fabric" in loaders:
            return "fabric"
        return sorted(loaders)[0]

    def drop_dependencies(self, mods: list[Mod]) -> list[Mod]:
        return [mod for mod in mods if not mod.is_library]

    def classify_mods(self, mods: list[Mod]) -> tuple[list[Mod], list[Mod]]:
        server_seed: list[Mod] = []
        client_seed: list[Mod] = []

        for mod in mods:
            if mod.server_required:
                server_seed.append(mod)

            if mod.client_required:
                client_seed.append(mod)

        return server_seed, client_seed

    def _get_dependency(
        self, dep: Dependency, logger: Optional[Logger] = None
    ) -> Mod:
        project_data = self._modrinth.get_project(dep.project_id, logger=logger)
        version_data = self._modrinth.get_version(dep.version_id, logger=logger)
        return Mod.from_modrinth(
            project_data, version_data, version_data["files"][0]["filename"]
        )

    def resolve_dependencies(
        self,
        seed: list[Mod],
        all_mods: list[Mod],
        target_version: Optional[str] = None,
        target_loader: Optional[str] = None,
        logger: Optional[Logger] = None,
    ) -> tuple[list[Mod], dict[str, set[str]]]:
        by_project = {mod.project_id: mod for mod in all_mods}

        if logger:
            logger.info(
                "Resolving dependencies",
                context={
                    "seed": str(len(seed)),
                    "known": str(len(all_mods)),
                },
            )

        if target_version is None or target_loader is None:
            common_versions, common_loaders = self.get_common_compatibility(seed)
            if target_version is None and common_versions:
                target_version = self._pick_version(common_versions)
            if target_loader is None and common_loaders:
                target_loader = self._pick_loader(common_loaders)

        expanded = {mod.project_id for mod in seed}
        dependency_map: dict[str, set[str]] = {}

        queue = list(seed)
        while queue:

            mod = queue.pop(0)

            for dep in mod.dependencies:
                if not dep.is_required:
                    continue

                dep_id = dep.project_id
                if not dep_id:
                    continue

                dependency_map.setdefault(mod.project_id, set()).add(dep_id)

                if dep_id in expanded:
                    continue
                expanded.add(dep_id)
                if dep_id in by_project:
                    queue.append(by_project[dep_id])
                    continue

                if not dep.version_id:
                    dep_version = target_version or self._pick_version(mod.mc_versions)
                    dep_loader = target_loader or self._pick_loader(mod.mc_loaders)
                    versions = self._modrinth.get_project_versions(
                        dep.project_id,
                        dep_version,
                        dep_loader,
                        logger=logger,
                    )
                    if not versions:
                        raise RuntimeError(
                            "No compatible versions for dependency "
                            f"{dep.project_id} ({mod.mc_loaders} {mod.mc_versions})"
                        )
                    dep = Dependency(
                        project_id=dep.project_id,
                        version_id=versions[0]["id"],
                        dependency_type=dep.dependency_type,
                    )

                dep_mod = self._get_dependency(dep, logger=logger)
                by_project[dep_id] = dep_mod
                queue.append(dep_mod)

        full_pack = [by_project[pid] for pid in expanded if pid in by_project]
        filtered_map = {pid: deps for pid, deps in dependency_map.items() if pid in expanded}

        if logger:
            logger.info(
                "Dependencies resolved",
                context={
                    "pack": str(len(full_pack)),
                    "links": str(len(filtered_map)),
                },
            )

        return full_pack, filtered_map

    def create_manifest(
        self,
        *,
        name: str,
        version: str,
        side: str,
        mc_version: str,
        mc_loader: str,
        mods: list[Mod],
        logger: Optional[Logger] = None,
    ) -> Manifest:
        if logger:
            logger.info(
                "Creating manifest",
                context={
                    "name": name,
                    "version": version,
                    "side": side,
                    "mods": str(len(mods)),
                },
            )
        return Manifest(
            name=name,
            version=version,
            side=side,
            mc_version=mc_version,
            mc_loader=mc_loader,
            created_at=self._now(),
            mods=mods
        )

    def export(
        self,
        *,
        manifest: Manifest,
        src_dir: Path,
        output_dir: Path,
        logger: Optional[Logger] = None,
    ) -> ExportResult:
        result = ExportResult()
        result.mods = manifest.mods

        output_dir = (
            output_dir
            / manifest.name
            / manifest.version
            / manifest.side
        )
        mods_dir = output_dir / "mods"

        if logger:
            logger.info(
                "Exporting pack",
                context={
                    "name": manifest.name,
                    "version": manifest.version,
                    "side": manifest.side,
                    "mods": str(len(manifest.mods)),
                    "output": str(output_dir),
                },
            )

        mods_dir.mkdir(parents=True, exist_ok=True)

        for mod in manifest.mods:
            src = src_dir / mod.file_name

            if src.exists():
                dst = mods_dir / mod.file_name
                self._fs.copy_mod(src, dst, logger=logger)
                result.exported_mods.append(mod)
            elif self._modrinth.download_mod(mod, mods_dir, logger=logger):
                result.exported_mods.append(mod)

        if self._fs.write_manifest(manifest, output_dir, logger=logger):
            result.manifest = manifest

        if logger:
            logger.info(
                "Export complete",
                context={"exported": str(len(result.exported_mods))},
            )

        return result

    def save_manifest(
        self,
        *,
        manifest: Manifest,
        output_path: Path,
        logger: Optional[Logger] = None,
    ) -> bool:
        return self._fs.write_manifest(manifest, output_path, logger=logger)

    def validate(
        self,
        *,
        manifest_path: Path,
        src_dir: Path,
        logger: Optional[Logger] = None,
    ) -> ValidationResult:
        manifest = self._fs.read_manifest(manifest_path, logger=logger)
        src_dir = (
            src_dir
            / manifest.name
            / manifest.version
            / manifest.side
            / "mods"
        )

        if logger:
            logger.info(
                "Validating manifest",
                context={"mods_dir": str(src_dir)},
            )

        manifest_mods = {mod.file_name for mod in manifest.mods}
        manifest_hashes = {mod.hash for mod in manifest.mods}
        on_disk_mods = {
            file.name for file in self._fs.get_mods(src_dir, logger=logger)
        }

        missing = []
        extra = []
        mismatched = []

        for mod in manifest_mods:
            if mod not in on_disk_mods:
                missing.append(mod)
                continue

        for mod in on_disk_mods:
            if mod not in manifest_mods:
                extra.append(mod)
                continue
            if self._fs.sha1(src_dir / mod, logger=logger) not in manifest_hashes:
                mismatched.append(mod)

        return ValidationResult(
            missing=missing,
            extra=extra,
            mismatched=mismatched
        )

    def build(
        self,
        *,
        manifest_path: Path,
        output_dir: Path,
        logger: Optional[Logger] = None,
    ) -> BuildResult:
        result = BuildResult()

        manifest = self._fs.read_manifest(manifest_path, logger=logger)
        result.mods = manifest.mods

        mods_out = (
            output_dir
            / manifest.name
            / manifest.version
            / manifest.side
            / "mods"
        )
        mods_out.mkdir(parents=True, exist_ok=True)

        if logger:
            logger.info(
                "Building pack",
                context={
                    "name": manifest.name,
                    "version": manifest.version,
                    "side": manifest.side,
                    "mods": str(len(manifest.mods)),
                    "output": str(mods_out),
                },
            )

        for mod in manifest.mods:
            mod_path = mods_out / mod.file_name
            if mod_path.exists():
                if self._fs.sha1(mod_path, logger=logger) == mod.hash:
                    continue

            if self._modrinth.download_mod(mod, mods_out, logger=logger):
                result.downloaded_mods.append(mod)

        if logger:
            logger.info(
                "Build complete",
                context={"downloaded": str(len(result.downloaded_mods))},
            )

        return result
