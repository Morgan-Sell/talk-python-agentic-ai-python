"""
Unit tests for the DirectoryScanner/RepositoryScanner module.
"""

import subprocess
from pathlib import Path

import pytest

from gittyup.core.scanner import DirectoryScanner, RepositoryScanner
from gittyup.exceptions import ScannerError


class TestDirectoryScanner:
    """Test cases for DirectoryScanner class (now RepositoryScanner)."""

    def test_scanner_initialization(self, temp_dir: Path):
        """Test that scanner initializes correctly."""
        scanner = DirectoryScanner(root_path=temp_dir)

        # Use resolve() for both to handle macOS /private/var vs /var symlink
        assert scanner.root_path.resolve() == temp_dir.resolve()
        assert scanner.max_depth is None
        assert scanner.exclude_patterns == []
        assert scanner.follow_symlinks is True

    def test_scanner_with_options(self, temp_dir: Path):
        """Test scanner initialization with custom options."""
        scanner = DirectoryScanner(
            root_path=temp_dir,
            max_depth=2,
            exclude_patterns=["node_modules", "venv"],
            follow_symlinks=False,
        )

        assert scanner.max_depth == 2
        assert scanner.exclude_patterns == ["node_modules", "venv"]
        assert scanner.follow_symlinks is False

    def test_scan_empty_directory(self, temp_dir: Path):
        """Test scanning an empty directory (no git repos)."""
        scanner = DirectoryScanner(root_path=temp_dir)
        result = scanner.scan()

        # Phase 2: Returns ScanResult object
        assert len(result.repositories) == 0
        assert result.total_scanned > 0

    def test_scan_simple_directory_tree(self, sample_git_tree: Path):
        """Test scanning a simple directory tree with git repositories."""
        scanner = DirectoryScanner(root_path=sample_git_tree)
        result = scanner.scan()

        # Should find git repositories (project1 and project2)
        assert len(result.repositories) >= 2

        # Check that some expected git repositories are found
        repo_names = [r.name for r in result.repositories]
        assert "project1" in repo_names
        assert "project2" in repo_names

    def test_scan_with_exclusions(self, sample_git_tree: Path):
        """Test scanning with exclusion patterns."""
        scanner = DirectoryScanner(
            root_path=sample_git_tree, exclude_patterns=["node_modules", "venv"]
        )
        result = scanner.scan()

        # node_modules and venv should be excluded
        repo_names = [r.name for r in result.repositories]
        assert "node_modules" not in repo_names
        assert "venv" not in repo_names

    def test_scan_with_depth_limit(self, sample_git_tree: Path):
        """Test scanning with depth limit."""
        scanner = DirectoryScanner(root_path=sample_git_tree, max_depth=1)
        result = scanner.scan()

        # Should only find first level repositories
        repo_names = [r.name for r in result.repositories]
        assert "project1" in repo_names
        assert "project2" in repo_names

    def test_get_statistics(self, sample_git_tree: Path):
        """Test getting scan statistics."""
        scanner = DirectoryScanner(root_path=sample_git_tree)
        scanner.scan()

        stats = scanner.get_statistics()

        assert "root_path" in stats
        assert "max_depth" in stats
        assert "repositories_found" in stats  # Phase 2: changed from directories_found
        assert "exclude_patterns" in stats
        assert stats["repositories_found"] >= 0

    def test_scan_nonexistent_directory(self, temp_dir: Path):
        """Test scanning a non-existent directory."""
        nonexistent = temp_dir / "does_not_exist"
        scanner = DirectoryScanner(root_path=nonexistent)

        # Scanner handles non-existent directories gracefully
        result = scanner.scan()
        assert len(result.repositories) == 0
        assert result.has_errors  # Phase 2: errors are tracked
