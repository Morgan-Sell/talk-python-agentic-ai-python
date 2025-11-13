"""
Unit tests for repository_info module.
"""

import subprocess
from pathlib import Path

import pytest

from gittyup.core.models import RepositoryState
from gittyup.core.repository_info import (
    check_uncommitted_changes,
    determine_repository_state,
    extract_repository_info,
    get_ahead_behind_counts,
    get_current_branch,
    get_remote_info,
)
from gittyup.exceptions import InvalidRepositoryError


class TestGetCurrentBranch:
    """Tests for get_current_branch function."""

    def test_get_current_branch(self, git_repo):
        """Test getting current branch name."""
        repo_path, _ = git_repo

        branch = get_current_branch(repo_path)

        # Default branch is usually 'main' or 'master'
        assert branch in ["main", "master"] or branch.startswith("detached@")

    def test_get_branch_invalid_repo(self, tmp_path):
        """Test getting branch from invalid repository."""
        with pytest.raises(InvalidRepositoryError):
            get_current_branch(tmp_path)


class TestGetRemoteInfo:
    """Tests for get_remote_info function."""

    def test_get_remote_no_remote_configured(self, git_repo):
        """Test getting remote info when no remote is configured."""
        repo_path, _ = git_repo

        remote_url, remote_name = get_remote_info(repo_path)

        # No remote configured in test repo
        assert remote_url is None
        assert remote_name == "origin"

    def test_get_remote_with_origin(self, git_repo_with_remote):
        """Test getting remote info when origin is configured."""
        repo_path = git_repo_with_remote

        remote_url, remote_name = get_remote_info(repo_path)

        assert remote_url is not None
        assert "test-remote" in remote_url
        assert remote_name == "origin"

    def test_get_remote_invalid_repo(self, tmp_path):
        """Test getting remote from invalid repository."""
        with pytest.raises(InvalidRepositoryError):
            get_remote_info(tmp_path)


class TestCheckUncommittedChanges:
    """Tests for check_uncommitted_changes function."""

    def test_check_clean_repository(self, git_repo):
        """Test checking a clean repository."""
        repo_path, _ = git_repo

        has_uncommitted, has_untracked = check_uncommitted_changes(repo_path)

        assert has_uncommitted is False
        assert has_untracked is False

    def test_check_with_uncommitted_changes(self, git_repo):
        """Test checking repository with uncommitted changes."""
        repo_path, test_file = git_repo

        # Modify the tracked file
        test_file.write_text("modified content")

        has_uncommitted, has_untracked = check_uncommitted_changes(repo_path)

        assert has_uncommitted is True

    def test_check_with_untracked_files(self, git_repo):
        """Test checking repository with untracked files."""
        repo_path, _ = git_repo

        # Create an untracked file
        (repo_path / "untracked.txt").write_text("untracked")

        has_uncommitted, has_untracked = check_uncommitted_changes(repo_path)

        assert has_untracked is True

    def test_check_invalid_repo(self, tmp_path):
        """Test checking invalid repository."""
        with pytest.raises(InvalidRepositoryError):
            check_uncommitted_changes(tmp_path)


class TestGetAheadBehindCounts:
    """Tests for get_ahead_behind_counts function."""

    def test_counts_without_remote(self, git_repo):
        """Test getting counts when no remote is configured."""
        repo_path, _ = git_repo

        ahead, behind = get_ahead_behind_counts(repo_path, "main")

        # Without remote, should return 0, 0
        assert ahead == 0
        assert behind == 0

    def test_counts_detached_head(self, git_repo):
        """Test getting counts in detached HEAD state."""
        repo_path, _ = git_repo

        ahead, behind = get_ahead_behind_counts(repo_path, "detached@abc123")

        assert ahead == 0
        assert behind == 0


class TestDetermineRepositoryState:
    """Tests for determine_repository_state function."""

    def test_state_clean(self):
        """Test determining clean state."""
        state = determine_repository_state(
            has_uncommitted=False,
            has_untracked=False,
            ahead=0,
            behind=0,
            has_remote=True,
        )

        assert state == RepositoryState.CLEAN

    def test_state_dirty(self):
        """Test determining dirty state."""
        state = determine_repository_state(
            has_uncommitted=True,
            has_untracked=False,
            ahead=0,
            behind=0,
            has_remote=True,
        )

        assert state == RepositoryState.DIRTY

    def test_state_ahead(self):
        """Test determining ahead state."""
        state = determine_repository_state(
            has_uncommitted=False,
            has_untracked=False,
            ahead=3,
            behind=0,
            has_remote=True,
        )

        assert state == RepositoryState.AHEAD

    def test_state_behind(self):
        """Test determining behind state."""
        state = determine_repository_state(
            has_uncommitted=False,
            has_untracked=False,
            ahead=0,
            behind=2,
            has_remote=True,
        )

        assert state == RepositoryState.BEHIND

    def test_state_diverged(self):
        """Test determining diverged state."""
        state = determine_repository_state(
            has_uncommitted=False,
            has_untracked=False,
            ahead=2,
            behind=3,
            has_remote=True,
        )

        assert state == RepositoryState.DIVERGED

    def test_state_no_remote(self):
        """Test determining no remote state."""
        state = determine_repository_state(
            has_uncommitted=False,
            has_untracked=False,
            ahead=0,
            behind=0,
            has_remote=False,
        )

        assert state == RepositoryState.NO_REMOTE


class TestExtractRepositoryInfo:
    """Tests for extract_repository_info function."""

    def test_extract_from_valid_repo(self, git_repo):
        """Test extracting info from a valid repository."""
        repo_path, _ = git_repo

        repo = extract_repository_info(repo_path)

        assert repo.path == repo_path
        assert repo.name == repo_path.name
        assert repo.current_branch is not None
        assert repo.is_submodule is False
        assert repo.is_bare is False

    def test_extract_from_invalid_repo(self, tmp_path):
        """Test extracting info from invalid repository."""
        with pytest.raises(InvalidRepositoryError):
            extract_repository_info(tmp_path)

    def test_extract_with_dirty_state(self, git_repo):
        """Test extracting info with uncommitted changes."""
        repo_path, test_file = git_repo

        # Make repository dirty
        test_file.write_text("modified")

        repo = extract_repository_info(repo_path)

        assert repo.has_uncommitted_changes is True
        assert repo.state == RepositoryState.DIRTY


@pytest.fixture
def git_repo(tmp_path):
    """Create a real git repository for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Create an initial commit
    test_file = repo_path / "test.txt"
    test_file.write_text("test content")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path, test_file


@pytest.fixture
def git_repo_with_remote(tmp_path):
    """Create a git repository with a remote configured."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Add a remote
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/user/test-remote.git"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Create an initial commit
    test_file = repo_path / "test.txt"
    test_file.write_text("test content")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path

