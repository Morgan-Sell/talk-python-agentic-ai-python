"""
Directory scanning module for Gitty Up.

This module is responsible for traversing directory trees and identifying
directories (Phase 1 does not include git detection yet).
"""

import os
from pathlib import Path
from typing import List, Optional, Set

from gittyup.exceptions import ScannerError
from gittyup.utils.path_utils import should_exclude


class DirectoryScanner:
    """
    Scans directory trees to find directories.

    In Phase 1, this scanner simply finds all directories within the given
    root path, respecting depth limits and exclusion patterns. Git repository
    detection will be added in Phase 2.
    """

    def __init__(
        self,
        root_path: Path,
        max_depth: Optional[int] = None,
        exclude_patterns: Optional[List[str]] = None,
        follow_symlinks: bool = True,
    ):
        """
        Initialize the DirectoryScanner.

        Args:
            root_path: The root directory to start scanning from
            max_depth: Maximum depth to traverse (None for unlimited)
            exclude_patterns: List of patterns to exclude (e.g., 'node_modules')
            follow_symlinks: Whether to follow symbolic links
        """
        self.root_path = Path(root_path).resolve()
        self.max_depth = max_depth
        self.exclude_patterns = exclude_patterns or []
        self.follow_symlinks = follow_symlinks
        self._visited_paths: Set[Path] = set()
        self._directories: List[Path] = []

    def scan(self) -> List[Path]:
        """
        Scan the directory tree and return all discovered directories.

        Returns:
            List of Path objects representing discovered directories

        Raises:
            ScannerError: If there's an error during scanning
        """
        try:
            self._directories = []
            self._visited_paths = set()
            self._scan_recursive(self.root_path, depth=0)
            return self._directories
        except Exception as e:
            raise ScannerError(f"Error scanning directory tree: {e}") from e

    def _scan_recursive(self, current_path: Path, depth: int) -> None:
        """
        Recursively scan directories.

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

                            # Add directory to results
                            self._directories.append(entry_path)

                            # Recurse into subdirectory
                            self._scan_recursive(entry_path, depth + 1)

                    except PermissionError:
                        # Skip directories we can't access
                        continue
                    except OSError:
                        # Skip entries with OS errors
                        continue

        except PermissionError:
            # Skip directories we can't read
            pass
        except OSError:
            # Skip directories with OS errors
            pass

    def get_statistics(self) -> dict:
        """
        Get statistics about the scan.

        Returns:
            Dictionary with scan statistics
        """
        return {
            "root_path": str(self.root_path),
            "max_depth": self.max_depth,
            "directories_found": len(self._directories),
            "exclude_patterns": self.exclude_patterns,
        }
