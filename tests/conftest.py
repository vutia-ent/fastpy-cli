"""Pytest configuration and fixtures for Fastpy CLI tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from fastpy_cli.main import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_project(temp_dir: Path) -> Path:
    """Create a temporary Fastpy project structure."""
    project_path = temp_dir / "test-project"
    project_path.mkdir()

    # Create cli.py to simulate a Fastpy project
    cli_py = project_path / "cli.py"
    cli_py.write_text("""#!/usr/bin/env python3
import sys
print(f"Project CLI called with: {sys.argv[1:]}")
""")

    # Create .env.example
    (project_path / ".env.example").write_text("DATABASE_URL=sqlite:///./test.db\n")

    return project_path


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")


@pytest.fixture
def clean_config(temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a clean config directory for testing."""
    config_dir = temp_dir / ".fastpy"
    config_dir.mkdir()
    monkeypatch.setattr("fastpy_cli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("fastpy_cli.config.CONFIG_FILE", config_dir / "config.toml")
    return config_dir


@pytest.fixture
def mock_httpx_response() -> MagicMock:
    """Create a mock httpx response."""
    response = MagicMock()
    response.status_code = 200
    response.raise_for_status = MagicMock()
    return response
