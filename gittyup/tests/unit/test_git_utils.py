"""
Unit tests for git_utils module.
"""

import subprocess
from pathlib import Path

import pytest

from gittyup.exceptions import InvalidRepositoryError
from gittyup.utils.git_utils import (
    get_git_root,
    is_git_repository,
    is_submodule,
    run_git_command,
    validate_repository,
)


class TestIsGitRepository:
    """Tests for is_git_repository function."""

    def test_valid_git_repository(self, tmp_path):
        """Test detection of a valid git repository."""
        # Create a mock .git directory with required files
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        (git_dir / "config").write_text("[core]\n")
        (git_dir / "refs").mkdir()

        assert is_git_repository(tmp_path) is True

    def test_non_git_directory(self, tmp_path):
        """Test detection of a non-git directory."""
        assert is_git_repository(tmp_path) is False

    def test_incomplete_git_directory(self, tmp_path):
        """Test detection of incomplete .git directory."""
        # Create .git directory but without required files
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        assert is_git_repository(tmp_path) is False

    def test_git_worktree(self, tmp_path):
        """Test detection of a git worktree."""
        # Create a .git file (worktree marker)
        git_file = tmp_path / ".git"
        git_file.write_text("gitdir: /some/path/.git/worktrees/test\n")

        assert is_git_repository(tmp_path) is True

    def test_bare_repository(self, tmp_path):
        """Test detection of a bare repository."""
        # Create bare repository structure
        (tmp_path / "config").write_text("[core]\nbare = true\n")
        (tmp_path / "HEAD").write_text("ref: refs/heads/main\n")
        (tmp_path / "refs").mkdir()

        assert is_git_repository(tmp_path) is True


class TestValidateRepository:
    """Tests for validate_repository function."""

    def test_validate_valid_repository(self, tmp_path):
        """Test validation of a valid repository."""
        # Create a mock git repository
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        (git_dir / "config").write_text("[core]\n")
        (git_dir / "refs").mkdir()

        # Should not raise an exception
        validate_repository(tmp_path)

    def test_validate_nonexistent_path(self, tmp_path):
        """Test validation of non-existent path."""
        nonexistent = tmp_path / "does_not_exist"

        with pytest.raises(InvalidRepositoryError) as exc_info:
            validate_repository(nonexistent)

        assert "does not exist" in str(exc_info.value)

    def test_validate_file_instead_of_directory(self, tmp_path):
        """Test validation of a file instead of directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        with pytest.raises(InvalidRepositoryError) as exc_info:
            validate_repository(file_path)

        assert "not a directory" in str(exc_info.value)

    def test_validate_non_git_directory(self, tmp_path):
        """Test validation of a non-git directory."""
        with pytest.raises(InvalidRepositoryError) as exc_info:
            validate_repository(tmp_path)

        assert "not a git repository" in str(exc_info.value)


class TestGetGitRoot:
    """Tests for get_git_root function."""

    def test_find_git_root_from_root(self, tmp_path):
        """Test finding git root from repository root."""
        # Create a mock git repository
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        (git_dir / "config").write_text("[core]\n")
        (git_dir / "refs").mkdir()

        root = get_git_root(tmp_path)
        assert root == tmp_path

    def test_find_git_root_from_subdirectory(self, tmp_path):
        """Test finding git root from a subdirectory."""
        # Create a mock git repository
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        (git_dir / "config").write_text("[core]\n")
        (git_dir / "refs").mkdir()

        # Create a subdirectory
        subdir = tmp_path / "src" / "module"
        subdir.mkdir(parents=True)

        root = get_git_root(subdir)
        assert root == tmp_path

    def test_no_git_root_found(self, tmp_path):
        """Test when no git root is found."""
        root = get_git_root(tmp_path)
        assert root is None


class TestIsSubmodule:
    """Tests for is_submodule function."""

    def test_regular_repository_not_submodule(self, tmp_path):
        """Test that a regular repository is not identified as a submodule."""
        # Create a mock git repository
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        (git_dir / "config").write_text("[core]\n")
        (git_dir / "refs").mkdir()

        assert is_submodule(tmp_path) is False

    def test_submodule_detected(self, tmp_path):
        """Test detection of a git submodule."""
        # Submodules have a .git file with a gitdir reference to .git/modules
        git_file = tmp_path / ".git"
        git_file.write_text("gitdir: ../.git/modules/mysubmodule\n")

        assert is_submodule(tmp_path) is True

    def test_worktree_not_submodule(self, tmp_path):
        """Test that a worktree is not identified as a submodule."""
        # Worktrees have a different gitdir format
        git_file = tmp_path / ".git"
        git_file.write_text("gitdir: /some/path/.git/worktrees/test\n")

        assert is_submodule(tmp_path) is False

    def test_non_git_directory(self, tmp_path):
        """Test that a non-git directory is not a submodule."""
        assert is_submodule(tmp_path) is False


class TestRunGitCommand:
    """Tests for run_git_command function."""

    def test_run_command_in_valid_repo(self, git_repo_path):
        """Test running a git command in a valid repository."""
        returncode, stdout, stderr = run_git_command(
            git_repo_path, ["status", "--porcelain"]
        )

        assert returncode == 0
        assert isinstance(stdout, str)
        assert isinstance(stderr, str)

    def test_run_command_with_timeout(self, git_repo_path):
        """Test that timeout parameter is respected."""
        # This should complete quickly
        returncode, stdout, stderr = run_git_command(
            git_repo_path, ["status"], timeout=5
        )

        assert returncode == 0

    def test_run_command_in_invalid_repo(self, tmp_path):
        """Test running a command in an invalid repository raises error."""
        with pytest.raises(InvalidRepositoryError):
            run_git_command(tmp_path, ["status"])

    def test_run_command_captures_output(self, git_repo_path):
        """Test that command output is captured correctly."""
        returncode, stdout, stderr = run_git_command(
            git_repo_path, ["rev-parse", "--git-dir"]
        )

        assert returncode == 0
        assert ".git" in stdout


@pytest.fixture
def git_repo_path(tmp_path):
    """Create a real git repository for testing."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    # Create an initial commit
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    return tmp_path

