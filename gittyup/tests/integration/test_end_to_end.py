"""
End-to-end integration tests for Gitty Up (Phase 2: Git repository scanning).
"""

from pathlib import Path

import pytest

from gittyup.core.reporter import Reporter
from gittyup.core.scanner import DirectoryScanner


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_scan_and_report_workflow(self, sample_git_tree: Path):
        """Test complete scan and report workflow."""
        # Create scanner
        scanner = DirectoryScanner(root_path=sample_git_tree)

        # Perform scan (Phase 2: returns ScanResult)
        result = scanner.scan()

        # Create reporter
        reporter = Reporter(verbose=False, quiet=False)

        # Report findings
        reporter.success(f"Found {len(result.repositories)} repositories")

        # Get statistics
        stats = scanner.get_statistics()

        assert stats["repositories_found"] == len(result.repositories)
        assert "root_path" in stats

    def test_scan_with_exclusions_workflow(self, sample_git_tree: Path):
        """Test scan workflow with exclusions."""
        # Create scanner with exclusions
        scanner = DirectoryScanner(
            root_path=sample_git_tree, exclude_patterns=["node_modules", "venv"]
        )

        # Perform scan (Phase 2: returns ScanResult)
        result = scanner.scan()

        # Verify exclusions worked
        repo_names = [r.name for r in result.repositories]
        assert "node_modules" not in repo_names
        assert "venv" not in repo_names

    def test_scan_with_depth_limit_workflow(self, sample_git_tree: Path):
        """Test scan workflow with depth limit."""
        # Scan without depth limit
        scanner_unlimited = DirectoryScanner(root_path=sample_git_tree)
        all_repos = scanner_unlimited.scan()

        # Scan with depth limit
        scanner_limited = DirectoryScanner(root_path=sample_git_tree, max_depth=1)
        limited_repos = scanner_limited.scan()

        # Limited scan should find fewer or equal repositories
        assert len(limited_repos.repositories) <= len(all_repos.repositories)
