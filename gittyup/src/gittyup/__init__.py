"""
Gitty Up - A professional CLI tool for synchronizing multiple git repositories.

Recursively scans a directory tree, identifies all git repositories, and executes
pull operations to ensure all projects are up-to-date.
"""

__version__ = "0.1.0"
__author__ = "Morgan"
__license__ = "MIT"

from gittyup.cli import main

__all__ = ["main", "__version__"]
