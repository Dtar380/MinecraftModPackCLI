"""
Custom error types for modpack operations
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# ===============================================
#  ERRORS
# ===============================================
class AppError(Exception):

    """
    Base error with optional context and error codes
    """

    def __init__(
        self,
        message: str,
        *,
        cause: Exception | None = None,
        context: dict[str, str] | None = None,
        code: str | None = None,
    ):

        """
        Initializes the error with optional context

        Parameters:
            message (str): Human-readable error message
            cause (Exception | None): Optional underlying exception
            context (dict[str, str] | None): Extra metadata
            code (str | None): Optional error code
        """

        super().__init__(message)
        self.cause = cause
        self.context = context or {}
        self.code = code


class FilesystemError(AppError):

    """
    Raised when filesystem operations fail
    """


class ModrinthError(AppError):

    """
    Raised when Modrinth API operations fail
    """


class ModpackError(AppError):

    """
    Base error for modpack-related operations
    """


class ManifestError(ModpackError):

    """
    Raised when manifest operations fail
    """


class ValidationError(ModpackError):

    """
    Raised when validation detects mismatches
    """


class ExportError(ModpackError):

    """
    Raised when exporting a modpack fails
    """


class BuildError(ModpackError):

    """
    Raised when building a modpack fails
    """
