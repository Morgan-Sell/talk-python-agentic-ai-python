"""
Configuration file loader for Gitty Up.

Phase 1: Placeholder
Phase 4: Full implementation with YAML loading
"""

from pathlib import Path
from typing import Any, Dict

from gittyup.config.defaults import DEFAULT_CONFIG


class ConfigLoader:
    """
    Loads and merges configuration from various sources.

    Phase 1: Basic structure
    Phase 4: Full implementation
    """

    def __init__(self):
        """Initialize the configuration loader."""
        self.config = DEFAULT_CONFIG.copy()

    def load(self, config_path: Path | None = None) -> Dict[str, Any]:
        """
        Load configuration from file.

        Args:
            config_path: Optional path to configuration file

        Returns:
            Merged configuration dictionary
        """
        # Phase 4: Implement YAML loading
        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value
