"""
Unit tests for GitExecutor.
"""

import subprocess
from pathlib import Path

import pytest

from gittyup.core.executor import GitExecutor
from gittyup.core.models import OperationStatus, Repository


class TestGitExecutor:
    """Tests for GitExecutor class."""

    def test_executor_initialization(self):
        """Test GitExecutor initialization."""
        executor = GitExecutor(timeout=60, max_workers=4)

        assert executor.timeout == 60
        assert executor.max_workers == 4

    def test_executor_default_values(self):
        """Test GitExecutor with default values."""
        executor = GitExecutor()

        assert executor.timeout == 300
        assert executor.max_workers is None

    def test_execute_single_in_valid_repo(self, git_repo):
        """Test executing a command in a valid repository."""
        repo_path, _ = git_repo
        executor = GitExecutor()

        repo = Repository(path=repo_path, name="test-repo")
        result = executor.execute_single(repo, operation="status")

        assert result.repository == repo
        assert result.operation == "status"
        assert result.status == OperationStatus.SUCCESS
        assert result.return_code == 0

    def test_execute_single_dry_run(self, git_repo):
        """Test executing with dry-run mode."""
        repo_path, _ = git_repo
        executor = GitExecutor()

        repo = Repository(path=repo_path, name="test-repo")
        result = executor.execute_single(repo, operation="pull", dry_run=True)

        assert result.status == OperationStatus.SKIPPED
        assert "Would execute" in result.message

    def test_execute_single_invalid_repo(self, tmp_path):
        """Test executing in an invalid repository."""
        executor = GitExecutor()
        repo = Repository(path=tmp_path, name="invalid")

        result = executor.execute_single(repo, operation="status")

        assert result.status == OperationStatus.ERROR
        assert "Invalid repository" in result.message

    def test_execute_batch_sequential(self, git_repo):
        """Test batch execution in sequential mode."""
        repo_path, _ = git_repo
        executor = GitExecutor()

        repos = [
            Repository(path=repo_path, name="test-repo"),
        ]

        summary = executor.execute_batch(repos, operation="status", parallel=False)

        assert summary.total_repositories == 1
        assert summary.successful == 1
        assert len(summary.results) == 1

    def test_execute_batch_parallel(self, git_repo):
        """Test batch execution in parallel mode."""
        repo_path, _ = git_repo
        executor = GitExecutor()

        repos = [
            Repository(path=repo_path, name="test-repo"),
        ]

        summary = executor.execute_batch(repos, operation="status", parallel=True)

        assert summary.total_repositories == 1
        assert summary.successful == 1

    def test_execute_batch_dry_run(self, git_repo):
        """Test batch execution with dry-run."""
        repo_path, _ = git_repo
        executor = GitExecutor()

        repos = [
            Repository(path=repo_path, name="test-repo"),
        ]

        summary = executor.execute_batch(repos, operation="pull", dry_run=True)

        assert summary.total_repositories == 1
        assert summary.skipped == 1

    def test_build_command_args_pull(self):
        """Test building command args for pull operation."""
        executor = GitExecutor()
        repo = Repository(path=Path("/test"), name="test")

        args = executor._build_command_args("pull", repo)

        assert "pull" in args
        assert "--no-rebase" in args

    def test_build_command_args_fetch(self):
        """Test building command args for fetch operation."""
        executor = GitExecutor()
        repo = Repository(path=Path("/test"), name="test")

        args = executor._build_command_args("fetch", repo)

        assert "fetch" in args
        assert "--all" in args
        assert "--prune" in args

    def test_build_command_args_status(self):
        """Test building command args for status operation."""
        executor = GitExecutor()
        repo = Repository(path=Path("/test"), name="test")

        args = executor._build_command_args("status", repo)

        assert "status" in args
        assert "--porcelain" in args

    def test_parse_result_success(self):
        """Test parsing successful result."""
        executor = GitExecutor()
        repo = Repository(path=Path("/test"), name="test")

        status, message = executor._parse_result(
            "pull", 0, "Already up to date.", "", repo
        )

        assert status == OperationStatus.SUCCESS
        assert "up to date" in message.lower()

    def test_parse_result_fast_forward(self):
        """Test parsing fast-forward result."""
        executor = GitExecutor()
        repo = Repository(path=Path("/test"), name="test")

        status, message = executor._parse_result(
            "pull", 0, "Updating abc123..def456\nFast-forward", "", repo
        )

        assert status == OperationStatus.SUCCESS
        assert "fast-forward" in message.lower()

    def test_parse_result_error(self):
        """Test parsing error result."""
        executor = GitExecutor()
        repo = Repository(path=Path("/test"), name="test")

        status, message = executor._parse_result(
            "pull", 1, "", "fatal: not a git repository", repo
        )

        assert status == OperationStatus.ERROR
        assert "not a git repository" in message.lower()

    def test_parse_result_permission_error(self):
        """Test parsing permission error."""
        executor = GitExecutor()
        repo = Repository(path=Path("/test"), name="test")

        status, message = executor._parse_result(
            "pull", 1, "", "error: permission denied", repo
        )

        assert status == OperationStatus.ERROR
        assert "permission denied" in message.lower()

    def test_parse_result_network_error(self):
        """Test parsing network error."""
        executor = GitExecutor()
        repo = Repository(path=Path("/test"), name="test")

        status, message = executor._parse_result(
            "pull", 1, "", "fatal: could not resolve host", repo
        )

        assert status == OperationStatus.ERROR
        assert "network error" in message.lower()

    def test_parse_result_warning(self):
        """Test parsing warning result."""
        executor = GitExecutor()
        repo = Repository(path=Path("/test"), name="test")

        status, message = executor._parse_result(
            "pull", 1, "", "warning: something happened", repo
        )

        assert status == OperationStatus.WARNING
        assert "warning" in message.lower()

    def test_batch_with_mixed_results(self, git_repo, tmp_path):
        """Test batch execution with mixed success and error results."""
        repo_path, _ = git_repo
        executor = GitExecutor()

        repos = [
            Repository(path=repo_path, name="valid-repo"),
            Repository(path=tmp_path / "invalid", name="invalid-repo"),
        ]

        summary = executor.execute_batch(repos, operation="status", parallel=False)

        assert summary.total_repositories == 2
        assert summary.successful == 1
        assert summary.errors == 1


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

