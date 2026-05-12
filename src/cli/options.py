"""
Defines common Click parameters shared across CLI commands
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from pathlib import Path

# === EXTERNAL ===
from click import Argument, Option  # type: ignore
from click import Path as clickPath


# ===============================================
#  VARIABLES
# ===============================================
modpack_param = Argument(["modpack"], required=True)
src_param = Argument(
    ["src"],
    required=True,
    type=clickPath(exists=True, dir_okay=True, path_type=Path),
)
manifest_param = Argument(
    ["manifest"],
    required=True,
    type=clickPath(exists=True, dir_okay=False, path_type=Path),
)
version_param = Option(
    ["--version"],
    default="1.0.0",
    type=str,
    help="Type the version of the ModPack",
)
server_param = Option(
    ["--server"], is_flag=True, default=False, help="Server only export"
)
client_param = Option(
    ["--client"], is_flag=True, default=False, help="Client only export"
)
verbose_param = Option(
    ["--verbose"],
    is_flag=True,
    default=False,
    help="Adds more logs to the terminal",
)
