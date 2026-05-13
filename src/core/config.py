"""
Configuration Manager — pure parser, no filesystem I/O
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === LOCAL ===
from ..models import AppConfig
from ..utils import LogLevel, LogTarget


# ===============================================
#  CONFIG MANAGER
# ===============================================
VALID_LOG_LEVELS = LogLevel._member_names_  # pylint:disable=E1101,W0212
VALID_LOG_TARGETS = LogTarget._member_names_  # pylint:disable=E1101,W0212


# ===============================================
#  CONFIG MANAGER
# ===============================================
class ConfigManager:

    """
    Pure parser that converts raw dictionaries into ``AppConfig`` objects.

    This class never touches the filesystem — all I/O lives in
    ``FilesystemService``.
    """

    @staticmethod
    def parse(data: dict) -> AppConfig:

        """
        Parse a raw TOML dict into a typed ``AppConfig``.

        Parameters:
            data (dict): Raw dictionary from ``tomllib.load()``.

        Returns:
            AppConfig: Fully populated config (missing keys → defaults).
        """

        return AppConfig.from_dict(data)

    @staticmethod
    def validate(config: AppConfig) -> list[str]:

        """
        Validate config values and return a list of warning strings.

        Parameters:
            config (AppConfig): The config to validate.

        Returns:
            list[str]: Human-readable warnings (empty when everything is valid).
        """

        warnings: list[str] = []

        lvl = config.logging.level.lower()
        if lvl not in VALID_LOG_LEVELS:
            warnings.append(
                f"Invalid logging.level '{config.logging.level}': "
                f"expected one of {sorted(VALID_LOG_LEVELS)}"
            )

        tgt = config.logging.target.lower()
        if tgt not in VALID_LOG_TARGETS:
            warnings.append(
                f"Invalid logging.target '{config.logging.target}': "
                f"expected one of {sorted(VALID_LOG_TARGETS)}"
            )

        if config.filesystem.hash_chunk_size <= 0:
            warnings.append(
                f"filesystem.hash_chunk_size must be > 0, got "
                f"{config.filesystem.hash_chunk_size}; using default 8192"
            )

        if not config.filesystem.mod_glob:
            warnings.append("filesystem.mod_glob must not be empty; using default '*.jar'")

        return warnings

    @staticmethod
    def generate_default_toml() -> str:

        """
        Generate a commented default ``config.toml``.

        Returns:
            str: Formatted TOML string suitable for writing to disk.
        """

        return """# MinecraftModpackCLI — default configuration
# Uncomment and edit values to override built-in defaults.

[defaults]
# modpack_name = "MyPack"
# version = "1.0.0"

[paths]
# logs_dir = ""

[logging]
# level = "info"       # debug | info | warning | error
# target = "file"      # console | file | both
# file_path = ""
# use_ui = true

[ui]
# enable_progress = true
# bar_width = 50
# label_width = 36

[modrinth]
# base_url = "https://api.modrinth.com/v2"
# timeout_seconds = 10
# user_agent = "MinecraftModpackCLI/0.x"

[resolve]
# version_policy = "latest_compatible"
# loader_policy = "prefer_fabric"

[validate]
# strict_missing = true
# strict_extra = false
# strict_mismatch = true

[build]
# skip_existing = true

[export]
# allow_download = true
# copy_existing = true

[filesystem]
# hash_chunk_size = 8192
# mod_glob = "*.jar"
"""

    @staticmethod
    def get_default_config() -> AppConfig:

        """
        Return an ``AppConfig`` populated entirely with defaults.

        This matches the hardcoded behaviour of v0.4.0.
        """

        return AppConfig()
