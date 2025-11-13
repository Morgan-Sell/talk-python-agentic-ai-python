"""
Unit tests for data models.
"""

from pathlib import Path

import pytest

from gittyup.core.models import (
    ExecutionSummary,
    OperationResult,
    OperationStatus,
    Repository,
    RepositoryState,
    ScanResult,
)


class TestRepository:
    """Tests for Repository model."""

    def test_repository_creation(self, tmp_path):
        """Test creating a Repository object."""
        repo = Repository(
            path=tmp_path,
            name="test-repo",
            current_branch="main",
            remote_url="https://github.com/user/repo.git",
        )

        assert repo.path == tmp_path
        assert repo.name == "test-repo"
        assert repo.current_branch == "main"
        assert repo.remote_url == "https://github.com/user/repo.git"

    def test_repository_str_representation(self, tmp_path):
        """Test string representation of Repository."""
        repo = Repository(path=tmp_path, name="test-repo")
        assert "test-repo" in str(repo)
        assert str(tmp_path) in str(repo)

    def test_display_path_with_home_directory(self, tmp_path):
        """Test display path shows ~ for home directory."""
        # Use actual home directory to test
        home = Path.home()
        test_path = home / "projects" / "test"
        repo = Repository(path=test_path, name="test")

        assert repo.display_path.startswith("~/")

    def test_needs_pull_property(self, tmp_path):
        """Test needs_pull property."""
        repo = Repository(path=tmp_path, name="test", commits_behind=5)
        assert repo.needs_pull is True

        repo.commits_behind = 0
        assert repo.needs_pull is False

    def test_needs_push_property(self, tmp_path):
        """Test needs_push property."""
        repo = Repository(path=tmp_path, name="test", commits_ahead=3)
        assert repo.needs_push is True

        repo.commits_ahead = 0
        assert repo.needs_push is False

    def test_is_clean_property(self, tmp_path):
        """Test is_clean property."""
        repo = Repository(path=tmp_path, name="test")
        assert repo.is_clean is True

        repo.has_uncommitted_changes = True
        assert repo.is_clean is False

        repo.has_uncommitted_changes = False
        repo.has_untracked_files = True
        assert repo.is_clean is False


class TestOperationResult:
    """Tests for OperationResult model."""

    def test_operation_result_creation(self, tmp_path):
        """Test creating an OperationResult object."""
        repo = Repository(path=tmp_path, name="test")
        result = OperationResult(
            repository=repo,
            operation="pull",
            status=OperationStatus.SUCCESS,
            message="Operation completed",
        )

        assert result.repository == repo
        assert result.operation == "pull"
        assert result.status == OperationStatus.SUCCESS
        assert result.message == "Operation completed"

    def test_operation_result_str(self, tmp_path):
        """Test string representation of OperationResult."""
        repo = Repository(path=tmp_path, name="test-repo")
        result = OperationResult(
            repository=repo,
            operation="pull",
            status=OperationStatus.SUCCESS,
            message="Success",
        )

        result_str = str(result)
        assert "test-repo" in result_str
        assert "pull" in result_str
        assert "success" in result_str

    def test_is_success_property(self, tmp_path):
        """Test is_success property."""
        repo = Repository(path=tmp_path, name="test")
        result = OperationResult(
            repository=repo,
            operation="pull",
            status=OperationStatus.SUCCESS,
            message="Success",
        )

        assert result.is_success is True

        result.status = OperationStatus.ERROR
        assert result.is_success is False

    def test_is_error_property(self, tmp_path):
        """Test is_error property."""
        repo = Repository(path=tmp_path, name="test")
        result = OperationResult(
            repository=repo,
            operation="pull",
            status=OperationStatus.ERROR,
            message="Error",
        )

        assert result.is_error is True

        result.status = OperationStatus.SUCCESS
        assert result.is_error is False

    def test_is_warning_property(self, tmp_path):
        """Test is_warning property."""
        repo = Repository(path=tmp_path, name="test")
        result = OperationResult(
            repository=repo,
            operation="pull",
            status=OperationStatus.WARNING,
            message="Warning",
        )

        assert result.is_warning is True


class TestScanResult:
    """Tests for ScanResult model."""

    def test_scan_result_creation(self, tmp_path):
        """Test creating a ScanResult object."""
        repo1 = Repository(path=tmp_path / "repo1", name="repo1")
        repo2 = Repository(path=tmp_path / "repo2", name="repo2")

        result = ScanResult(
            repositories=[repo1, repo2],
            total_scanned=10,
            duration=1.5,
        )

        assert len(result.repositories) == 2
        assert result.total_scanned == 10
        assert result.duration == 1.5

    def test_scan_result_length(self, tmp_path):
        """Test __len__ method of ScanResult."""
        repo1 = Repository(path=tmp_path / "repo1", name="repo1")
        repo2 = Repository(path=tmp_path / "repo2", name="repo2")

        result = ScanResult(repositories=[repo1, repo2])

        assert len(result) == 2

    def test_has_errors_property(self):
        """Test has_errors property."""
        result = ScanResult()
        assert result.has_errors is False

        result.errors.append("Error 1")
        assert result.has_errors is True


