"""Tests for configuration module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from fastpy_cli.config import (
    Config,
    DEFAULT_CONFIG,
    get_config,
    init_config_file,
)


class TestConfig:
    """Tests for Config class."""

    def test_default_values(self, clean_config: Path) -> None:
        """Test that default values are set."""
        # Reset singleton for clean test
        Config._instance = None

        config = get_config()
        assert config.ai_provider == "anthropic"
        assert config.ai_timeout == 30
        assert config.ai_max_retries == 3

    def test_get_value(self, clean_config: Path) -> None:
        """Test getting configuration values."""
        Config._instance = None
        config = get_config()

        assert config.get("ai", "provider") == "anthropic"
        assert config.get("nonexistent", "key", "default") == "default"

    def test_set_value(self, clean_config: Path) -> None:
        """Test setting configuration values."""
        Config._instance = None
        config = get_config()

        config.set("ai", "provider", "openai")
        assert config.get("ai", "provider") == "openai"

    def test_env_override(
        self, clean_config: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that environment variables override config."""
        Config._instance = None
        monkeypatch.setenv("FASTPY_AI_PROVIDER", "ollama")

        config = get_config()
        assert config.ai_provider == "ollama"

    def test_as_dict(self, clean_config: Path) -> None:
        """Test converting config to dictionary."""
        Config._instance = None
        config = get_config()

        config_dict = config.as_dict()
        assert isinstance(config_dict, dict)
        assert "ai" in config_dict


class TestInitConfigFile:
    """Tests for init_config_file function."""

    def test_creates_config_file(self, clean_config: Path) -> None:
        """Test that init creates config file."""
        Config._instance = None
        from fastpy_cli.config import CONFIG_FILE

        # Ensure file doesn't exist
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()

        path = init_config_file()
        assert path.exists()

    def test_config_file_content(self, clean_config: Path) -> None:
        """Test that config file has expected content."""
        Config._instance = None
        from fastpy_cli.config import CONFIG_FILE

        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()

        init_config_file()

        content = CONFIG_FILE.read_text()
        assert "[ai]" in content
        assert "provider" in content


class TestConfigProperties:
    """Tests for config property accessors."""

    def test_ai_provider(self, clean_config: Path) -> None:
        """Test ai_provider property."""
        Config._instance = None
        config = get_config()
        assert isinstance(config.ai_provider, str)

    def test_ai_timeout(self, clean_config: Path) -> None:
        """Test ai_timeout property."""
        Config._instance = None
        config = get_config()
        assert isinstance(config.ai_timeout, int)
        assert config.ai_timeout > 0

    def test_default_branch(self, clean_config: Path) -> None:
        """Test default_branch property."""
        Config._instance = None
        config = get_config()
        assert config.default_branch == "main"

    def test_default_git(self, clean_config: Path) -> None:
        """Test default_git property."""
        Config._instance = None
        config = get_config()
        assert isinstance(config.default_git, bool)
