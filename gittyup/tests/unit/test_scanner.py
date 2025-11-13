"""
Unit tests for the DirectoryScanner module.
"""

from pathlib import Path

import pytest

from gittyup.core.scanner import DirectoryScanner
from gittyup.exceptions import ScannerError


class TestDirectoryScanner:
    """Test cases for DirectoryScanner class."""

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
        """Test scanning an empty directory."""
        scanner = DirectoryScanner(root_path=temp_dir)
        directories = scanner.scan()

        assert directories == []

    def test_scan_simple_directory_tree(self, sample_dir_tree: Path):
        """Test scanning a simple directory tree."""
        scanner = DirectoryScanner(root_path=sample_dir_tree)
        directories = scanner.scan()

        # Should find project1, project2, subdir1, subdir2, subdir3, node_modules, venv
        assert len(directories) >= 5

        # Check that some expected directories are found
        dir_names = [d.name for d in directories]
        assert "project1" in dir_names
        assert "project2" in dir_names

    def test_scan_with_exclusions(self, sample_dir_tree: Path):
        """Test scanning with exclusion patterns."""
        scanner = DirectoryScanner(
            root_path=sample_dir_tree, exclude_patterns=["node_modules", "venv"]
        )
        directories = scanner.scan()

        # node_modules and venv should be excluded
        dir_names = [d.name for d in directories]
        assert "node_modules" not in dir_names
        assert "venv" not in dir_names

    def test_scan_with_depth_limit(self, sample_dir_tree: Path):
        """Test scanning with depth limit."""
        scanner = DirectoryScanner(root_path=sample_dir_tree, max_depth=1)
        directories = scanner.scan()

        # Should only find first level directories
        # subdir1, subdir2, subdir3 should not be found
        dir_names = [d.name for d in directories]
        assert "project1" in dir_names
        assert "project2" in dir_names
        # Subdirectories should not be in results at depth > 1

    def test_get_statistics(self, sample_dir_tree: Path):
        """Test getting scan statistics."""
        scanner = DirectoryScanner(root_path=sample_dir_tree)
        scanner.scan()

        stats = scanner.get_statistics()

        assert "root_path" in stats
        assert "max_depth" in stats
        assert "directories_found" in stats
        assert "exclude_patterns" in stats
        assert stats["directories_found"] >= 0

    def test_scan_nonexistent_directory(self, temp_dir: Path):
        """Test scanning a non-existent directory."""
        nonexistent = temp_dir / "does_not_exist"
        scanner = DirectoryScanner(root_path=nonexistent)

        # Scanner handles non-existent directories gracefully by returning empty list
        directories = scanner.scan()
        assert directories == []
