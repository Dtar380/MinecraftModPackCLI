from __future__ import annotations

from pathlib import Path

from click import Argument, Option  # type: ignore
from click import Path as clickPath

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
version_param = Option(["--version"], default="1.0.0", type=str)
server_param = Option(["--server"], is_flag=True, default=False)
client_param = Option(["--client"], is_flag=True, default=False)
verbose_param = Option(["--verbose"], is_flag=True, default=False)
