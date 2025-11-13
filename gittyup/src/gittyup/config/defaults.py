"""
Default configuration values for Gitty Up.
"""

DEFAULT_CONFIG = {
    "scan": {
        "max_depth": None,
        "follow_symlinks": True,
        "exclude_patterns": [
            "node_modules",
            "venv",
            ".venv",
            "env",
            ".env",
            "__pycache__",
            ".tox",
            ".pytest_cache",
            ".mypy_cache",
            "build",
            "dist",
            "*.egg-info",
        ],
    },
    "git": {
        "operation": "pull",
        "args": ["--all"],
        "timeout": 300,
        "retry_attempts": 3,
        "retry_delay": 5,
    },
    "execution": {
        "parallel": True,
        "max_workers": 4,
        "sequential_on_error": False,
    },
    "output": {
        "color": "auto",
        "verbosity": "normal",
        "show_progress": True,
        "show_summary": True,
        "format": "text",
    },
    "logging": {
        "enabled": True,
        "level": "INFO",
        "rotate": True,
        "max_size_mb": 10,
        "backup_count": 5,
    },
}
