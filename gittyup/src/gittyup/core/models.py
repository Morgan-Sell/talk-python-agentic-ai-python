"""
Data models for Gitty Up.

This module defines data classes for representing git repositories and operation results.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class OperationStatus(Enum):
    """Status of a git operation."""

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class RepositoryState(Enum):
    """State of a git repository."""

    CLEAN = "clean"  # No uncommitted changes
    DIRTY = "dirty"  # Has uncommitted changes
    AHEAD = "ahead"  # Ahead of remote
    BEHIND = "behind"  # Behind remote
    DIVERGED = "diverged"  # Diverged from remote
    NO_REMOTE = "no_remote"  # No remote configured
    UNKNOWN = "unknown"  # Unable to determine state


@dataclass
class Repository:
    """
    Represents a git repository with its metadata.

    Attributes:
        path: Absolute path to the repository
        name: Repository name (directory name)
        current_branch: Current branch name
        remote_url: URL of the primary remote (usually 'origin')
        remote_name: Name of the primary remote
        has_uncommitted_changes: Whether there are uncommitted changes
        has_untracked_files: Whether there are untracked files
        commits_ahead: Number of commits ahead of remote
        commits_behind: Number of commits behind remote
        state: Current state of the repository
        is_submodule: Whether this is a git submodule
        is_bare: Whether this is a bare repository
    """

    path: Path
    name: str
    current_branch: Optional[str] = None
    remote_url: Optional[str] = None
    remote_name: str = "origin"
    has_uncommitted_changes: bool = False
    has_untracked_files: bool = False
    commits_ahead: int = 0
    commits_behind: int = 0
    state: RepositoryState = RepositoryState.UNKNOWN
    is_submodule: bool = False
    is_bare: bool = False

    def __str__(self) -> str:
        """String representation of the repository."""
        return f"{self.name} ({self.path})"

    @property
    def display_path(self) -> str:
        """Get a display-friendly path (with ~ for home directory)."""
        try:
            return f"~/{self.path.relative_to(Path.home())}"
        except ValueError:
            return str(self.path)

    @property
    def needs_pull(self) -> bool:
        """Check if repository needs to be pulled."""
        return self.commits_behind > 0

    @property
    def needs_push(self) -> bool:
        """Check if repository needs to be pushed."""
        return self.commits_ahead > 0

    @property
    def is_clean(self) -> bool:
        """Check if repository has no uncommitted changes."""
        return not self.has_uncommitted_changes and not self.has_untracked_files


@dataclass
class OperationResult:
    """
    Represents the result of a git operation on a repository.

    Attributes:
        repository: The repository the operation was performed on
        operation: Name of the operation (e.g., 'pull', 'fetch', 'status')
        status: Status of the operation
        message: Human-readable message about the result
        output: Raw output from the git command
        error: Error message if the operation failed
        duration: Duration of the operation in seconds
        return_code: Return code from the git command
    """

    repository: Repository
    operation: str
    status: OperationStatus
    message: str
    output: str = ""
    error: str = ""
    duration: float = 0.0
    return_code: int = 0

    def __str__(self) -> str:
        """String representation of the operation result."""
        return f"{self.repository.name}: {self.operation} - {self.status.value}"

    @property
    def is_success(self) -> bool:
        """Check if the operation was successful."""
        return self.status == OperationStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if the operation resulted in an error."""
        return self.status == OperationStatus.ERROR

    @property
    def is_warning(self) -> bool:
        """Check if the operation resulted in a warning."""
        return self.status == OperationStatus.WARNING


@dataclass
class ScanResult:
    """
    Represents the result of scanning for repositories.

    Attributes:
        repositories: List of discovered repositories
        total_scanned: Total number of directories scanned
        duration: Duration of the scan in seconds
        errors: List of errors encountered during scanning
    """

    repositories: list[Repository] = field(default_factory=list)
    total_scanned: int = 0
    duration: float = 0.0
    errors: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        """Return the number of repositories found."""
        return len(self.repositories)

    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred during scanning."""
        return len(self.errors) > 0


@dataclass
class ExecutionSummary:
    """
    Summary of batch operation execution.

    Attributes:
        results: List of operation results
        total_repositories: Total number of repositories processed
        successful: Number of successful operations
        warnings: Number of operations with warnings
        errors: Number of failed operations
        skipped: Number of skipped operations
        total_duration: Total duration of all operations in seconds
    """

    results: list[OperationResult] = field(default_factory=list)
    total_repositories: int = 0
    successful: int = 0
    warnings: int = 0
    errors: int = 0
    skipped: int = 0
    total_duration: float = 0.0

    def add_result(self, result: OperationResult) -> None:
        """
        Add an operation result to the summary.

        Args:
            result: The operation result to add
        """
        self.results.append(result)
        self.total_duration += result.duration

        if result.status == OperationStatus.SUCCESS:
            self.successful += 1
        elif result.status == OperationStatus.WARNING:
            self.warnings += 1
        elif result.status == OperationStatus.ERROR:
            self.errors += 1
        elif result.status == OperationStatus.SKIPPED:
            self.skipped += 1

    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_repositories == 0:
            return 0.0
        return (self.successful / self.total_repositories) * 100

    @property
    def has_errors(self) -> bool:
        """Check if any operations resulted in errors."""
        return self.errors > 0

    @property
    def has_warnings(self) -> bool:
        """Check if any operations resulted in warnings."""
        return self.warnings > 0

