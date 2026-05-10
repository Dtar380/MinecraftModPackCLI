from __future__ import annotations

from datetime import datetime
import inspect
from pathlib import Path
import traceback

from click import Command, Group  # type: ignore

from .options import (
    modpack_param,
    src_param,
    manifest_param,
    version_param,
    server_param,
    client_param,
    verbose_param,
)
from .ui import UI
from ..core import Builder
from ..utils import errors, Logger, LogLevel, LogTarget  # pylint: disable=W0611


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
        for name, func in inspect.getmembers(
            self.__class__, predicate=inspect.isfunction
        ):
            if name.startswith("_"):
                continue

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
        params = [modpack_param, src_param, version_param, server_param, client_param, verbose_param]

        def callback(
            modpack: str,
            src: Path,
            version: str = version_param.default,
            server: bool = server_param.default,
            client: bool = client_param.default,
            verbose: bool = False
        ) -> int:
            logger = self._logger("export", verbose)
            mods_dir = self._mods_dir(src)

            if not server and not client:
                server = True
                client = True

            self.ui.stage("Scanning mods")
            mod_files = self.builder.discover_mods(mods_dir)
            if not mod_files:
                self.ui.fail("Scanning mods")
                self.ui.error("No mods found")
                logger.error("No mods found")
                return 1
            self.ui.done("Scanning mods")

            self.ui.stage("Resolving mods")
            hash_index = self.builder.build_hash_index(mod_files)
            mods = self.builder.resolve_mods(hash_index)
            self.ui.done("Resolving mods")
            logger.info("Mods resolved", context={"count": str(len(mods))})

            mods = self.builder.drop_dependencies(mods)
            server_seed, client_seed = self.builder.classify_mods(mods)

            if server:
                self.ui.stage("Resolving server dependencies")
                server_pack, _ = self.builder.resolve_dependencies(server_seed, mods)
                self.ui.done("Resolving server dependencies")

                if not server_pack:
                    self.ui.warn("No server mods to export")
                else:
                    server_manifest = self.builder.create_manifest(
                        name=f"{modpack} [server]",
                        version=version,
                        side="server",
                        mc_version=server_pack[0].mc_version,
                        mc_loader=server_pack[0].mc_loader,
                        mods=server_pack,
                    )

                    self.ui.stage("Exporting server pack")
                    result = self.builder.export(
                        manifest=server_manifest,
                        src_dir=mods_dir,
                        output_dir=self.cwd,
                    )
                    self.ui.done("Exporting server pack")

                    expected = len(result.mods)
                    actual = len(result.exported_mods)
                    if actual < expected:
                        self.ui.warn(f"Server export incomplete: expected={expected} exported={actual}")
                        logger.warning(
                            "Server export incomplete",
                            context={"expected": str(expected), "exported": str(actual)},
                        )
                    else:
                        self.ui.success(f"Server export complete: {actual} mods")

            if client:
                self.ui.stage("Resolving client dependencies")
                client_pack, _ = self.builder.resolve_dependencies(client_seed, mods)
                self.ui.done("Resolving client dependencies")

                if not client_pack:
                    self.ui.warn("No client mods to export")
                else:
                    client_manifest = self.builder.create_manifest(
                        name=f"{modpack} [client]",
                        version=version,
                        side="client",
                        mc_version=client_pack[0].mc_version,
                        mc_loader=client_pack[0].mc_loader,
                        mods=client_pack,
                    )

                    self.ui.stage("Exporting client pack")
                    result = self.builder.export(
                        manifest=client_manifest,
                        src_dir=mods_dir,
                        output_dir=self.cwd,
                    )
                    self.ui.done("Exporting client pack")

                    expected = len(result.mods)
                    actual = len(result.exported_mods)
                    if actual < expected:
                        self.ui.warn(f"Client export incomplete: expected={expected} exported={actual}")
                        logger.warning(
                            "Client export incomplete",
                            context={"expected": str(expected), "exported": str(actual)},
                        )
                    else:
                        self.ui.success(f"Client export complete: {actual} mods")

            return 0

        return Command(
            name=name, help=help_text, callback=callback, params=params
        )

    def manifest(self) -> Command:

        current_frame = inspect.currentframe()
        name = current_frame.f_code.co_name if current_frame else ""
        help_text = "Create the manifest"
        params = [modpack_param, src_param, version_param, verbose_param]

        def callback(
            modpack: str,
            src: Path,
            version: str = version_param.default,
            verbose: bool = False,
        ) -> int:
            logger = self._logger("manifest", verbose)
            mods_dir = self._mods_dir(src)
            output_dir = mods_dir.parent

            self.ui.stage("Scanning mods")
            mod_files = self.builder.discover_mods(mods_dir)
            if not mod_files:
                self.ui.fail("Scanning mods")
                self.ui.error("No mods found")
                logger.error("No mods found")
                return 1
            self.ui.done("Scanning mods")

            self.ui.stage("Resolving mods")
            hash_index = self.builder.build_hash_index(mod_files)
            mods = self.builder.resolve_mods(hash_index)
            self.ui.done("Resolving mods")

            mods = self.builder.drop_dependencies(mods)
            server_seed, client_seed = self.builder.classify_mods(mods)
            combined_seed = {m.project_id: m for m in (server_seed + client_seed)}

            self.ui.stage("Resolving dependencies")
            full_pack, _ = self.builder.resolve_dependencies(
                list(combined_seed.values()), mods
            )
            self.ui.done("Resolving dependencies")

            if not full_pack:
                self.ui.error("No mods to include in manifest")
                logger.error("No mods to include in manifest")
                return 1

            manifest_obj = self.builder.create_manifest(
                name=modpack,
                version=version,
                side="local",
                mc_version=full_pack[0].mc_version,
                mc_loader=full_pack[0].mc_loader,
                mods=full_pack,
            )

            self.ui.stage("Writing manifest")
            self.builder.save_manifest(manifest=manifest_obj, output_path=output_dir)
            self.ui.done("Writing manifest")
            self.ui.success("Manifest created")

            return 0

        return Command(
            name=name, help=help_text, callback=callback, params=params
        )

    def validate(self) -> Command:

        current_frame = inspect.currentframe()
        name = current_frame.f_code.co_name if current_frame else ""
        help_text = "Validate the mods with the manifest"
        params = [src_param, verbose_param]

        def callback(src: Path, verbose: bool = False) -> int:
            logger = self._logger("validate", verbose)

            if src.is_dir():
                manifest_path = src / "manifest.json"
                base_dir = src
            else:
                manifest_path = src
                base_dir = src.parent.parent.parent.parent

            self.ui.stage("Validating manifest")
            result = self.builder.validate(
                manifest_path=manifest_path,
                src_dir=base_dir,
            )
            self.ui.done("Validating manifest")

            if result.missing or result.mismatched:
                self.ui.warn(f"Missing: {len(result.missing)}")
                self.ui.warn(f"Mismatched: {len(result.mismatched)}")
                self.ui.warn(f"Extra: {len(result.extra)}")
                logger.warning(
                    "Validation issues",
                    context={
                        "missing": str(len(result.missing)),
                        "mismatched": str(len(result.mismatched)),
                        "extra": str(len(result.extra)),
                    },
                )
                return 1

            self.ui.success("Validation passed")
            return 0

        return Command(
            name=name, help=help_text, callback=callback, params=params
        )

    def build(self) -> Command:

        current_frame = inspect.currentframe()
        name = current_frame.f_code.co_name if current_frame else ""
        help_text = "Build a modpack from the manifest"
        params = [manifest_param, verbose_param]

        def callback(manifest: Path, verbose: bool = False) -> int:
            logger = self._logger("build", verbose)

            self.ui.stage("Building modpack")
            result = self.builder.build(
                manifest_path=manifest,
                output_dir=self.cwd,
            )
            self.ui.done("Building modpack")

            expected = len(result.mods)
            actual = len(result.downloaded_mods)
            if actual < expected:
                self.ui.warn(f"Download incomplete: expected={expected} downloaded={actual}")
                logger.warning(
                    "Download incomplete",
                    context={"expected": str(expected), "downloaded": str(actual)},
                )
                return 1

            self.ui.success(f"Downloaded: {actual} mods")
            return 0

        return Command(
            name=name, help=help_text, callback=callback, params=params
        )
