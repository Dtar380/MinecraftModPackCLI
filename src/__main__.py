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
from .cli.app import APP


# ===============================================
#  MAIN
# ===============================================
@version_option(version=version, message="%(version)s")
@group(cls=APP)
def cli() -> None:

    """
    Root Click command group for the modpack CLI

    Returns:
        None: Delegates to Click's command dispatcher via the APP group
    """


def main() -> None:

    """
    Runs the CLI entrypoint

    Returns:
        None: Delegates to cli() which dispatches to Click
    """

    # Delegate to Click's command dispatcher.
    cli()


if __name__ == "__main__":
    main()
