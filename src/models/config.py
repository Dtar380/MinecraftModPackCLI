"""
Dataclasses and functions to manage user configs.
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from dataclasses import dataclass, field, fields as dataclass_fields
from pathlib import Path
from typing import Any, get_type_hints

# === LOCAL ===
from ..utils import errors


# ===============================================
#  defaults → defaults.names
# ===============================================
@dataclass(slots=True)
class NamesConfig:

    """
    Corresponds to [defaults.names] in the TOML file.
    """

    name: str = "MyPack"
    version: str = "1.0"


@dataclass(slots=True)
class PathsConfig:

    """
    Corresponds to [defaults.paths] in the TOML file.
    """

    output_dir: Path = Path.home() / "Documents" / "Modpacks"
    logs_dir: Path = output_dir / "logs"


@dataclass(slots=True)
class DefaultsConfig:

    """
    Groups [defaults.names] and [defaults.paths].
    """

    names: NamesConfig = field(default_factory=NamesConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)


# ===============================================
#  cli → cli.logging / cli.ui
# ===============================================
@dataclass(slots=True)
class LoggingConfig:

    """
    Corresponds to [cli.logging] in the TOML file.
    """

    level: str = "info"
    target: str = "file"
    file_path: str = ""
    use_ui: bool = True


@dataclass(slots=True)
class UIConfig:

    """
    Corresponds to [cli.ui] in the TOML file.
    """

    enable_progress: bool = True
    bar_width: int = 50
    label_width: int = 36


@dataclass(slots=True)
class CliConfig:

    """
    Groups [cli.logging] and [cli.ui].
    """

    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ui: UIConfig = field(default_factory=UIConfig)


# ===============================================
#  services → services.filesystem / services.modrinth
# ===============================================
@dataclass(slots=True)
class FilesystemConfig:

    """
    Corresponds to [services.filesystem] in the TOML file.
    """

    hash_chunk_size: int = 8192
    mod_glob: str = "*.jar"


@dataclass(slots=True)
class ResolveConfig:

    """
    Corresponds to [services.modrinth.resolve] in the TOML file.
    """

    version_policy: str = "latest_compatible"
    loader_policy: str = "prefer_fabric"


@dataclass(slots=True)
class ModrinthConfig:

    """
    Corresponds to [services.modrinth] in the TOML file.
    """

    base_url: str = "https://api.modrinth.com/v2"
    timeout_seconds: int = 10
    user_agent: str = "MinecraftModpackCLI/0.x"
    resolve: ResolveConfig = field(default_factory=ResolveConfig)


@dataclass(slots=True)
class ServicesConfig:

    """
    Groups [services.filesystem] and [services.modrinth].
    """

    filesystem: FilesystemConfig = field(default_factory=FilesystemConfig)
    modrinth: ModrinthConfig = field(default_factory=ModrinthConfig)


# ===============================================
#  core → core.validate / core.build / core.export
# ===============================================
@dataclass(slots=True)
class ValidateConfig:

    """
    Corresponds to [core.validate] in the TOML file.
    """

    strict_missing: bool = True
    strict_extra: bool = False
    strict_mismatch: bool = True


@dataclass(slots=True)
class BuildConfig:

    """
    Corresponds to [core.build] in the TOML file.
    """

    skip_existing: bool = True


@dataclass(slots=True)
class ExportConfig:

    """
    Corresponds to [core.export] in the TOML file.
    """

    allow_download: bool = True
    copy_existing: bool = True


@dataclass(slots=True)
class CoreConfig:

    """
    Groups [core.validate], [core.build], and [core.export].
    """

    validate: ValidateConfig = field(default_factory=ValidateConfig)
    build: BuildConfig = field(default_factory=BuildConfig)
    export: ExportConfig = field(default_factory=ExportConfig)


# ===============================================
#  AppConfig — top-level config matching TOML
# ===============================================
@dataclass(slots=True)
class AppConfig:

    """
    Top-level config dataclass mirroring the full TOML structure.
    """

    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    cli: CliConfig = field(default_factory=CliConfig)
    services: ServicesConfig = field(default_factory=ServicesConfig)
    core: CoreConfig = field(default_factory=CoreConfig)


# ===============================================
#  Generic serialization / deserialization
# ===============================================


def from_dict(data_class: Any, data: dict) -> Any:

    """
    Deserialize a dict into a config dataclass, recursing into nested dataclasses.

    Parameters:
        data_class: The dataclass type to build.
        data: Raw dictionary (from TOML parsing).

    Returns:
        An instance of *data_class* with all fields populated.

    Raises:
        errors.ConfigError: If a required key is missing or the data is invalid.
    """

    try:
        hints = get_type_hints(data_class)
    except NameError:
        hints = {}

    try:
        kwargs: dict[str, Any] = {}
        for f in dataclass_fields(data_class):
            raw = data[f.name]
            f_type = hints.get(f.name)

            if f_type is not None and hasattr(f_type, "__dataclass_fields__"):
                kwargs[f.name] = from_dict(f_type, raw)
            elif f_type is Path:
                kwargs[f.name] = Path(raw)
            else:
                kwargs[f.name] = raw

        return data_class(**kwargs)
    except (KeyError, TypeError) as exc:
        raise errors.ConfigError(
            f"Invalid config data for {data_class.__name__}",
            cause=exc,
            code="config_parse_failed",
        ) from exc


def to_dict(instance: Any) -> dict:

    """
    Serialize a config dataclass to a plain dict, recursing into nested dataclasses.

    Parameters:
        instance: A config dataclass instance.

    Returns:
        A plain dictionary (suitable for TOML serialization).
    """

    result: dict[str, Any] = {}
    for f in dataclass_fields(type(instance)):
        value = getattr(instance, f.name)

        if hasattr(type(value), "__dataclass_fields__"):
            result[f.name] = to_dict(value)
        elif isinstance(value, Path):
            result[f.name] = str(value)
        else:
            result[f.name] = value

    return result
