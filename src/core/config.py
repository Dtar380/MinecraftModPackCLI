"""Configuration persistence, validation, and defaults for the modpack CLI"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from dataclasses import fields as dataclass_fields
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints, Union

# === LOCAL ===
from ..models import AppConfig
from ..services import FilesystemService
from ..utils import LogLevel, LogTarget, errors


# ===============================================
#  CONFIG MANAGER
# ===============================================
VALID_LOG_LEVELS = LogLevel._member_names_  # pylint:disable=E1101,W0212
VALID_LOG_TARGETS = LogTarget._member_names_  # pylint:disable=E1101,W0212
VALID_LOADER_POLICIES = {
    f"prefer_{loader}" for loader in ["fabric", "forge", "neoforge", "quilt"]
}
VALID_VERSION_POLICIES = {"latest_compatible"}


# ===============================================
#  CONFIG MANAGER
# ===============================================
class ConfigManager:

    """
    Manages reading, writing, validating, and generating default configuration
    """

    config_path = Path.home() / ".config" / "minecraftmodpack"

    def __init__(self) -> None:

        """
        Initialize the manager with a FilesystemService using default config
        """

        self.config_path.mkdir(parents=True, exist_ok=True)
        self._fs = FilesystemService(AppConfig().services.filesystem)

    @property
    def config_file(self) -> Path:

        """
        Resolve the absolute path to the config.toml file

        Returns:
            Path: path to the config file
        """

        return self.config_path / "config.toml"

    @classmethod
    def generate_default(cls) -> AppConfig:

        """
        Return a freshly-constructed AppConfig with all default values

        Returns:
            AppConfig:
        """

        return AppConfig()

    def init(self) -> bool:

        """
        Write a default config file to disk

        Returns:
            bool: True on success (always)

        Raises:
            FilesystemError: If the default config file cannot be written to disk.
        """

        self.save(self.generate_default())
        return True

    def save(self, config: AppConfig) -> bool:

        """
        Persist a config to the config file

        Parameters:
            config (AppConfig): The configuration to write

        Returns:
            bool: True on success (always)

        Raises:
            FilesystemError: If the config file cannot be written to disk.
        """

        self._fs.write_config(config, self.config_file)
        return True

    @staticmethod
    def _validate_values(config: AppConfig) -> bool:

        """
        Check value-level constraints (log levels, policies, etc.)

        Parameters:
            config (AppConfig): The configuration to validate

        Returns:
            bool: True when all values are within allowed sets
        """

        logging = config.cli.logging
        if logging.level not in VALID_LOG_LEVELS:
            return False
        if logging.target not in VALID_LOG_TARGETS:
            return False

        resolve = config.services.modrinth.resolve
        if resolve.loader_policy not in VALID_LOADER_POLICIES:
            return False
        if resolve.version_policy not in VALID_VERSION_POLICIES:
            return False

        return True

    @staticmethod
    def _validate_types(config: AppConfig) -> list[str]:

        """
        Walk the full AppConfig tree and verify every field matches its declared type.

        Parameters:
            config (AppConfig): The configuration to validate

        Returns:
            list[str]: Human-readable type-mismatch descriptions.
                       An empty list means all types are correct.
        """

        errors_list: list[str] = []
        ConfigManager._check_dataclass(AppConfig, config, [], errors_list)
        return errors_list

    @staticmethod
    def _check_dataclass(
        dc_type: type,
        instance: Any,
        path: list[str],
        errors_list: list[str],
    ) -> None:

        """
        Recurse into one dataclass level, appending type errors to *errors_list*.

        Parameters:
            dc_type: The dataclass type to validate against.
            instance: The dataclass instance to check.
            path: Current dotted-field-path (for error messages).
            errors_list: Accumulator for error strings.
        """

        try:
            hints = get_type_hints(dc_type)
        except (NameError, TypeError):
            return  # Can't validate without resolved type hints.

        for f in dataclass_fields(dc_type):
            expected = hints.get(f.name)
            if expected is None:
                continue

            value = getattr(instance, f.name)
            field_path = path + [f.name]

            # Nested dataclass → recurse.
            if hasattr(expected, "__dataclass_fields__"):
                if not isinstance(value, expected):
                    errors_list.append(
                        f"{'.'.join(field_path)}: "
                        f"expected {expected.__name__}, "
                        f"got {type(value).__name__} ({value!r})",
                    )
                else:
                    ConfigManager._check_dataclass(
                        expected, value, field_path, errors_list,
                    )
            else:
                if not ConfigManager._type_matches(expected, value):
                    errors_list.append(
                        f"{'.'.join(field_path)}: "
                        f"expected {expected!r}, "
                        f"got {type(value).__name__} ({value!r})",
                    )

    @staticmethod
    def _type_matches(expected: type, value: Any) -> bool:

        """
        Check whether *value* satisfies the *expected* type annotation.

        Parameters:
            expected (type): The type annotation to check against
            value (Any): The value to check

        Returns:
            bool: True if the value matches the expected type

        Notes:
            Handles Optional (Union[X, None]), Path, bool (before int), and
            simple isinstance checks.
        """

        origin = get_origin(expected)

        # Optional[X] → Union[X, None]
        if origin is Union:
            args = get_args(expected)
            if value is None and type(None) in args:
                return True
            non_none = [a for a in args if not isinstance(a, type(None))]
            return any(ConfigManager._type_matches(a, value) for a in non_none)

        # Path
        if expected is Path:
            return isinstance(value, Path)

        # bool must be checked before int (bool is a subclass of int in Python).
        if expected is bool:
            return isinstance(value, bool)

        # Primitive types (str, int, float, …).
        return isinstance(value, expected)

    def read(self) -> AppConfig:

        """
        Load, validate types, and validate values from the config file

        Returns:
            AppConfig: Parsed and validated configuration

        Raises:
            ConfigError: If the config file is missing, has type mismatches,
                or contains invalid values
        """

        if not self.config_file.exists():
            raise errors.ConfigError(
                f"Config file not found at {self.config_file}. Run init first.",
                code="config_not_found",
            )

        config = self._fs.read_config(self.config_file)

        # First verify every field's Python type matches its annotation.
        type_errors = self._validate_types(config)
        if type_errors:
            raise errors.ConfigError(
                "Config has type mismatches:\n  - "
                + "\n  - ".join(type_errors),
                code="invalid_config_types",
            )

        # Then verify value-level constraints (log levels, policies, …).
        if not self._validate_values(config):
            raise errors.ConfigError(
                "Config file contains invalid values.",
                code="invalid_config",
            )

        return config
