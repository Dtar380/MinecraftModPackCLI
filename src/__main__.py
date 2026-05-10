"""
CLI entrypoint for the Minecraft modpack tool
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === EXTERNAL ===
from click import group, version_option  # type: ignore

# === LOCAL ===
from . import version
from .cli.commands import APP

# ===============================================
#  MAIN
# ===============================================
@version_option(version=version, message="%(version)s")
@group(cls=APP)
def cli() -> None:

    """
    Root Click command group
    """


def main() -> None:

    """
    Runs the CLI entrypoint
    """

    cli()


if __name__ == "__main__":
    main()
