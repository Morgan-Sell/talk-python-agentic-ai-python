"""
CLI interface for Gitty Up using Click framework.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from gittyup import __version__
from gittyup.core.executor import GitExecutor
from gittyup.core.reporter import Reporter
from gittyup.core.scanner import RepositoryScanner
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
    "--operation",
    "-o",
    type=click.Choice(["pull", "fetch", "status"], case_sensitive=False),
    default="pull",
    help="Git operation to perform (default: pull)",
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
    "--parallel/--no-parallel",
    default=True,
    help="Execute operations in parallel (default: enabled)",
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
    operation: str,
    depth: Optional[int],
    exclude: tuple,
    dry_run: bool,
    parallel: bool,
    verbose: bool,
    quiet: bool,
    no_color: bool,
) -> None:
    """
    Gitty Up - Sync multiple git repositories recursively.

    Scans PATH (default: current directory) for git repositories and
    performs git operations (pull, fetch, or status) on all discovered repos.

    Examples:

        gittyup                              # Pull all repos in current directory

        gittyup ~/projects                   # Pull all repos in ~/projects

        gittyup --operation fetch ~/projects # Fetch instead of pull

        gittyup --depth 2 ~/projects         # Limit scan depth

        gittyup --exclude node_modules       # Exclude directories

        gittyup --dry-run                    # Show what would be done
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
        reporter.info(f"🔍 Scanning for git repositories in: {path}")

        # Create scanner with options
        scanner = RepositoryScanner(
            root_path=path,
            max_depth=depth,
            exclude_patterns=list(exclude) if exclude else None,
        )

        # Perform scan
        scan_result = scanner.scan()

        # Report scan results
        reporter.info(
            f"✓ Found {len(scan_result.repositories)} git "
            f"{'repository' if len(scan_result.repositories) == 1 else 'repositories'}"
        )

        if len(scan_result.repositories) == 0:
            reporter.warning("No git repositories found")
            sys.exit(0)

        if verbose:
            for repo in scan_result.repositories:
                reporter.info(f"  • {repo.display_path}")

        # If only scanning (no operation), exit here
        if operation == "status" and not dry_run:
            for repo in scan_result.repositories:
                reporter.info(f"\n{repo.name}:")
                reporter.info(f"  Branch: {repo.current_branch or 'unknown'}")
                if repo.remote_url:
                    reporter.info(f"  Remote: {repo.remote_url}")
                reporter.info(f"  State: {repo.state.value}")
            sys.exit(0)

        # Execute git operations
        if dry_run:
            reporter.info(f"\n[Dry run] Would execute 'git {operation}' on {len(scan_result.repositories)} repositories")
            for repo in scan_result.repositories:
                reporter.info(f"  • {repo.display_path}")
        else:
            reporter.info(f"\n🔄 Executing 'git {operation}' on repositories...")

            # Create executor
            executor = GitExecutor()

            # Execute operation on all repositories
            summary = executor.execute_batch(
                repositories=scan_result.repositories,
                operation=operation,
                dry_run=dry_run,
                parallel=parallel,
            )

            # Report results
            reporter.info("\n" + "=" * 50)
            reporter.info("Summary:")
            reporter.success(f"  ✓ Successful: {summary.successful}")
            if summary.warnings > 0:
                reporter.warning(f"  ⚠ Warnings: {summary.warnings}")
            if summary.errors > 0:
                reporter.error(f"  ✗ Errors: {summary.errors}")
            if summary.skipped > 0:
                reporter.info(f"  - Skipped: {summary.skipped}")

            reporter.info(f"  Duration: {summary.total_duration:.2f}s")

            # Show individual results if verbose
            if verbose:
                reporter.info("\nDetailed results:")
                for result in summary.results:
                    if result.is_success:
                        reporter.success(f"  ✓ {result.repository.name}: {result.message}")
                    elif result.is_error:
                        reporter.error(f"  ✗ {result.repository.name}: {result.message}")
                    elif result.is_warning:
                        reporter.warning(f"  ⚠ {result.repository.name}: {result.message}")

            # Exit with appropriate code
            sys.exit(1 if summary.errors > 0 else 0)

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
