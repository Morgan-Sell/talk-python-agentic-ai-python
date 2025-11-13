"""
Git-related utilities for Gitty Up.

This module provides comprehensive git repository detection and validation,
including support for standard repositories, bare repositories, submodules,
and git worktrees.
"""

import subprocess
from pathlib import Path
from typing import Optional, Tuple

from gittyup.exceptions import InvalidRepositoryError


def is_git_repository(path: Path) -> bool:
    """
    Check if a directory is a git repository.

    This function checks for:
    - Standard repositories (.git directory)
    - Bare repositories (config file + refs directory)
    - Git worktrees (.git file pointing to worktree)

    Args:
        path: Path to check

    Returns:
        True if the directory is a valid git repository, False otherwise
    """
    path = Path(path).resolve()

    # Check for standard .git directory
    git_dir = path / ".git"
    if git_dir.is_dir():
        return _is_valid_git_dir(git_dir)

    # Check for .git file (worktree)
    if git_dir.is_file():
        return _is_valid_worktree(git_dir)

    # Check for bare repository
    if _is_bare_repository(path):
        return True

    return False


def _is_valid_git_dir(git_dir: Path) -> bool:
    """
    Validate that a .git directory is properly structured.

    Args:
        git_dir: Path to the .git directory

    Returns:
        True if the directory has required git files/directories
    """
    # Check for essential git directory components
    required_items = ["HEAD", "config", "refs"]
    return all((git_dir / item).exists() for item in required_items)


def _is_valid_worktree(git_file: Path) -> bool:
    """
    Validate that a .git file is a valid worktree reference.

    Args:
        git_file: Path to the .git file

    Returns:
        True if the file contains a valid gitdir reference
    """
    try:
        content = git_file.read_text().strip()
        return content.startswith("gitdir: ")
    except (OSError, UnicodeDecodeError):
        return False


def _is_bare_repository(path: Path) -> bool:
    """
    Check if a directory is a bare git repository.

    Args:
        path: Path to check

    Returns:
        True if the directory is a bare repository
    """
    # Bare repositories have these files/directories at the root
    config_file = path / "config"
    refs_dir = path / "refs"
    head_file = path / "HEAD"

    if not (config_file.exists() and refs_dir.exists() and head_file.exists()):
        return False

    # Check if config file indicates this is a bare repo
    try:
        config_content = config_file.read_text()
        return "bare = true" in config_content
    except (OSError, UnicodeDecodeError):
        return False


def validate_repository(path: Path) -> None:
    """
    Validate that a path is a valid git repository.

    Args:
        path: Path to validate

    Raises:
        InvalidRepositoryError: If the path is not a valid git repository
    """
    if not path.exists():
        raise InvalidRepositoryError(
            f"Repository path does not exist: {path}",
            details=f"Path: {path}",
        )

    if not path.is_dir():
        raise InvalidRepositoryError(
            f"Repository path is not a directory: {path}",
            details=f"Path: {path}",
        )

    if not is_git_repository(path):
        raise InvalidRepositoryError(
            f"Directory is not a git repository: {path}",
            details=f"No .git directory or valid git structure found at {path}",
        )


def get_git_root(path: Path) -> Optional[Path]:
    """
    Find the root of a git repository by traversing up the directory tree.

    Args:
        path: Path to start searching from

    Returns:
        Path to git repository root, or None if not in a git repository
    """
    current = Path(path).resolve()

    while current != current.parent:
        if is_git_repository(current):
            return current
        current = current.parent

    return None


def is_submodule(path: Path) -> bool:
    """
    Check if a repository is a git submodule.

    Args:
        path: Path to check

    Returns:
        True if the repository is a submodule
    """
    git_dir = path / ".git"

    # Submodules typically have a .git file instead of a directory
    if git_dir.is_file():
        try:
            content = git_dir.read_text().strip()
            # Submodules have a gitdir reference pointing to .git/modules
            return "gitdir: " in content and "/.git/modules/" in content
        except (OSError, UnicodeDecodeError):
            return False

    return False


def run_git_command(
    repo_path: Path,
    args: list,
    timeout: int = 30,
    check: bool = False,
) -> Tuple[int, str, str]:
    """
    Run a git command in a repository.

    Args:
        repo_path: Path to the git repository
        args: List of git command arguments (e.g., ['status', '--porcelain'])
        timeout: Command timeout in seconds
        check: If True, raise exception on non-zero return code

    Returns:
        Tuple of (return_code, stdout, stderr)

    Raises:
        InvalidRepositoryError: If the path is not a valid repository
        subprocess.TimeoutExpired: If the command times out
        subprocess.CalledProcessError: If check=True and command fails
    """
    validate_repository(repo_path)

    cmd = ["git", "-C", str(repo_path)] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        raise
    except subprocess.CalledProcessError as e:
        raise
