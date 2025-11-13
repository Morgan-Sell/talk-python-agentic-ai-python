"""
Custom exceptions for Gitty Up.

This module defines a comprehensive exception hierarchy for proper error handling
throughout the application.
"""


class GittyUpError(Exception):
    """Base exception for all Gitty Up errors."""

    def __init__(self, message: str, details: str = None):
        """
        Initialize exception with message and optional details.

        Args:
            message: The main error message
            details: Additional context or details about the error
        """
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self):
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message


class ConfigurationError(GittyUpError):
    """Raised when there's an error in configuration."""

    pass


class ScannerError(GittyUpError):
    """Raised when there's an error during directory scanning."""

    pass


class ExecutorError(GittyUpError):
    """Raised when there's an error executing git commands."""

    pass


class GitCommandError(ExecutorError):
    """Raised when a git command fails."""

    def __init__(
        self, message: str, command: str = None, return_code: int = None, stderr: str = None
    ):
        """
        Initialize GitCommandError.

        Args:
            message: The main error message
            command: The git command that failed
            return_code: The return code from the failed command
            stderr: The stderr output from the command
        """
        self.command = command
        self.return_code = return_code
        self.stderr = stderr
        details = []
        if command:
            details.append(f"Command: {command}")
        if return_code is not None:
            details.append(f"Return code: {return_code}")
        if stderr:
            details.append(f"Error output: {stderr}")
        super().__init__(message, "\n".join(details) if details else None)


class GitTimeoutError(ExecutorError):
    """Raised when a git command times out."""

    pass


class InvalidRepositoryError(GittyUpError):
    """Raised when a directory is not a valid git repository."""

    pass


class RepositoryStateError(GittyUpError):
    """Raised when a repository is in an unexpected state."""

    pass


class PermissionDeniedError(ScannerError):
    """Raised when there's a permission error accessing directories or files."""

    pass


class InvalidPathError(GittyUpError):
    """Raised when an invalid path is provided."""

    pass
