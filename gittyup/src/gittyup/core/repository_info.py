"""
Repository information extraction module.

This module provides functions to extract metadata and state information
from git repositories.
"""

from pathlib import Path
from typing import Optional, Tuple

from gittyup.core.models import Repository, RepositoryState
from gittyup.exceptions import InvalidRepositoryError, RepositoryStateError
from gittyup.utils.git_utils import (
    is_submodule,
    run_git_command,
    validate_repository,
    _is_bare_repository,
)


def get_current_branch(repo_path: Path) -> Optional[str]:
    """
    Get the current branch name of a repository.

    Args:
        repo_path: Path to the git repository

    Returns:
        Current branch name, or None if detached HEAD or error

    Raises:
        InvalidRepositoryError: If the path is not a valid repository
    """
    try:
        returncode, stdout, stderr = run_git_command(
            repo_path, ["symbolic-ref", "--short", "HEAD"], timeout=5
        )

        if returncode == 0:
            return stdout.strip()

        # If we're in detached HEAD state, try to get the commit hash
        returncode, stdout, stderr = run_git_command(
            repo_path, ["rev-parse", "--short", "HEAD"], timeout=5
        )

        if returncode == 0:
            return f"detached@{stdout.strip()}"

        return None
    except InvalidRepositoryError:
        # Let InvalidRepositoryError propagate
        raise
    except Exception:
        return None


def get_remote_info(repo_path: Path, remote_name: str = "origin") -> Tuple[Optional[str], str]:
    """
    Get remote URL and name for a repository.

    Args:
        repo_path: Path to the git repository
        remote_name: Name of the remote to query (default: 'origin')

    Returns:
        Tuple of (remote_url, remote_name)

    Raises:
        InvalidRepositoryError: If the path is not a valid repository
    """
    try:
        # Try to get the specified remote URL
        returncode, stdout, stderr = run_git_command(
            repo_path, ["remote", "get-url", remote_name], timeout=5
        )

        if returncode == 0:
            return stdout.strip(), remote_name

        # If the specified remote doesn't exist, try to get the first available remote
        returncode, stdout, stderr = run_git_command(
            repo_path, ["remote"], timeout=5
        )

        if returncode == 0 and stdout.strip():
            first_remote = stdout.strip().split("\n")[0]
            returncode, stdout, stderr = run_git_command(
                repo_path, ["remote", "get-url", first_remote], timeout=5
            )
            if returncode == 0:
                return stdout.strip(), first_remote

        return None, remote_name
    except InvalidRepositoryError:
        # Let InvalidRepositoryError propagate
        raise
    except Exception:
        return None, remote_name


def check_uncommitted_changes(repo_path: Path) -> Tuple[bool, bool]:
    """
    Check if a repository has uncommitted changes or untracked files.

    Args:
        repo_path: Path to the git repository

    Returns:
        Tuple of (has_uncommitted_changes, has_untracked_files)

    Raises:
        InvalidRepositoryError: If the path is not a valid repository
    """
    try:
        returncode, stdout, stderr = run_git_command(
            repo_path, ["status", "--porcelain"], timeout=10
        )

        if returncode != 0:
            return False, False

        lines = stdout.strip().split("\n") if stdout.strip() else []

        has_uncommitted = False
        has_untracked = False

        for line in lines:
            if not line:
                continue

            status = line[:2]

            # Check for uncommitted changes (modified, added, deleted, etc.)
            if status[0] in ["M", "A", "D", "R", "C"] or status[1] in ["M", "D"]:
                has_uncommitted = True

            # Check for untracked files
            if status == "??":
                has_untracked = True

        return has_uncommitted, has_untracked
    except InvalidRepositoryError:
        # Let InvalidRepositoryError propagate
        raise
    except Exception:
        return False, False


def get_ahead_behind_counts(repo_path: Path, branch: str, remote: str = "origin") -> Tuple[int, int]:
    """
    Get the number of commits ahead and behind the remote.

    Args:
        repo_path: Path to the git repository
        branch: Current branch name
        remote: Remote name (default: 'origin')

    Returns:
        Tuple of (commits_ahead, commits_behind)
    """
    if not branch or branch.startswith("detached@"):
        return 0, 0

    try:
        # Try to get ahead/behind counts
        remote_branch = f"{remote}/{branch}"
        returncode, stdout, stderr = run_git_command(
            repo_path,
            ["rev-list", "--left-right", "--count", f"{remote_branch}...HEAD"],
            timeout=10,
        )

        if returncode == 0:
            parts = stdout.strip().split()
            if len(parts) == 2:
                behind = int(parts[0])
                ahead = int(parts[1])
                return ahead, behind

        return 0, 0
    except Exception:
        return 0, 0


def determine_repository_state(
    has_uncommitted: bool,
    has_untracked: bool,
    ahead: int,
    behind: int,
    has_remote: bool,
) -> RepositoryState:
    """
    Determine the overall state of a repository.

    Priority:
    1. Remote sync issues (ahead/behind/diverged)
    2. Local changes (dirty/clean)
    3. No remote configured

    Args:
        has_uncommitted: Whether there are uncommitted changes
        has_untracked: Whether there are untracked files
        ahead: Number of commits ahead of remote
        behind: Number of commits behind remote
        has_remote: Whether the repository has a remote configured

    Returns:
        RepositoryState enum value
    """
    # Check remote sync status first (if remote exists)
    if has_remote:
        if ahead > 0 and behind > 0:
            return RepositoryState.DIVERGED

        if behind > 0:
            return RepositoryState.BEHIND

        if ahead > 0:
            return RepositoryState.AHEAD

    # Check local changes
    if has_uncommitted or has_untracked:
        return RepositoryState.DIRTY

    # If no remote but clean
    if not has_remote:
        return RepositoryState.NO_REMOTE

    return RepositoryState.CLEAN


def extract_repository_info(repo_path: Path) -> Repository:
    """
    Extract comprehensive information about a git repository.

    This is the main function that gathers all repository metadata
    and returns a Repository object.

    Args:
        repo_path: Path to the git repository

    Returns:
        Repository object with all extracted information

    Raises:
        InvalidRepositoryError: If the path is not a valid repository
    """
    repo_path = Path(repo_path).resolve()

    # Validate repository
    validate_repository(repo_path)

    # Get basic info
    name = repo_path.name

    # Check if bare repository
    is_bare = _is_bare_repository(repo_path)

    # Check if submodule
    is_sub = is_submodule(repo_path)

    # Get current branch
    current_branch = get_current_branch(repo_path)

    # Get remote info
    remote_url, remote_name = get_remote_info(repo_path)

    # Check for uncommitted changes (skip for bare repos)
    has_uncommitted = False
    has_untracked = False
    if not is_bare:
        has_uncommitted, has_untracked = check_uncommitted_changes(repo_path)

    # Get ahead/behind counts (skip for bare repos and if no remote)
    ahead = 0
    behind = 0
    if not is_bare and remote_url and current_branch:
        ahead, behind = get_ahead_behind_counts(repo_path, current_branch, remote_name)

    # Determine state
    state = determine_repository_state(
        has_uncommitted, has_untracked, ahead, behind, remote_url is not None
    )

    return Repository(
        path=repo_path,
        name=name,
        current_branch=current_branch,
        remote_url=remote_url,
        remote_name=remote_name,
        has_uncommitted_changes=has_uncommitted,
        has_untracked_files=has_untracked,
        commits_ahead=ahead,
        commits_behind=behind,
        state=state,
        is_submodule=is_sub,
        is_bare=is_bare,
    )

