"""
Directory scanning module for Gitty Up.

This module is responsible for traversing directory trees and identifying
git repositories.
"""

import os
import time
from pathlib import Path
from typing import List, Optional, Set

from gittyup.core.models import Repository, ScanResult
from gittyup.core.repository_info import extract_repository_info
from gittyup.exceptions import ScannerError
from gittyup.utils.git_utils import is_git_repository
from gittyup.utils.path_utils import should_exclude


class RepositoryScanner:
    """
    Scans directory trees to find git repositories.

    This scanner traverses directory trees, identifies git repositories,
    and extracts comprehensive information about each repository.
    """

    def __init__(
        self,
        root_path: Path,
        max_depth: Optional[int] = None,
        exclude_patterns: Optional[List[str]] = None,
        follow_symlinks: bool = True,
        extract_info: bool = True,
    ):
        """
        Initialize the RepositoryScanner.

        Args:
            root_path: The root directory to start scanning from
            max_depth: Maximum depth to traverse (None for unlimited)
            exclude_patterns: List of patterns to exclude (e.g., 'node_modules')
            follow_symlinks: Whether to follow symbolic links
            extract_info: Whether to extract detailed info from repositories
        """
        self.root_path = Path(root_path).resolve()
        self.max_depth = max_depth
        self.exclude_patterns = exclude_patterns or []
        self.follow_symlinks = follow_symlinks
        self.extract_info = extract_info
        self._visited_paths: Set[Path] = set()
        self._repositories: List[Repository] = []
        self._errors: List[str] = []
        self._directories_scanned: int = 0

    def scan(self) -> ScanResult:
        """
        Scan the directory tree and return all discovered git repositories.

        Returns:
            ScanResult with discovered repositories and scan statistics

        Raises:
            ScannerError: If there's a critical error during scanning
        """
        start_time = time.time()

        try:
            self._repositories = []
            self._visited_paths = set()
            self._errors = []
            self._directories_scanned = 0

            # Check if root path itself is a git repository
            if is_git_repository(self.root_path):
                self._add_repository(self.root_path)
            else:
                # Scan subdirectories
                self._scan_recursive(self.root_path, depth=0)

            duration = time.time() - start_time

            return ScanResult(
                repositories=self._repositories,
                total_scanned=self._directories_scanned,
                duration=duration,
                errors=self._errors,
            )

        except Exception as e:
            raise ScannerError(f"Error scanning directory tree: {e}") from e

    def scan_paths_only(self) -> List[Path]:
        """
        Scan and return only repository paths (faster, no info extraction).

        Returns:
            List of Path objects representing git repositories
        """
        original_extract_info = self.extract_info
        self.extract_info = False

        try:
            result = self.scan()
            return [repo.path for repo in result.repositories]
        finally:
            self.extract_info = original_extract_info

    def _scan_recursive(self, current_path: Path, depth: int) -> None:
        """
        Recursively scan directories looking for git repositories.

        Args:
            current_path: The current directory being scanned
            depth: Current depth in the tree
        """
        # Check depth limit
        if self.max_depth is not None and depth > self.max_depth:
            return

        # Handle symlinks (prevent cycles)
        if current_path.is_symlink():
            if not self.follow_symlinks:
                return
            real_path = current_path.resolve()
            if real_path in self._visited_paths:
                return  # Already visited, prevent infinite loop
            self._visited_paths.add(real_path)

        # Check if directory should be excluded
        if should_exclude(current_path, self.exclude_patterns):
            return

        self._directories_scanned += 1

        try:
            # Use scandir for better performance
            with os.scandir(current_path) as entries:
                for entry in entries:
                    try:
                        # Only process directories
                        if entry.is_dir(follow_symlinks=self.follow_symlinks):
                            entry_path = Path(entry.path)

                            # Skip if excluded
                            if should_exclude(entry_path, self.exclude_patterns):
                                continue

                            # Check if this is a git repository
                            if is_git_repository(entry_path):
                                self._add_repository(entry_path)
                                # Don't recurse into git repositories
                                # (avoid finding nested .git directories)
                                continue

                            # Recurse into subdirectory
                            self._scan_recursive(entry_path, depth + 1)

                    except PermissionError:
                        # Skip directories we can't access
                        self._errors.append(f"Permission denied: {entry.path}")
                        continue
                    except OSError as e:
                        # Skip entries with OS errors
                        self._errors.append(f"OS error at {entry.path}: {e}")
                        continue

        except PermissionError:
            # Skip directories we can't read
            self._errors.append(f"Permission denied: {current_path}")
        except OSError as e:
            # Skip directories with OS errors
            self._errors.append(f"OS error at {current_path}: {e}")

    def _add_repository(self, repo_path: Path) -> None:
        """
        Add a git repository to the results.

        Args:
            repo_path: Path to the git repository
        """
        try:
            if self.extract_info:
                # Extract full repository information
                repo = extract_repository_info(repo_path)
                self._repositories.append(repo)
            else:
                # Create minimal repository object (just path and name)
                repo = Repository(path=repo_path, name=repo_path.name)
                self._repositories.append(repo)
        except Exception as e:
            # Log error but continue scanning
            self._errors.append(f"Failed to extract info from {repo_path}: {e}")

    def get_statistics(self) -> dict:
        """
        Get statistics about the scan.

        Returns:
            Dictionary with scan statistics
        """
        return {
            "root_path": str(self.root_path),
            "max_depth": self.max_depth,
            "repositories_found": len(self._repositories),
            "directories_scanned": self._directories_scanned,
            "errors": len(self._errors),
            "exclude_patterns": self.exclude_patterns,
        }


# Keep DirectoryScanner as alias for backwards compatibility with Phase 1 tests
DirectoryScanner = RepositoryScanner
