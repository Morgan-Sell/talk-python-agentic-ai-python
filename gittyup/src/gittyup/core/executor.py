"""
Git command executor module for Gitty Up.

This module provides safe, robust execution of git commands on repositories
with proper error handling, timeout management, and result tracking.
"""

import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

from gittyup.core.models import (
    ExecutionSummary,
    OperationResult,
    OperationStatus,
    Repository,
)
from gittyup.core.repository_info import extract_repository_info
from gittyup.exceptions import (
    GitCommandError,
    GitTimeoutError,
    InvalidRepositoryError,
)
from gittyup.utils.git_utils import run_git_command, validate_repository


class GitExecutor:
    """
    Executes git commands on repositories safely and efficiently.

    This class handles:
    - Single and batch git operations
    - Timeout management
    - Error handling and recovery
    - Thread-safe parallel execution
    - Detailed result tracking
    """

    def __init__(self, timeout: int = 300, max_workers: Optional[int] = None):
        """
        Initialize the GitExecutor.

        Args:
            timeout: Maximum time in seconds for git operations (default: 300)
            max_workers: Maximum number of parallel workers (default: None = auto)
        """
        self.timeout = timeout
        self.max_workers = max_workers

    def execute_single(
        self,
        repository: Repository,
        operation: str = "pull",
        dry_run: bool = False,
    ) -> OperationResult:
        """
        Execute a git command on a single repository.

        Args:
            repository: Repository object to operate on
            operation: Git operation to perform (e.g., 'pull', 'fetch', 'status')
            dry_run: If True, don't actually execute the command

        Returns:
            OperationResult with execution details

        Raises:
            InvalidRepositoryError: If the repository is not valid
        """
        start_time = time.time()

        try:
            # Validate repository
            validate_repository(repository.path)

            # Handle dry-run mode
            if dry_run:
                message = f"Would execute: git {operation}"
                return OperationResult(
                    repository=repository,
                    operation=operation,
                    status=OperationStatus.SKIPPED,
                    message=message,
                    output=message,
                    duration=time.time() - start_time,
                )

            # Execute the git command
            args = self._build_command_args(operation, repository)
            returncode, stdout, stderr = run_git_command(
                repository.path, args, timeout=self.timeout
            )

            # Determine status based on return code and output
            status, message = self._parse_result(
                operation, returncode, stdout, stderr, repository
            )

            return OperationResult(
                repository=repository,
                operation=operation,
                status=status,
                message=message,
                output=stdout,
                error=stderr,
                duration=time.time() - start_time,
                return_code=returncode,
            )

        except subprocess.TimeoutExpired:
            return OperationResult(
                repository=repository,
                operation=operation,
                status=OperationStatus.TIMEOUT,
                message=f"Operation timed out after {self.timeout} seconds",
                error=f"Command exceeded timeout of {self.timeout} seconds",
                duration=time.time() - start_time,
            )

        except InvalidRepositoryError as e:
            return OperationResult(
                repository=repository,
                operation=operation,
                status=OperationStatus.ERROR,
                message=f"Invalid repository: {e.message}",
                error=str(e),
                duration=time.time() - start_time,
            )

        except Exception as e:
            return OperationResult(
                repository=repository,
                operation=operation,
                status=OperationStatus.ERROR,
                message=f"Unexpected error: {str(e)}",
                error=str(e),
                duration=time.time() - start_time,
            )

    def execute_batch(
        self,
        repositories: List[Repository],
        operation: str = "pull",
        dry_run: bool = False,
        parallel: bool = True,
    ) -> ExecutionSummary:
        """
        Execute a git command on multiple repositories.

        Args:
            repositories: List of Repository objects to operate on
            operation: Git operation to perform
            dry_run: If True, don't actually execute commands
            parallel: If True, execute operations in parallel

        Returns:
            ExecutionSummary with results for all repositories
        """
        summary = ExecutionSummary(total_repositories=len(repositories))
        start_time = time.time()

        if parallel and len(repositories) > 1:
            # Execute in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(
                        self.execute_single, repo, operation, dry_run
                    ): repo
                    for repo in repositories
                }

                for future in as_completed(futures):
                    result = future.result()
                    summary.add_result(result)
        else:
            # Execute sequentially
            for repo in repositories:
                result = self.execute_single(repo, operation, dry_run)
                summary.add_result(result)

        summary.total_duration = time.time() - start_time
        return summary

    def _build_command_args(self, operation: str, repository: Repository) -> List[str]:
        """
        Build git command arguments based on the operation.

        Args:
            operation: The git operation to perform
            repository: The repository to operate on

        Returns:
            List of command arguments
        """
        # Handle different operations
        if operation == "pull":
            return ["pull", "--no-rebase"]
        elif operation == "fetch":
            return ["fetch", "--all", "--prune"]
        elif operation == "status":
            return ["status", "--porcelain", "--branch"]
        elif operation == "push":
            return ["push"]
        else:
            # For custom operations, split the operation string
            return operation.split()

    def _parse_result(
        self,
        operation: str,
        returncode: int,
        stdout: str,
        stderr: str,
        repository: Repository,
    ) -> tuple[OperationStatus, str]:
        """
        Parse git command results to determine status and message.

        Args:
            operation: The operation that was performed
            returncode: Return code from git command
            stdout: Standard output from git command
            stderr: Standard error from git command
            repository: The repository operated on

        Returns:
            Tuple of (OperationStatus, message)
        """
        # Success case
        if returncode == 0:
            # Check for specific success messages
            if operation == "pull":
                if "Already up to date" in stdout or "Already up-to-date" in stdout:
                    return OperationStatus.SUCCESS, "Already up to date"
                elif "Fast-forward" in stdout:
                    return OperationStatus.SUCCESS, "Updated (fast-forward)"
                else:
                    return OperationStatus.SUCCESS, "Pull completed successfully"

            elif operation == "fetch":
                return OperationStatus.SUCCESS, "Fetch completed successfully"

            elif operation == "status":
                return OperationStatus.SUCCESS, "Status retrieved successfully"

            else:
                return OperationStatus.SUCCESS, f"{operation} completed successfully"

        # Warning cases (non-zero but not critical)
        if returncode == 1 and stderr:
            # Some git operations return 1 for non-critical issues
            if "nothing to commit" in stderr.lower():
                return OperationStatus.SUCCESS, "No changes to commit"

            if "no changes" in stderr.lower():
                return OperationStatus.SUCCESS, "No changes"

            # Check for warnings
            if any(
                word in stderr.lower()
                for word in ["warning", "hint", "suggestion"]
            ):
                return OperationStatus.WARNING, f"Completed with warnings: {stderr[:100]}"

        # Error cases
        error_msg = stderr if stderr else stdout

        if "not a git repository" in error_msg.lower():
            return OperationStatus.ERROR, "Not a git repository"

        if "permission denied" in error_msg.lower():
            return OperationStatus.ERROR, "Permission denied"

        if "could not resolve host" in error_msg.lower():
            return OperationStatus.ERROR, "Network error: Could not resolve host"

        if "connection" in error_msg.lower() and "refused" in error_msg.lower():
            return OperationStatus.ERROR, "Network error: Connection refused"

        if "authentication failed" in error_msg.lower():
            return OperationStatus.ERROR, "Authentication failed"

        if "conflict" in error_msg.lower():
            return OperationStatus.ERROR, "Merge conflict detected"

        # Generic error
        error_preview = error_msg[:200] if error_msg else "Unknown error"
        return OperationStatus.ERROR, f"Failed: {error_preview}"