class TestExecutionSummary:
    """Tests for ExecutionSummary model."""

    def test_execution_summary_creation(self):
        """Test creating an ExecutionSummary object."""
        summary = ExecutionSummary(total_repositories=5)

        assert summary.total_repositories == 5
        assert summary.successful == 0
        assert summary.errors == 0

    def test_add_result_success(self, tmp_path):
        """Test adding a successful result."""
        summary = ExecutionSummary(total_repositories=1)
        repo = Repository(path=tmp_path, name="test")
        result = OperationResult(
            repository=repo,
            operation="pull",
            status=OperationStatus.SUCCESS,
            message="Success",
            duration=1.0,
        )

        summary.add_result(result)

        assert summary.total_repositories == 1
        assert summary.successful == 1
        assert summary.errors == 0
        assert summary.total_duration == 1.0

    def test_add_result_error(self, tmp_path):
        """Test adding an error result."""
        summary = ExecutionSummary(total_repositories=1)
        repo = Repository(path=tmp_path, name="test")
        result = OperationResult(
            repository=repo,
            operation="pull",
            status=OperationStatus.ERROR,
            message="Error",
        )

        summary.add_result(result)

        assert summary.total_repositories == 1
        assert summary.successful == 0
        assert summary.errors == 1

    def test_add_result_warning(self, tmp_path):
        """Test adding a warning result."""
        summary = ExecutionSummary()
        repo = Repository(path=tmp_path, name="test")
        result = OperationResult(
            repository=repo,
            operation="pull",
            status=OperationStatus.WARNING,
            message="Warning",
        )

        summary.add_result(result)

        assert summary.warnings == 1

    def test_success_rate_calculation(self, tmp_path):
        """Test success rate calculation."""
        summary = ExecutionSummary(total_repositories=4)
        repo = Repository(path=tmp_path, name="test")

        # Add 3 successful, 1 error
        for i in range(3):
            result = OperationResult(
                repository=repo,
                operation="pull",
                status=OperationStatus.SUCCESS,
                message="Success",
            )
            summary.add_result(result)

        result = OperationResult(
            repository=repo,
            operation="pull",
            status=OperationStatus.ERROR,
            message="Error",
        )
        summary.add_result(result)

        assert summary.success_rate == 75.0

    def test_success_rate_no_repositories(self):
        """Test success rate with no repositories."""
        summary = ExecutionSummary()
        assert summary.success_rate == 0.0

    def test_has_errors_property(self, tmp_path):
        """Test has_errors property."""
        summary = ExecutionSummary()
        assert summary.has_errors is False

        repo = Repository(path=tmp_path, name="test")
        result = OperationResult(
            repository=repo,
            operation="pull",
            status=OperationStatus.ERROR,
            message="Error",
        )
        summary.add_result(result)

        assert summary.has_errors is True

    def test_has_warnings_property(self, tmp_path):
        """Test has_warnings property."""
        summary = ExecutionSummary()
        assert summary.has_warnings is False

        repo = Repository(path=tmp_path, name="test")
        result = OperationResult(
            repository=repo,
            operation="pull",
            status=OperationStatus.WARNING,
            message="Warning",
        )
        summary.add_result(result)

        assert summary.has_warnings is True


class TestOperationStatus:
    """Tests for OperationStatus enum."""

    def test_status_values(self):
        """Test that all status values are available."""
        assert OperationStatus.SUCCESS.value == "success"
        assert OperationStatus.WARNING.value == "warning"
        assert OperationStatus.ERROR.value == "error"
        assert OperationStatus.SKIPPED.value == "skipped"
        assert OperationStatus.TIMEOUT.value == "timeout"


class TestRepositoryState:
    """Tests for RepositoryState enum."""

    def test_state_values(self):
        """Test that all state values are available."""
        assert RepositoryState.CLEAN.value == "clean"
        assert RepositoryState.DIRTY.value == "dirty"
        assert RepositoryState.AHEAD.value == "ahead"
        assert RepositoryState.BEHIND.value == "behind"
        assert RepositoryState.DIVERGED.value == "diverged"
        assert RepositoryState.NO_REMOTE.value == "no_remote"
        assert RepositoryState.UNKNOWN.value == "unknown"

