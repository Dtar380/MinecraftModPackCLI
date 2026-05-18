"""
Orchestration layer for mod discovery, resolution, export, and build workflows
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

# === LOCAL ===
from ..models import Dependency, Manifest, Mod, AppConfig
from ..services import FilesystemService, ModrinthService
from ..utils import errors
from ..utils.logging import Logger

if TYPE_CHECKING:
    from ..cli.ui import UI


# ===============================================
#  RESPONSE DATACLASS
# ===============================================
# === EXPORT RESULT ===
@dataclass(slots=True)
class ExportResult:

    """
    Result metadata for an export operation
    """

    mods: list[Mod] = field(default_factory=list)
    exported_mods: list[Mod] = field(default_factory=list)
    manifest: Optional[Manifest] = None


# === VALIDATION RESULT ===
@dataclass(slots=True)
class ValidationResult:

    """
    Result metadata for a validation operation
    """

    missing: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)


# === BUILD RESULT ===
@dataclass(slots=True)
class BuildResult:

    """
    Result metadata for a build operation
    """

    mods: list[Mod] = field(default_factory=list)
    downloaded_mods: list[Mod] = field(default_factory=list)


# ===============================================
#  BUILDER
# ===============================================
class Builder:

    """
    Exposes endpoints to orchestrate services
    """

    def __init__(self, config: AppConfig, ui: Optional["UI"] = None) -> None:

        """
        Initializes service dependencies

        Parameters:
            config (AppConfig): Application configuration (filesystem, modrinth,
                resolve settings)
            ui (Optional[UI]): Optional UI for progress updates
        """

        self._fs = FilesystemService(config.services.filesystem, ui=ui)
        self._modrinth = ModrinthService(config.services.modrinth, ui=ui)
        self._now = datetime.now
        self._ui = ui
        self._core_config = config.core
        self._resolve_config = config.services.modrinth.resolve

    def discover_mods(
        self, mods_dir: Path, logger: Optional[Logger] = None
    ) -> list[Path]:

        """
        Discover mods in the providen mods directory

        Parameters:
            mods_dir (Path): Path to the mods directory
            logger (Optional[Logger]): Log helper

        Returns:
            list[Path]: List with all jar files paths located

        Raises:
            FilesystemError: If the mods directory cannot be read or does not exist.
        """

        mods = self._fs.get_mods(mods_dir, logger=logger)
        if logger:
            logger.info(
                "Mods discovered",
                context={"count": str(len(mods)), "dir": str(mods_dir)},
            )
        return mods

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
            dict[str, Path]: List with all jar files paths located

        Raises:
            FilesystemError: If any mod file cannot be read or hashed (e.g.
                permission denied, corrupt file).
        """

        index = self._fs.build_hash_index(mods, logger=logger)
        if logger:
            logger.info("Hash index built", context={"count": str(len(index))})
        return index

    def resolve_mods(
        self,
        hash_index: dict[str, Path],
        logger: Optional[Logger] = None,
    ) -> list[Mod]:

        """
        Resolves a list of hashes and returns mod objects

        Parameters:
            hash_index (dict[str, Path]):Dictionary with hashes as Keys and
                paths to the files as values
            logger (Optional[Logger]): Log helper

        Returns:
            list[Mod]: List with all the resolved mods

        Raises:
            ModrinthError: If the Modrinth API request fails due to network
                errors or bad responses.
            ModpackError: If the Modrinth API response data is malformed.
        """

        mods = self._modrinth.resolve_mods(hash_index, logger=logger)
        if logger:
            logger.info("Mods resolved", context={"count": str(len(mods))})
        return mods

    def get_common_compatibility(
        self, mods: list[Mod]
    ) -> tuple[set[str], set[str]]:

        """
        Computes the common Minecraft versions and loaders across mods

        Parameters:
            mods (list[Mod]): List of mods to analyze

        Returns:
            tuple[set[str], set[str]]: Common versions set and common loaders set
        """

        if not mods:
            return set(), set()

        common_versions = set(mods[0].mc_versions)
        common_loaders = set(mods[0].mc_loaders)

        # Intersect compatibility data across the mod list.
        for mod in mods[1:]:
            common_versions &= mod.mc_versions
            common_loaders &= mod.mc_loaders

        return common_versions, common_loaders

    def get_unique_compatibility(self, mods: list[Mod]) -> tuple[str, str]:

        """
        Picks a single Minecraft version and loader compatible with all mods

        Parameters:
            mods (list[Mod]): List of mods to analyze

        Returns:
            tuple[str, str]: Selected Minecraft version and loader

        Raises:
            ValidationError: If no common versions or loaders exist across the mods.
            ConfigError: If the configured version_policy is unknown.
        """

        common_versions, common_loaders = self.get_common_compatibility(mods)
        return self._pick_version(common_versions), self._pick_loader(common_loaders)

    def _pick_version(self, versions: set[str]) -> str:

        """
        Picks a Minecraft version from a set using the configured version_policy.

        Parameters:
            versions (set[str]): Available Minecraft versions

        Returns:
            str: Selected Minecraft version

        Raises:
            ValidationError: If the available versions set is empty (no
                compatible versions found).
            ConfigError: If the configured version_policy is not recognized.
        """

        if not versions:
            raise errors.ValidationError(
                "No compatible versions found",
                code="no_compatible_versions",
            )

        policy = self._resolve_config.version_policy

        if policy == "latest_compatible":
            # Sort by numeric parts to pick the highest dotted version.
            return sorted(
                versions,
                key=lambda v: [int(p) for p in v.split(".") if p.isdigit()],
            )[-1]

        raise errors.ConfigError(
            f"Unknown version_policy: {policy}",
            code="unknown_version_policy",
        )

    def _pick_loader(self, loaders: set[str]) -> str:

        """
        Picks a preferred loader from a set using the configured loader_policy.

        Parameters:
            loaders (set[str]): Available Minecraft loaders

        Returns:
            str: Selected Minecraft loader

        Raises:
            ValidationError: If the available loaders set is empty (no
                compatible loaders found).
        """

        if not loaders:
            raise errors.ValidationError(
                "No compatible loaders found",
                code="no_compatible_loaders",
            )

        # Extract the preferred loader from the policy (e.g. "prefer_fabric" -> "fabric").
        preferred = self._resolve_config.loader_policy.split("_", 1)[-1]
        if preferred in loaders:
            return preferred
        return sorted(loaders)[0]

    def drop_dependencies(self, mods: list[Mod]) -> list[Mod]:

        """
        Filters out library/dependency mods from a list

        Parameters:
            mods (list[Mod]): List of mods to filter

        Returns:
            list[Mod]: Mods that are not libraries
        """

        return [mod for mod in mods if not mod.is_library]

    def classify_mods(self, mods: list[Mod]) -> tuple[list[Mod], list[Mod]]:

        """
        Splits mods into server and client seed lists

        Parameters:
            mods (list[Mod]): List of mods to classify

        Returns:
            tuple[list[Mod], list[Mod]]: Server seed and client seed lists
        """

        server_seed: list[Mod] = []
        client_seed: list[Mod] = []

        # Each mod can appear in either or both seed lists.
        for mod in mods:
            if mod.server_required:
                server_seed.append(mod)

            if mod.client_required:
                client_seed.append(mod)

        return server_seed, client_seed

    def _get_dependency(
        self, dep: Dependency, logger: Optional[Logger] = None
    ) -> Mod:

        """
        Resolves a dependency to a Mod object using Modrinth

        Parameters:
            dep (Dependency): Dependency object to resolve
            logger (Optional[Logger]): Log helper

        Returns:
            Mod: Resolved dependency mod

        Raises:
            ModrinthError: If the Modrinth API request fails
            ModpackError: If the Modrinth response data is malformed
        """

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

        """
        Resolves required dependencies for a seed set of mods

        Parameters:
            seed (list[Mod]): Seed mods to expand dependencies from
            all_mods (list[Mod]): Known mods to use before fetching
            target_version (Optional[str]): Target Minecraft version
            target_loader (Optional[str]): Target Minecraft loader
            logger (Optional[Logger]): Log helper

        Returns:
            tuple[list[Mod], dict[str, set[str]]]: Full mod list and dependency map

        Raises:
            ModpackError: If no compatible versions are found for a required
                dependency during resolution.
            ModrinthError: If the Modrinth API request (get_project, get_version
                , or get_project_versions) fails.
            ValidationError: If version or loader sets are empty when inferring
                compatibility defaults.
            ConfigError: If the configured version_policy is unknown.
        """

        # Index known mods by project id to avoid duplicate lookups.
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

        # Breadth-first expansion of required dependencies.
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
                        raise errors.ModpackError(
                            "No compatible versions for dependency",
                            context={
                                "project_id": dep.project_id,
                                "mod_project_id": mod.project_id,
                                "loaders": ",".join(sorted(mod.mc_loaders)),
                                "versions": ",".join(sorted(mod.mc_versions)),
                            },
                            code="dependency_version_missing",
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
        filtered_map = {
            pid: deps for pid, deps in dependency_map.items() if pid in expanded
        }

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

        """
        Builds a manifest object from pack metadata and mods

        Parameters:
            name (str): Pack name
            version (str): Pack version
            side (str): Pack side (client or server)
            mc_version (str): Minecraft version
            mc_loader (str): Minecraft loader
            mods (list[Mod]): Mods to include in the manifest
            logger (Optional[Logger]): Log helper

        Returns:
            Manifest: Created manifest object
        """

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
        # Keep manifest creation centralized to avoid drift in metadata.
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

        """
        Exports a manifest to a pack directory with mods and manifest.json

        Parameters:
            manifest (Manifest): Manifest object to export
            src_dir (Path): Directory containing local mods
            output_dir (Path): Base output directory
            logger (Optional[Logger]): Log helper

        Returns:
            ExportResult: Export metadata and exported mods

        Raises:
            ExportError: If a mod file cannot be copied or downloaded, or if
                manifest.json cannot be written.
        """

        result = ExportResult()
        result.mods = manifest.mods

        # Target output path is namespaced by pack name/version/side.
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

        # Prefer local files, fall back to remote download when missing.
        total = len(manifest.mods)
        for idx, mod in enumerate(manifest.mods, start=1):
            src = src_dir / mod.file_name

            try:
                if src.exists():
                    dst = mods_dir / mod.file_name
                    self._fs.copy_mod(src, dst, logger=logger)
                    result.exported_mods.append(mod)
                else:
                    self._modrinth.download_mod(mod, mods_dir, logger=logger)
                    result.exported_mods.append(mod)
            except errors.AppError as exc:
                raise errors.ExportError(
                    "Failed to export mod",
                    cause=exc,
                    context={
                        "file": mod.file_name,
                        "project_id": mod.project_id,
                    },
                    code="export_mod_failed",
                ) from exc
            if self._ui:
                self._ui.progress(idx, total)

        try:
            if self._fs.write_manifest(manifest, output_dir, logger=logger):
                result.manifest = manifest
        except errors.AppError as exc:
            raise errors.ExportError(
                "Failed to write export manifest",
                cause=exc,
                context={"path": str(output_dir / "manifest.json")},
                code="export_manifest_failed",
            ) from exc

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

        """
        Writes a manifest to disk

        Parameters:
            manifest (Manifest): Manifest object to save
            output_path (Path): Output path for the manifest
            logger (Optional[Logger]): Log helper

        Returns:
            bool: True if the manifest was written

        Raises:
            FilesystemError: If the manifest file cannot be written (e.g.
                permission denied, disk full).
        """

        return self._fs.write_manifest(manifest, output_path, logger=logger)

    def validate(
        self,
        *,
        manifest_path: Path,
        src_dir: Path,
        logger: Optional[Logger] = None,
    ) -> ValidationResult:

        """
        Validates that a manifest matches the mods on disk

        Parameters:
            manifest_path (Path): Path to the manifest.json file
            src_dir (Path): Base source directory containing exported packs
            logger (Optional[Logger]): Log helper

        Returns:
            ValidationResult: Missing, extra, and mismatched mods

        Raises:
            ValidationError: If the manifest.json file cannot be read or parsed.
        """

        try:
            manifest = self._fs.read_manifest(manifest_path, logger=logger)
        except errors.AppError as exc:
            raise errors.ValidationError(
                "Failed to read manifest",
                cause=exc,
                context={"path": str(manifest_path)},
                code="manifest_read_failed",
            ) from exc
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

        # Compare file names and hashes to detect missing or mismatched mods.
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
            # Hash mismatch indicates stale or wrong binary content.
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

        """
        Builds a modpack by downloading missing or mismatched mods

        Parameters:
            manifest_path (Path): Path to the manifest.json file
            output_dir (Path): Base output directory
            logger (Optional[Logger]): Log helper

        Returns:
            BuildResult: Build metadata and downloaded mods

        Raises:
            BuildError: If the manifest.json cannot be read, or if a mod
                download during the build fails.
        """

        result = BuildResult()

        try:
            manifest = self._fs.read_manifest(manifest_path, logger=logger)
        except errors.AppError as exc:
            raise errors.BuildError(
                "Failed to read manifest for build",
                cause=exc,
                context={"path": str(manifest_path)},
                code="manifest_read_failed",
            ) from exc
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

        # Download only missing or mismatched mods.
        total = len(manifest.mods)
        for idx, mod in enumerate(manifest.mods, start=1):
            mod_path = mods_out / mod.file_name
            if mod_path.exists():
                if self._fs.sha1(mod_path, logger=logger) == mod.hash:
                    continue

            try:
                self._modrinth.download_mod(mod, mods_out, logger=logger)
                result.downloaded_mods.append(mod)
            except errors.AppError as exc:
                raise errors.BuildError(
                    "Failed to download mod during build",
                    cause=exc,
                    context={
                        "file": mod.file_name,
                        "project_id": mod.project_id,
                    },
                    code="build_download_failed",
                ) from exc
            if self._ui:
                self._ui.progress(idx, total)

        if logger:
            logger.info(
                "Build complete",
                context={"downloaded": str(len(result.downloaded_mods))},
            )

        return result
