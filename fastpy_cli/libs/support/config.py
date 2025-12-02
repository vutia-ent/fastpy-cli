"""
Configuration Manager - Centralized configuration access.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
import json

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore


class Config:
    """
    Configuration manager with dot notation access.

    Usage:
        config = Config()
        config.load_from_env()

        # Access with dot notation
        database_url = config.get('database.url')

        # With default
        debug = config.get('app.debug', False)

        # Set values
        config.set('cache.driver', 'redis')
    """

    _instance: Optional["Config"] = None
    _config: Dict[str, Any]

    def __new__(cls) -> "Config":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = {}
        return cls._instance

    def load(self, config: Dict[str, Any]) -> "Config":
        """Load configuration from a dictionary."""
        self._merge(self._config, config)
        return self

    def load_from_file(self, path: Union[str, Path]) -> "Config":
        """Load configuration from a file (JSON or TOML)."""
        path = Path(path)

        if not path.exists():
            return self

        content = path.read_bytes()

        if path.suffix == ".json":
            data = json.loads(content)
        elif path.suffix in (".toml", ".tml"):
            data = tomllib.loads(content.decode())
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")

        return self.load(data)

    def load_from_env(self, prefix: str = "FASTPY_") -> "Config":
        """
        Load configuration from environment variables.

        Environment variables are converted using the pattern:
        FASTPY_DATABASE_URL -> database.url
        """
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to dot notation
                config_key = key[len(prefix):].lower().replace("__", ".").replace("_", ".")
                self.set(config_key, self._parse_env_value(value))

        return self

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Boolean
        if value.lower() in ("true", "1", "yes", "on"):
            return True
        if value.lower() in ("false", "0", "no", "off"):
            return False

        # Number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # JSON array/object
        if value.startswith(("[", "{")):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        return value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: The configuration key (e.g., 'database.url')
            default: Default value if key doesn't exist
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> "Config":
        """
        Set a configuration value using dot notation.

        Args:
            key: The configuration key (e.g., 'database.url')
            value: The value to set
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        return self

    def has(self, key: str) -> bool:
        """Check if a configuration key exists."""
        return self.get(key) is not None

    def all(self) -> Dict[str, Any]:
        """Get all configuration."""
        return self._config.copy()

    def _merge(self, base: Dict, update: Dict) -> Dict:
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge(base[key], value)
            else:
                base[key] = value
        return base

    @classmethod
    def get_instance(cls) -> "Config":
        """Get the global config instance."""
        return cls()


# Global config instance
config = Config()
