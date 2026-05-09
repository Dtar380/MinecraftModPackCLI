from __future__ import annotations

from pathlib import Path

from click import Argument, Option  # type: ignore
from click import Path as clickPath

modpack = Argument(["modpack"], required=True)
src = Argument(
    ["src"],
    required=True,
    type=clickPath(exists=True, dir_okay=True, path_type=Path),
)
manifest = Argument(
    ["manifest"],
    required=True,
    type=clickPath(exists=True, dir_okay=False, path_type=Path),
)
version = Option(["--version"], default="1.0.0", type=str)
server = Option(["--server"], is_flag=True, default=False)
client = Option(["--client"], is_flag=True, default=False)
