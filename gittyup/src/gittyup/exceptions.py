"""
Custom exceptions for Gitty Up.
"""


class GittyUpError(Exception):
    """Base exception for all Gitty Up errors."""

    pass


class ConfigurationError(GittyUpError):
    """Raised when there's an error in configuration."""

    pass


class ScannerError(GittyUpError):
    """Raised when there's an error during directory scanning."""

    pass


class ExecutorError(GittyUpError):
    """Raised when there's an error executing git commands."""

    pass


class PermissionError(ScannerError):
    """Raised when there's a permission error accessing directories."""

    pass


class InvalidPathError(GittyUpError):
    """Raised when an invalid path is provided."""

    pass
