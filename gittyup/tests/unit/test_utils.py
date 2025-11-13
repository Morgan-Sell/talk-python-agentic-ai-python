"""
Unit tests for utility modules.
"""

from pathlib import Path

import pytest

from gittyup.utils.git_utils import get_git_root, is_git_repository
from gittyup.utils.path_utils import get_relative_path, normalize_path, should_exclude


class TestPathUtils:
    """Test cases for path utilities."""

    def test_normalize_path_string(self, temp_dir: Path):
        """Test normalizing a path from string."""
        path_str = str(temp_dir)
        normalized = normalize_path(path_str)

        assert isinstance(normalized, Path)
        assert normalized.is_absolute()

    def test_normalize_path_with_tilde(self):
        """Test normalizing path with tilde."""
        path = normalize_path("~/test")

        assert isinstance(path, Path)
        assert "~" not in str(path)
        assert path.is_absolute()

    def test_should_exclude_no_patterns(self, temp_dir: Path):
        """Test exclusion with no patterns."""
        result = should_exclude(temp_dir, [])
        assert result is False

    def test_should_exclude_matching_name(self, temp_dir: Path):
        """Test exclusion with matching directory name."""
        node_modules = temp_dir / "node_modules"
        node_modules.mkdir()

        result = should_exclude(node_modules, ["node_modules"])
        assert result is True

    def test_should_exclude_non_matching(self, temp_dir: Path):
        """Test exclusion with non-matching pattern."""
        project = temp_dir / "project"
        project.mkdir()

        result = should_exclude(project, ["node_modules", "venv"])
        assert result is False

    def test_get_relative_path(self, temp_dir: Path):
        """Test getting relative path."""
        subdir = temp_dir / "subdir" / "nested"
        subdir.mkdir(parents=True)

        relative = get_relative_path(subdir, temp_dir)

        assert relative == Path("subdir/nested")

    def test_get_relative_path_not_relative(self, temp_dir: Path):
        """Test getting relative path when paths are not related."""
        other_path = Path("/some/other/path")

        result = get_relative_path(other_path, temp_dir)

        # Should return the original path if not relative
        assert result == other_path


class TestGitUtils:
    """Test cases for git utilities."""

    def test_is_git_repository_true(self, sample_git_repo: Path):
        """Test detecting a valid git repository."""
        result = is_git_repository(sample_git_repo)
        assert result is True

    def test_is_git_repository_false(self, temp_dir: Path):
        """Test detecting non-git directory."""
        result = is_git_repository(temp_dir)
        assert result is False

    def test_get_git_root_found(self, sample_git_repo: Path):
        """Test finding git root."""
        # Create a subdirectory
        subdir = sample_git_repo / "subdir"
        subdir.mkdir()

        root = get_git_root(subdir)

        # Use resolve() for both to handle macOS /private/var vs /var symlink
        assert root.resolve() == sample_git_repo.resolve()

    def test_get_git_root_not_found(self, temp_dir: Path):
        """Test get_git_root when not in a git repository."""
        root = get_git_root(temp_dir)
        assert root is None
