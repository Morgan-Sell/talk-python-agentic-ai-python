"""
Path manipulation utilities for Gitty Up.
"""

from pathlib import Path
from typing import List


def normalize_path(path: str | Path) -> Path:
    """
    Normalize a path to an absolute Path object.

    Args:
        path: Path as string or Path object

    Returns:
        Normalized absolute Path object
    """
    return Path(path).expanduser().resolve()


def should_exclude(path: Path, patterns: List[str]) -> bool:
    """
    Check if a path should be excluded based on patterns.

    Args:
        path: Path to check
        patterns: List of exclusion patterns (simple string matching for Phase 1)

    Returns:
        True if the path should be excluded, False otherwise
    """
    if not patterns:
        return False

    path_str = str(path)
    path_name = path.name

    for pattern in patterns:
        # Simple pattern matching for Phase 1
        # Check if pattern matches directory name or is in path
        if pattern in path_str or pattern == path_name:
            return True

    return False


def get_relative_path(path: Path, base: Path) -> Path:
    """
    Get relative path from base to path.

    Args:
        path: Target path
        base: Base path

    Returns:
        Relative path from base to path
    """
    try:
        return path.relative_to(base)
    except ValueError:
        # If path is not relative to base, return the original path
        return path
