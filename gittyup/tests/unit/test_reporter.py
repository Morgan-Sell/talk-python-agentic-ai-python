"""
Unit tests for the Reporter module.
"""

from io import StringIO

import pytest
from rich.console import Console

from gittyup.core.reporter import Reporter


class TestReporter:
    """Test cases for Reporter class."""

    def test_reporter_initialization(self):
        """Test that reporter initializes correctly."""
        reporter = Reporter()

        assert reporter.console is not None
        assert reporter.verbose is False
        assert reporter.quiet is False

    def test_reporter_with_custom_console(self):
        """Test reporter with custom console."""
        console = Console(file=StringIO())
        reporter = Reporter(console=console, verbose=True, quiet=False)

        assert reporter.console is console
        assert reporter.verbose is True
        assert reporter.quiet is False

    def test_info_message(self):
        """Test info message output."""
        output = StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = Reporter(console=console)

        reporter.info("Test message")

        result = output.getvalue()
        assert "Test message" in result

    def test_success_message(self):
        """Test success message output."""
        output = StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = Reporter(console=console)

        reporter.success("Operation successful")

        result = output.getvalue()
        assert "Operation successful" in result
        assert "✓" in result

    def test_warning_message(self):
        """Test warning message output."""
        output = StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = Reporter(console=console)

        reporter.warning("This is a warning")

        result = output.getvalue()
        assert "This is a warning" in result
        assert "⚠" in result

    def test_error_message(self):
        """Test error message output."""
        output = StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = Reporter(console=console)

        reporter.error("This is an error")

        result = output.getvalue()
        assert "This is an error" in result
        assert "✗" in result

    def test_quiet_mode_suppresses_non_errors(self):
        """Test that quiet mode suppresses non-error messages."""
        output = StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = Reporter(console=console, quiet=True)

        reporter.info("Info message")
        reporter.success("Success message")
        reporter.warning("Warning message")

        result = output.getvalue()
        assert result == ""

    def test_quiet_mode_shows_errors(self):
        """Test that quiet mode still shows errors."""
        output = StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = Reporter(console=console, quiet=True)

        reporter.error("Error message")

        result = output.getvalue()
        assert "Error message" in result

    def test_verbose_info(self):
        """Test verbose-only messages."""
        output = StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = Reporter(console=console, verbose=True)

        reporter.verbose_info("Verbose message")

        result = output.getvalue()
        assert "Verbose message" in result

    def test_verbose_info_not_shown_in_normal_mode(self):
        """Test that verbose messages are not shown in normal mode."""
        output = StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = Reporter(console=console, verbose=False)

        reporter.verbose_info("Verbose message")

        result = output.getvalue()
        assert result == ""

    def test_print_summary(self):
        """Test summary printing."""
        output = StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = Reporter(console=console)

        stats = {
            "total_repos": 10,
            "updated": 8,
            "errors": 2,
        }

        reporter.print_summary(stats)

        result = output.getvalue()
        assert "Summary" in result
        assert "10" in result
        assert "8" in result
        assert "2" in result
