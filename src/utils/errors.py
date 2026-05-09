from __future__ import annotations


class AppError(Exception):
    def __init__(
        self,
        message: str,
        *,
        cause: Exception | None = None,
        context: dict[str, str] | None = None,
        code: str | None = None,
    ):
        super().__init__(message)
        self.cause = cause
        self.context = context or {}
        self.code = code


class FilesystemError(AppError): ...
class ModrinthError(AppError): ...
class ModpackError(AppError): ...
class ManifestError(ModpackError): ...
class ValidationError(ModpackError): ...
class ExportError(ModpackError): ...
class BuildError(ModpackError): ...
