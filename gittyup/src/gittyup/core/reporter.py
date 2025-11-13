"""
Output and reporting module for Gitty Up.

Handles all user-facing output with colored, formatted text.
"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class Reporter:
    """
    Handles formatted output for Gitty Up operations.

    Supports different verbosity levels and colored output.
    """

    def __init__(
        self,
        console: Optional[Console] = None,
        verbose: bool = False,
        quiet: bool = False,
    ):
        """
        Initialize the Reporter.

        Args:
            console: Rich Console instance (creates new one if not provided)
            verbose: Whether to show detailed output
            quiet: Whether to suppress non-error output
        """
        self.console = console or Console()
        self.verbose = verbose
        self.quiet = quiet

    def info(self, message: str) -> None:
        """
        Display an informational message.

        Args:
            message: The message to display
        """
        if not self.quiet:
            self.console.print(message)

    def success(self, message: str) -> None:
        """
        Display a success message in green.

        Args:
            message: The message to display
        """
        if not self.quiet:
            self.console.print(f"[green]✓[/green] {message}")

    def warning(self, message: str) -> None:
        """
        Display a warning message in yellow.

        Args:
            message: The message to display
        """
        if not self.quiet:
            self.console.print(f"[yellow]⚠[/yellow] {message}")

    def error(self, message: str) -> None:
        """
        Display an error message in red.

        Args:
            message: The message to display
        """
        self.console.print(f"[red]✗[/red] {message}")

    def verbose_info(self, message: str) -> None:
        """
        Display a message only in verbose mode.

        Args:
            message: The message to display
        """
        if self.verbose and not self.quiet:
            self.console.print(f"[dim]{message}[/dim]")

    def print_summary(self, statistics: dict) -> None:
        """
        Print a formatted summary of operations.

        Args:
            statistics: Dictionary containing statistics to display
        """
        if self.quiet:
            return

        table = Table(title="Summary", show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")

        for key, value in statistics.items():
            formatted_key = key.replace("_", " ").title()
            table.add_row(formatted_key, str(value))

        self.console.print()
        self.console.print(table)

    def print_panel(self, message: str, title: Optional[str] = None, style: str = "blue") -> None:
        """
        Print a message in a panel.

        Args:
            message: The message to display
            title: Optional panel title
            style: Color style for the panel border
        """
        if not self.quiet:
            panel = Panel(message, title=title, border_style=style)
            self.console.print(panel)
