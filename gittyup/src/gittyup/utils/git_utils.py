"""
Git-related utilities for Gitty Up.

Phase 1: Basic structure
Phase 2: Full git repository detection and validation
"""

from pathlib import Path


def is_git_repository(path: Path) -> bool:
    """
    Check if a directory is a git repository.

    Args:
        path: Path to check

    Returns:
        True if the directory contains a .git folder, False otherwise
    """
    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def get_git_root(path: Path) -> Path | None:
    """
    Find the root of a git repository.

    Args:
        path: Path to start searching from

    Returns:
        Path to git repository root, or None if not in a git repository
    """
    current = path.resolve()

    while current != current.parent:
        if is_git_repository(current):
            return current
        current = current.parent

    return None
