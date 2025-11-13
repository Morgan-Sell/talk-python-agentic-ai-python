"""
End-to-end integration tests for Gitty Up.
"""

from pathlib import Path

import pytest

from gittyup.core.reporter import Reporter
from gittyup.core.scanner import DirectoryScanner


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_scan_and_report_workflow(self, sample_dir_tree: Path):
        """Test complete scan and report workflow."""
        # Create scanner
        scanner = DirectoryScanner(root_path=sample_dir_tree)

        # Perform scan
        directories = scanner.scan()

        # Create reporter
        reporter = Reporter(verbose=False, quiet=False)

        # Report findings
        reporter.success(f"Found {len(directories)} directories")

        # Get statistics
        stats = scanner.get_statistics()

        assert stats["directories_found"] == len(directories)
        assert "root_path" in stats

    def test_scan_with_exclusions_workflow(self, sample_dir_tree: Path):
        """Test scan workflow with exclusions."""
        # Create scanner with exclusions
        scanner = DirectoryScanner(
            root_path=sample_dir_tree, exclude_patterns=["node_modules", "venv"]
        )

        # Perform scan
        directories = scanner.scan()

        # Verify exclusions worked
        dir_names = [d.name for d in directories]
        assert "node_modules" not in dir_names
        assert "venv" not in dir_names

    def test_scan_with_depth_limit_workflow(self, sample_dir_tree: Path):
        """Test scan workflow with depth limit."""
        # Scan without depth limit
        scanner_unlimited = DirectoryScanner(root_path=sample_dir_tree)
        all_directories = scanner_unlimited.scan()

        # Scan with depth limit
        scanner_limited = DirectoryScanner(root_path=sample_dir_tree, max_depth=1)
        limited_directories = scanner_limited.scan()

        # Limited scan should find fewer or equal directories
        assert len(limited_directories) <= len(all_directories)
