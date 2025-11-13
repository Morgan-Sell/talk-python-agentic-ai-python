"""
Integration tests for the CLI interface.
"""

from pathlib import Path

import pytest
from click.testing import CliRunner

from gittyup.cli import main


class TestCLIIntegration:
    """Integration tests for the CLI."""

    def test_cli_help(self):
        """Test that CLI help works."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Gitty Up" in result.output
        assert "Sync multiple git repositories" in result.output

    def test_cli_version(self):
        """Test that CLI version works."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "Gitty Up" in result.output

    def test_cli_scan_empty_directory(self, temp_dir: Path):
        """Test scanning an empty directory (Phase 2: no git repos)."""
        runner = CliRunner()
        result = runner.invoke(main, [str(temp_dir)])

        assert result.exit_code == 0
        assert "Scanning" in result.output
        assert "Found 0 git" in result.output or "No git repositories found" in result.output

    def test_cli_scan_with_directories(self, sample_dir_tree: Path):
        """Test scanning a directory tree."""
        runner = CliRunner()
        result = runner.invoke(main, [str(sample_dir_tree)])

        assert result.exit_code == 0
        assert "Scanning" in result.output
        assert "Found" in result.output

    def test_cli_with_depth_limit(self, sample_dir_tree: Path):
        """Test CLI with depth limit."""
        runner = CliRunner()
        result = runner.invoke(main, [str(sample_dir_tree), "--depth", "1"])

        assert result.exit_code == 0

    def test_cli_with_exclusions(self, sample_dir_tree: Path):
        """Test CLI with exclusion patterns."""
        runner = CliRunner()
        result = runner.invoke(
            main, [str(sample_dir_tree), "--exclude", "node_modules", "--exclude", "venv"]
        )

        assert result.exit_code == 0

    def test_cli_verbose_mode(self, sample_dir_tree: Path):
        """Test CLI in verbose mode."""
        runner = CliRunner()
        result = runner.invoke(main, [str(sample_dir_tree), "--verbose"])

        assert result.exit_code == 0

    def test_cli_quiet_mode(self, sample_dir_tree: Path):
        """Test CLI in quiet mode."""
        runner = CliRunner()
        result = runner.invoke(main, [str(sample_dir_tree), "--quiet"])

        assert result.exit_code == 0

    def test_cli_dry_run(self, sample_git_tree: Path):
        """Test CLI in dry-run mode (Phase 2: git repos)."""
        runner = CliRunner()
        result = runner.invoke(main, [str(sample_git_tree), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run" in result.output or "Would execute" in result.output

    def test_cli_invalid_path(self):
        """Test CLI with invalid path."""
        runner = CliRunner()
        result = runner.invoke(main, ["/path/that/does/not/exist"])

        assert result.exit_code == 2  # Click returns 2 for invalid path

    def test_cli_no_color(self, sample_dir_tree: Path):
        """Test CLI with no-color option."""
        runner = CliRunner()
        result = runner.invoke(main, [str(sample_dir_tree), "--no-color"])

        assert result.exit_code == 0
