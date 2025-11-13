"""
CLI interface for Gitty Up using Click framework.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from gittyup import __version__
from gittyup.core.reporter import Reporter
from gittyup.core.scanner import DirectoryScanner
from gittyup.exceptions import GittyUpError, InvalidPathError

console = Console()


@click.command()
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=".",
    required=False,
)
@click.option(
    "--depth",
    "-d",
    type=int,
    default=None,
    help="Maximum depth to scan (default: unlimited)",
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Patterns to exclude (can be used multiple times)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without executing",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed output",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Minimal output, only errors",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output",
)
@click.version_option(version=__version__, prog_name="Gitty Up")
def main(
    path: Path,
    depth: Optional[int],
    exclude: tuple,
    dry_run: bool,
    verbose: bool,
    quiet: bool,
    no_color: bool,
) -> None:
    """
    Gitty Up - Sync multiple git repositories recursively.

    Scans PATH (default: current directory) for git repositories and
    pulls updates from all remotes.

    Examples:

        gittyup                          # Scan current directory

        gittyup ~/projects               # Scan specific directory

        gittyup --depth 2 ~/projects     # Limit scan depth

        gittyup --exclude node_modules   # Exclude directories
    """
    try:
        # Disable colors if requested or if not in a TTY
        if no_color or not sys.stdout.isatty():
            console.no_color = True

        # Create reporter with appropriate verbosity
        reporter = Reporter(console=console, verbose=verbose, quiet=quiet)

        # Validate path
        if not path.exists():
            raise InvalidPathError(f"Path does not exist: {path}")

        if not path.is_dir():
            raise InvalidPathError(f"Path is not a directory: {path}")

        # Display startup message
        reporter.info(f"🔍 Scanning for directories in: {path}")

        # Create scanner with options
        scanner = DirectoryScanner(
            root_path=path,
            max_depth=depth,
            exclude_patterns=list(exclude) if exclude else None,
        )

        # Perform scan
        directories = scanner.scan()

        # Report results
        reporter.success(f"Found {len(directories)} directories")

        if verbose:
            for directory in directories:
                reporter.info(f"  • {directory}")

        if dry_run:
            reporter.info("\n✓ Dry run complete - no changes made")

        sys.exit(0)

    except GittyUpError as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]✗ Unexpected error:[/red] {str(e)}")
        if verbose:
            console.print_exception()
        sys.exit(2)


if __name__ == "__main__":
    main()
