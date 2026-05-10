from __future__ import annotations

from datetime import datetime
import inspect
from pathlib import Path
import traceback

from click import Command, Group  # type: ignore

from .options import modpack, src, manifest, version, server, client, verbose
from .ui import UI
from ..core import Builder
from ..models import Mod, Manifest, Dependency
from ..utils import errors, Logger, LogLevel, LogTarget


class APP(Group):

    cwd: Path = Path.cwd()

    def __init__(self) -> None:
        super().__init__()
        self.__register_commands()

        self.log_dir = self.cwd / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.ui = UI()
        self.builder = Builder()

    def __register_commands(self) -> None:
        # Iterate only functions declared on the subclass (avoid inherited click methods)
        for name, func in inspect.getmembers(
            self.__class__, predicate=inspect.isfunction
        ):
            if name.startswith("_"):
                continue

            # Skip methods not defined on this exact class (i.e., inherited ones)
            if not func.__qualname__.startswith(self.__class__.__name__ + "."):
                continue

            method = getattr(self, name)
            try:
                result = method()
            except Exception as e:
                print(f"Error registering command '{name}': {e}")
                traceback.print_exc()
                continue

            if isinstance(result, Command):
                self.add_command(result)

    def _mods_dir(self, src: Path) -> Path:
        return src / "mods" if (src / "mods").exists() else src

    def _logger(self, command: str, verbose: bool) -> Logger:
        level = LogLevel.DEBUG if verbose else LogLevel.INFO
        target = LogTarget.BOTH if verbose else LogTarget.FILE
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        return Logger(
            level=level,
            target=target,
            file_path=self.log_dir / f"{command}-{ts}.log"
        )

    def export(self) -> Command:

        current_frame = inspect.currentframe()
        name = current_frame.f_code.co_name if current_frame else ""
        help_text = "Export the modpack and create a manifest"
        params = [modpack, src, version, server, client, verbose]

        def callback(
            modpack: str,
            src: Path,
            version: str = version.default,
            server: bool = server.default,
            client: bool = client.default,
            verbose: bool = False
        ) -> int:
            logger = self._logger("export", verbose)
            mods_dir = self._mods_dir(src)

            if not server and not client:
                server = True
                client = True

            return 0

        return Command(
            name=name, help=help_text, callback=callback, params=params
        )

    def manifest(self) -> Command:

        current_frame = inspect.currentframe()
        name = current_frame.f_code.co_name if current_frame else ""
        help_text = "Create the manifest"
        params = [modpack, src, version, verbose]

        def callback(
            modpack: str,
            src: Path,
            version: str = version.default,
            verbose: bool = False,
        ) -> int:
            return 0

        return Command(
            name=name, help=help_text, callback=callback, params=params
        )

    def validate(self) -> Command:

        current_frame = inspect.currentframe()
        name = current_frame.f_code.co_name if current_frame else ""
        help_text = "Validate the mods with the manifest"
        params = [src, verbose]

        def callback(src: Path, verbose: bool = False) -> int:
            return 0

        return Command(
            name=name, help=help_text, callback=callback, params=params
        )

    def build(self) -> Command:

        current_frame = inspect.currentframe()
        name = current_frame.f_code.co_name if current_frame else ""
        help_text = "Build a modpack from the manifest"
        params = [manifest, verbose]

        def callback(manifest: Path, verbose: bool = False) -> int:
            return 0

        return Command(
            name=name, help=help_text, callback=callback, params=params
        )
