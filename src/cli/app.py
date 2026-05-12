"""
Click command definitions for the modpack CLI
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from datetime import datetime
import inspect
from pathlib import Path
import traceback

# === EXTERNAL ===
from click import Command, Group  # type: ignore

# === LOCAL ===
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


# ===============================================
#  APP
# ===============================================
class APP(Group):

    """
    CLI application group that registers and runs commands
    """

    cwd: Path = Path.cwd()

    def __init__(self, *args, **kwargs) -> None:  # pylint: disable=W0613

        """
        Initializes the CLI app and registers commands
        """

        super().__init__()
        self.__register_commands()

        self.log_dir = self.cwd / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.ui = UI()
        self.builder = Builder(self.ui)

    def __register_commands(self) -> None:

        """
        Registers public command factory methods defined on the class
        """

        # Discover public factory methods and register any Click commands they return.
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

        """
        Resolves the mods directory from a source path

        Parameters:
            src (Path): Source path pointing to mods or its parent

        Returns:
            Path: Path to the mods directory
        """

        return src / "mods" if (src / "mods").exists() else src

    def _logger(self, command: str, verbose: bool) -> Logger:

        """
        Builds a logger for a command run

        Parameters:
            command (str): Command name
            verbose (bool): Verbose flag

        Returns:
            Logger: Configured logger instance
        """

        level = LogLevel.DEBUG if verbose else LogLevel.INFO
        target = LogTarget.BOTH if verbose else LogTarget.FILE
        ts = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        return Logger(
            level=level,
            target=target,
            file_path=self.log_dir / f"{command}-{ts}.log",
            ui=self.ui,
        )

    def _handle_app_error(self, err: errors.AppError, logger: Logger) -> int:

        """
        Handles known application errors consistently

        Parameters:
            err (errors.AppError): Custom error instance
            logger (Logger): Log helper

        Returns:
            int: Exit code
        """

        self.ui.fail()

        details = []
        if err.code:
            details.append(f"code={err.code}")
        if err.context:
            details.append(", ".join(f"{k}={v}" for k, v in err.context.items()))
        message = str(err)
        if details:
            message = f"{message} ({'; '.join(details)})"

        self.ui.error(message)
        context = {}
        if err.code:
            context["code"] = err.code
        if err.context:
            context.update({k: str(v) for k, v in err.context.items()})
        if err.cause:
            context["cause"] = str(err.cause)
        logger.error(str(err), context=context)
        return 1

    def export(self) -> Command:

        """
        Creates the export command

        Returns:
            Command: Click command for exporting packs
        """

        current_frame = inspect.currentframe()
        name = current_frame.f_code.co_name if current_frame else ""
        help_text = "Export the modpack and create a manifest"
        params = [
            modpack_param,
            src_param,
            version_param,
            server_param,
            client_param,
            verbose_param,
        ]

        def callback(
            modpack: str,
            src: Path,
            version: str = version_param.default,
            server: bool = server_param.default,
            client: bool = client_param.default,
            verbose: bool = False
        ) -> int:

            """
            Executes the export command

            Parameters:
                modpack (str): Modpack name
                src (Path): Source directory
                version (str): Modpack version
                server (bool): Export server side
                client (bool): Export client side
                verbose (bool): Verbose logging

            Returns:
                int: Exit code
            """

            logger = self._logger("export", verbose)
            try:
                mods_dir = self._mods_dir(src)

                logger.info("Command start", context={"command": "export"})
                logger.debug(
                    "Input params",
                    context={
                        "modpack": modpack,
                        "src": str(src),
                        "version": version,
                        "server": str(server),
                        "client": str(client),
                    },
                )
                logger.debug("Mods dir resolved", context={"mods_dir": str(mods_dir)})

                # If neither side is specified, export both by default.
                if not server and not client:
                    server = True
                    client = True

                self.ui.stage("Scanning mods")
                mod_files = self.builder.discover_mods(mods_dir, logger=logger)
                if not mod_files:
                    self.ui.fail("Scanning mods")
                    self.ui.error("No mods found")
                    return 1
                self.ui.done("Scanning mods")
                logger.info("Mods discovered", context={"count": str(len(mod_files))})

                self.ui.stage("Hashing mods")
                hash_index = self.builder.build_hash_index(
                    mod_files,
                    logger=logger,
                )
                self.ui.done("Hashing mods")

                self.ui.stage("Resolving mods")
                all_mods = self.builder.resolve_mods(
                    hash_index,
                    logger=logger,
                )
                self.ui.done("Resolving mods")
                logger.info("Mods resolved", context={"count": str(len(all_mods))})

                # Split out seed mods before expanding dependencies by side.
                seed_mods = self.builder.drop_dependencies(all_mods)
                server_seed, client_seed = self.builder.classify_mods(seed_mods)
                logger.info(
                    "Dependencies dropped",
                    context={"remaining": str(len(seed_mods))},
                )
                logger.info(
                    "Seeds classified",
                    context={
                        "server_seed": str(len(server_seed)),
                        "client_seed": str(len(client_seed)),
                    },
                )

                if server:
                    server_ids = self._export_side(
                        side="server",
                        modpack=modpack,
                        version=version,
                        seed=server_seed,
                        all_mods=all_mods,
                        mods_dir=mods_dir,
                        logger=logger,
                    )
                else:
                    server_ids = set()

                if client:
                    client_ids = self._export_side(
                        side="client",
                        modpack=modpack,
                        version=version,
                        seed=client_seed,
                        all_mods=all_mods,
                        mods_dir=mods_dir,
                        logger=logger,
                    )
                else:
                    client_ids = set()

                exported_ids = server_ids | client_ids
                dropped_total = len({m.project_id for m in all_mods}) - len(exported_ids)
                logger.info(
                    "Export dropped mods",
                    context={
                        "dropped": str(dropped_total),
                        "total": str(len(all_mods)),
                    },
                )

                self.ui.summary(
                    [
                        f"mods_total={len(all_mods)}",
                        f"mods_exported={len(exported_ids)}",
                        f"mods_dropped={dropped_total}",
                    ]
                )

                return 0
            except errors.AppError as exc:
                return self._handle_app_error(exc, logger)
            except Exception as exc:
                self.ui.fail()
                self.ui.error("Unexpected error")
                logger.error("Unexpected error", context={"error": str(exc)})
                return 1

        return Command(
            name=name, help=help_text, callback=callback, params=params
        )

    def _export_side(
        self,
        *,
        side: str,
        modpack: str,
        version: str,
        seed: list,
        all_mods: list,
        mods_dir: Path,
        logger: Logger,
    ) -> set[str]:

        """
        Exports a single pack side and returns the exported project ids

        Parameters:
            side (str): Side name (client or server)
            modpack (str): Modpack name
            version (str): Modpack version
            seed (list): Seed mods for the side
            all_mods (list): All resolved mods
            mods_dir (Path): Directory containing local mods
            logger (Logger): Log helper

        Returns:
            set[str]: Project ids included in the exported pack
        """

        side_title = side.capitalize()

        if not seed:
            self.ui.warn(f"No {side} mods to export")
            return set()

        # Expand dependencies to build the full pack for this side.
        target_version, target_loader = self.builder.get_unique_compatibility(seed)
        self.ui.stage(f"Resolving {side} dependencies")
        pack, _ = self.builder.resolve_dependencies(
            seed,
            all_mods,
            target_version=target_version,
            target_loader=target_loader,
            logger=logger,
        )
        self.ui.done(f"Resolving {side} dependencies")
        logger.info(
            f"{side_title} dependencies resolved",
            context={"pack": str(len(pack))},
        )

        if not pack:
            self.ui.warn(f"No {side} mods to export")
            return set()

        pack_version, pack_loader = self.builder.get_unique_compatibility(pack)
        manifest = self.builder.create_manifest(
            name=modpack,
            version=version,
            side=side,
            mc_version=pack_version,
            mc_loader=pack_loader,
            mods=pack,
            logger=logger,
        )

        # Write files and manifest to the output folder.
        self.ui.stage(f"Exporting {side} pack")
        result = self.builder.export(
            manifest=manifest,
            src_dir=mods_dir,
            output_dir=self.cwd,
            logger=logger,
        )
        self.ui.done(f"Exporting {side} pack")
        logger.info(
            f"{side_title} export result",
            context={
                "expected": str(len(result.mods)),
                "exported": str(len(result.exported_mods)),
            },
        )

        expected = len(result.mods)
        actual = len(result.exported_mods)
        if actual < expected:
            self.ui.warn(
                f"{side_title} export incomplete: expected={expected} exported={actual}"
            )
            logger.warning(
                f"{side_title} export incomplete",
                context={"expected": str(expected), "exported": str(actual)},
            )
        else:
            self.ui.success(f"{side_title} export complete: {actual} mods")

        return {mod.project_id for mod in pack}

    def manifest(self) -> Command:

        """
        Creates the manifest command

        Returns:
            Command: Click command for writing a manifest
        """

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

            """
            Executes the manifest command

            Parameters:
                modpack (str): Modpack name
                src (Path): Source directory
                version (str): Modpack version
                verbose (bool): Verbose logging

            Returns:
                int: Exit code
            """

            logger = self._logger("manifest", verbose)
            try:
                mods_dir = self._mods_dir(src)
                output_dir = mods_dir.parent

                logger.info("Command start", context={"command": "manifest"})
                logger.debug(
                    "Input params",
                    context={
                        "modpack": modpack,
                        "src": str(src),
                        "version": version,
                    },
                )
                logger.debug(
                    "Paths resolved",
                    context={
                        "mods_dir": str(mods_dir),
                        "output_dir": str(output_dir),
                    },
                )

                self.ui.stage("Scanning mods")
                mod_files = self.builder.discover_mods(mods_dir, logger=logger)
                if not mod_files:
                    self.ui.fail("Scanning mods")
                    self.ui.error("No mods found")
                    return 1
                self.ui.done("Scanning mods")
                logger.info("Mods discovered", context={"count": str(len(mod_files))})

                self.ui.stage("Hashing mods")
                hash_index = self.builder.build_hash_index(
                    mod_files,
                    logger=logger,
                )
                self.ui.done("Hashing mods")

                self.ui.stage("Resolving mods")
                all_mods = self.builder.resolve_mods(
                    hash_index,
                    logger=logger,
                )
                self.ui.done("Resolving mods")
                logger.info("Mods resolved", context={"count": str(len(all_mods))})

                seed_for_manifest = all_mods
                # Use a single compatibility target for the manifest.
                manifest_version, manifest_loader = self.builder.get_unique_compatibility(
                    all_mods
                )

                self.ui.stage("Resolving dependencies")
                full_pack, _ = self.builder.resolve_dependencies(
                    seed_for_manifest,
                    all_mods,
                    target_version=manifest_version,
                    target_loader=manifest_loader,
                    logger=logger,
                )
                self.ui.done("Resolving dependencies")
                logger.info(
                    "Dependencies resolved",
                    context={"pack": str(len(full_pack))},
                )

                if not full_pack:
                    self.ui.error("No mods to include in manifest")
                    return 1

                manifest_obj = self.builder.create_manifest(
                    name=modpack,
                    version=version,
                    side="local",
                    mc_version=manifest_version,
                    mc_loader=manifest_loader,
                    mods=full_pack,
                    logger=logger,
                )

                self.ui.stage("Writing manifest")
                self.builder.save_manifest(
                    manifest=manifest_obj, output_path=output_dir, logger=logger
                )
                self.ui.done("Writing manifest")
                self.ui.success("Manifest created")
                logger.info(
                    "Manifest saved",
                    context={"path": str(output_dir / "manifest.json")},
                )

                self.ui.summary(
                    [
                        f"mods_total={len(all_mods)}",
                        f"mods_manifest={len(full_pack)}",
                        f"manifest_path={output_dir / 'manifest.json'}",
                    ]
                )

                return 0
            except errors.AppError as exc:
                return self._handle_app_error(exc, logger)
            except Exception as exc:
                self.ui.fail()
                self.ui.error("Unexpected error")
                logger.error("Unexpected error", context={"error": str(exc)})
                return 1

        return Command(
            name=name, help=help_text, callback=callback, params=params
        )

    def validate(self) -> Command:

        """
        Creates the validate command

        Returns:
            Command: Click command for validating packs
        """

        current_frame = inspect.currentframe()
        name = current_frame.f_code.co_name if current_frame else ""
        help_text = "Validate the mods with the manifest"
        params = [src_param, verbose_param]

        def callback(src: Path, verbose: bool = False) -> int:

            """
            Executes the validate command

            Parameters:
                src (Path): Manifest path or pack directory
                verbose (bool): Verbose logging

            Returns:
                int: Exit code
            """

            logger = self._logger("validate", verbose)
            try:
                logger.info("Command start", context={"command": "validate"})

                # Accept either a manifest path or a pack directory.
                if src.is_dir():
                    manifest_path = src / "manifest.json"
                    if manifest_path.exists():
                        base_dir = src.parent.parent.parent
                    else:
                        base_dir = src
                else:
                    manifest_path = src
                    base_dir = src.parent.parent.parent

                logger.debug(
                    "Validation paths",
                    context={
                        "manifest": str(manifest_path),
                        "base_dir": str(base_dir),
                    },
                )

                self.ui.stage("Validating manifest")
                result = self.builder.validate(
                    manifest_path=manifest_path,
                    src_dir=base_dir,
                    logger=logger,
                )
                self.ui.done("Validating manifest")

                logger.info(
                    "Validation result",
                    context={
                        "missing": str(len(result.missing)),
                        "mismatched": str(len(result.mismatched)),
                        "extra": str(len(result.extra)),
                    },
                )

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
                    self.ui.summary(
                        [
                            f"missing={len(result.missing)}",
                            f"mismatched={len(result.mismatched)}",
                            f"extra={len(result.extra)}",
                        ]
                    )
                    return 1

                self.ui.success("Validation passed")
                self.ui.summary(
                    [
                        "missing=0",
                        "mismatched=0",
                        f"extra={len(result.extra)}",
                    ]
                )
                return 0
            except errors.AppError as exc:
                return self._handle_app_error(exc, logger)
            except Exception as exc:
                self.ui.fail()
                self.ui.error("Unexpected error")
                logger.error("Unexpected error", context={"error": str(exc)})
                return 1

        return Command(
            name=name, help=help_text, callback=callback, params=params
        )

    def build(self) -> Command:

        """
        Creates the build command

        Returns:
            Command: Click command for building packs
        """

        current_frame = inspect.currentframe()
        name = current_frame.f_code.co_name if current_frame else ""
        help_text = "Build a modpack from the manifest"
        params = [manifest_param, verbose_param]

        def callback(manifest: Path, verbose: bool = False) -> int:

            """
            Executes the build command

            Parameters:
                manifest (Path): Path to manifest.json
                verbose (bool): Verbose logging

            Returns:
                int: Exit code
            """

            logger = self._logger("build", verbose)
            try:
                logger.info("Command start", context={"command": "build"})
                logger.debug("Manifest path", context={"manifest": str(manifest)})

                self.ui.stage("Building modpack")
                result = self.builder.build(
                    manifest_path=manifest,
                    output_dir=self.cwd,
                    logger=logger,
                )
                self.ui.done("Building modpack")

                logger.info(
                    "Build result",
                    context={
                        "expected": str(len(result.mods)),
                        "downloaded": str(len(result.downloaded_mods)),
                    },
                )

                # Ensure all expected mods were downloaded.
                expected = len(result.mods)
                actual = len(result.downloaded_mods)
                if actual < expected:
                    self.ui.warn(
                        f"Download incomplete: expected={expected} downloaded={actual}"
                    )
                    logger.warning(
                        "Download incomplete",
                        context={"expected": str(expected), "downloaded": str(actual)},
                    )
                    self.ui.summary(
                        [
                            f"mods_expected={expected}",
                            f"mods_downloaded={actual}",
                        ]
                    )
                    return 1

                self.ui.success(f"Downloaded: {actual} mods")
                self.ui.summary(
                    [
                        f"mods_expected={expected}",
                        f"mods_downloaded={actual}",
                    ]
                )
                return 0
            except errors.AppError as exc:
                return self._handle_app_error(exc, logger)
            except Exception as exc:
                self.ui.fail()
                self.ui.error("Unexpected error")
                logger.error("Unexpected error", context={"error": str(exc)})
                return 1

        return Command(
            name=name, help=help_text, callback=callback, params=params
        )
