"""Configuration management for Fastpy CLI."""

import os
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

from rich.console import Console

console = Console()

# Default configuration
DEFAULT_CONFIG = {
    "ai": {
        "provider": "anthropic",
        "anthropic_model": "claude-sonnet-4-20250514",
        "openai_model": "gpt-4o",
        "ollama_model": "llama3.2",
        "ollama_host": "http://localhost:11434",
        "timeout": 30,
        "max_retries": 3,
    },
    "defaults": {
        "git": True,
        "setup": True,
        "branch": "main",
    },
    "telemetry": {
        "enabled": False,
    },
    "logging": {
        "level": "INFO",
        "file": None,
    },
}

CONFIG_DIR = Path.home() / ".fastpy"
CONFIG_FILE = CONFIG_DIR / "config.toml"


class Config:
    """Configuration manager for Fastpy CLI."""

    _instance: Optional["Config"] = None
    _config: dict[str, Any]

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = {}
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """Load configuration from file and environment."""
        # Start with defaults
        self._config = DEFAULT_CONFIG.copy()

        # Load from config file if exists
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "rb") as f:
                    file_config = tomllib.load(f)
                self._merge_config(file_config)
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Failed to load config: {e}")

        # Override with environment variables
        self._load_env_overrides()

    def _merge_config(self, new_config: dict[str, Any]) -> None:
        """Merge new configuration into existing."""
        for section, values in new_config.items():
            if section in self._config and isinstance(values, dict):
                self._config[section].update(values)
            else:
                self._config[section] = values

    def _load_env_overrides(self) -> None:
        """Load configuration overrides from environment variables."""
        env_mappings = {
            "FASTPY_AI_PROVIDER": ("ai", "provider"),
            "FASTPY_AI_TIMEOUT": ("ai", "timeout"),
            "FASTPY_AI_MAX_RETRIES": ("ai", "max_retries"),
            "OLLAMA_MODEL": ("ai", "ollama_model"),
            "OLLAMA_HOST": ("ai", "ollama_host"),
            "FASTPY_LOG_LEVEL": ("logging", "level"),
            "FASTPY_LOG_FILE": ("logging", "file"),
            "FASTPY_TELEMETRY": ("telemetry", "enabled"),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Type conversion
                if key in ("timeout", "max_retries"):
                    value = int(value)
                elif key == "enabled":
                    value = value.lower() in ("true", "1", "yes")
                self._config[section][key] = value

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value (runtime only)."""
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value

    def save(self) -> None:
        """Save current configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Convert to TOML format manually (tomllib is read-only)
        lines = []
        for section, values in self._config.items():
            lines.append(f"[{section}]")
            for key, value in values.items():
                if isinstance(value, str):
                    lines.append(f'{key} = "{value}"')
                elif isinstance(value, bool):
                    lines.append(f"{key} = {str(value).lower()}")
                elif value is None:
                    continue  # Skip None values
                else:
                    lines.append(f"{key} = {value}")
            lines.append("")

        with open(CONFIG_FILE, "w") as f:
            f.write("\n".join(lines))

    @property
    def ai_provider(self) -> str:
        """Get the configured AI provider."""
        return self.get("ai", "provider", "anthropic")

    @property
    def ai_timeout(self) -> int:
        """Get the AI request timeout."""
        return self.get("ai", "timeout", 30)

    @property
    def ai_max_retries(self) -> int:
        """Get the maximum number of retries for AI requests."""
        return self.get("ai", "max_retries", 3)

    @property
    def default_branch(self) -> str:
        """Get the default branch for cloning."""
        return self.get("defaults", "branch", "main")

    @property
    def default_git(self) -> bool:
        """Get whether to initialize git by default."""
        return self.get("defaults", "git", True)

    @property
    def default_setup(self) -> bool:
        """Get whether to run setup by default."""
        return self.get("defaults", "setup", True)

    @property
    def log_level(self) -> str:
        """Get the logging level."""
        return self.get("logging", "level", "INFO")

    @property
    def log_file(self) -> Optional[str]:
        """Get the log file path."""
        return self.get("logging", "file")

    def as_dict(self) -> dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()


def get_config() -> Config:
    """Get the global configuration instance."""
    return Config()


def init_config_file() -> Path:
    """Initialize a new configuration file with defaults."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_FILE.exists():
        return CONFIG_FILE

    # Create default config file
    default_content = '''# Fastpy CLI Configuration
# Documentation: https://fastpy.ve.ke/cli/config

[ai]
provider = "anthropic"  # anthropic, openai, ollama
# anthropic_model = "claude-sonnet-4-20250514"
# openai_model = "gpt-4o"
# ollama_model = "llama3.2"
# ollama_host = "http://localhost:11434"
timeout = 30
max_retries = 3

[defaults]
git = true
setup = true
branch = "main"

[telemetry]
enabled = false

[logging]
level = "INFO"
# file = "/path/to/fastpy.log"
'''

    with open(CONFIG_FILE, "w") as f:
        f.write(default_content)

    return CONFIG_FILE
