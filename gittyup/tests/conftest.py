"""
Pytest configuration and fixtures for Gitty Up tests.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for tests.

    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_dir_tree(temp_dir: Path) -> Path:
    """
    Create a sample directory tree for testing.

    Structure:
        temp_dir/
        ├── project1/
        │   └── subdir1/
        ├── project2/
        │   ├── subdir2/
        │   └── subdir3/
        ├── node_modules/
        └── venv/

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to the root of the sample tree
    """
    # Create directory structure
    (temp_dir / "project1").mkdir()
    (temp_dir / "project1" / "subdir1").mkdir()
    (temp_dir / "project2").mkdir()
    (temp_dir / "project2" / "subdir2").mkdir()
    (temp_dir / "project2" / "subdir3").mkdir()
    (temp_dir / "node_modules").mkdir()
    (temp_dir / "venv").mkdir()

    # Create some files
    (temp_dir / "project1" / "file1.txt").write_text("test")
    (temp_dir / "project2" / "file2.txt").write_text("test")

    return temp_dir


@pytest.fixture
def sample_git_repo(temp_dir: Path) -> Path:
    """
    Create a sample git repository for testing (proper git structure).

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to the git repository
    """
    repo_dir = temp_dir / "test_repo"
    repo_dir.mkdir()

    # Create proper .git directory structure
    git_dir = repo_dir / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
    (git_dir / "config").write_text("[core]\n\trepositoryformatversion = 0\n")
    (git_dir / "refs").mkdir()
    (git_dir / "refs" / "heads").mkdir()

    return repo_dir


@pytest.fixture
def sample_git_tree(temp_dir: Path) -> Path:
    """
    Create a sample directory tree with git repositories for testing.

    Structure:
        temp_dir/
        ├── project1/.git/
        │   └── subdir1/
        ├── project2/.git/
        │   ├── subdir2/
        │   └── subdir3/
        ├── node_modules/
        └── venv/

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to the root of the sample tree
    """
    # Create directory structure
    project1 = temp_dir / "project1"
    project1.mkdir()
    (project1 / "subdir1").mkdir()

    project2 = temp_dir / "project2"
    project2.mkdir()
    (project2 / "subdir2").mkdir()
    (project2 / "subdir3").mkdir()

    (temp_dir / "node_modules").mkdir()
    (temp_dir / "venv").mkdir()

    # Create git directories for project1
    git1 = project1 / ".git"
    git1.mkdir()
    (git1 / "HEAD").write_text("ref: refs/heads/main\n")
    (git1 / "config").write_text("[core]\n")
    (git1 / "refs").mkdir()

    # Create git directories for project2
    git2 = project2 / ".git"
    git2.mkdir()
    (git2 / "HEAD").write_text("ref: refs/heads/main\n")
    (git2 / "config").write_text("[core]\n")
    (git2 / "refs").mkdir()

    # Create some files
    (project1 / "file1.txt").write_text("test")
    (project2 / "file2.txt").write_text("test")

    return temp_dir


@pytest.fixture
def multiple_git_repos(temp_dir: Path) -> Path:
    """
    Create multiple git repositories for testing.

    Structure:
        temp_dir/
        ├── repo1/.git/
        ├── repo2/.git/
        └── nested/
            └── repo3/.git/

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to the root directory containing repos
    """
    # Create repo1
    repo1 = temp_dir / "repo1"
    repo1.mkdir()
    (repo1 / ".git").mkdir()

    # Create repo2
    repo2 = temp_dir / "repo2"
    repo2.mkdir()
    (repo2 / ".git").mkdir()

    # Create nested repo3
    nested = temp_dir / "nested"
    nested.mkdir()
    repo3 = nested / "repo3"
    repo3.mkdir()
    (repo3 / ".git").mkdir()

    return temp_dir
