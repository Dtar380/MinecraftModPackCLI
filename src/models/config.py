"""
Dataclasses and functions to manage user configs
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from dataclasses import dataclass, field
from pathlib import Path


# ===============================================
#  Defaults
# ===============================================
@dataclass(slots=True)
class DefaultsConfig:
    modpack_name: str = "MyPack"
    version: str = "1.0.0"


@dataclass(slots=True)
class PathsConfig:
    output_dir: Path = Path.home() / "Documents" / "Modpacks"
    logs_dir: Path = output_dir / "logs"


@dataclass(slots=True)
class LoggingConfig:
    level: str = "info"
    target: str = "file"
    use_ui: bool = True


@dataclass(slots=True)
class UIConfig:
    enable_progress: bool = True
    bar_width: int = 50
    label_width: int = 36


@dataclass(slots=True)
class ModrinthConfig:
    base_url: str = "https://api.modrinth.com/v2"
    timeout_seconds: int = 10
    user_agent: str = "MinecraftModpackCLI/0.x"


@dataclass(slots=True)
class ResolveConfig:
    version_policy: str = "latest_compatible"
    loader_policy: str = "prefer_fabric"


@dataclass(slots=True)
class ValidateConfig:
    strict_missing: bool = True
    strict_extra: bool = False
    strict_mismatch: bool = True


@dataclass(slots=True)
class BuildConfig:
    skip_existing: bool = True


@dataclass(slots=True)
class ExportConfig:
    allow_download: bool = True
    copy_existing: bool = True


@dataclass(slots=True)
class FilesystemConfig:
    hash_chunk_size: int = 8192
    mod_glob: str = "*.jar"


# ===============================================
#  AppConfig
# ===============================================
@dataclass(slots=True)
class AppConfig:
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    modrinth: ModrinthConfig = field(default_factory=ModrinthConfig)
    resolve: ResolveConfig = field(default_factory=ResolveConfig)
    validate: ValidateConfig = field(default_factory=ValidateConfig)
    build: BuildConfig = field(default_factory=BuildConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    filesystem: FilesystemConfig = field(default_factory=FilesystemConfig)
