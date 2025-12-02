"""Tests for main CLI commands."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from fastpy_cli import __version__
from fastpy_cli.main import (
    app,
    check_git_installed,
    is_fastpy_project,
)


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_command(self, cli_runner: CliRunner) -> None:
        """Test that version command shows version."""
        result = cli_runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_version_flag(self, cli_runner: CliRunner) -> None:
        """Test that --version flag shows version."""
        result = cli_runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_version_short_flag(self, cli_runner: CliRunner) -> None:
        """Test that -v flag shows version."""
        result = cli_runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert __version__ in result.stdout


class TestHelpCommand:
    """Tests for help output."""

    def test_help_flag(self, cli_runner: CliRunner) -> None:
        """Test that --help shows usage."""
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "fastpy" in result.stdout.lower()
        assert "new" in result.stdout

    def test_new_help(self, cli_runner: CliRunner) -> None:
        """Test that new --help shows command help."""
        result = cli_runner.invoke(app, ["new", "--help"])
        assert result.exit_code == 0
        assert "project" in result.stdout.lower()


class TestNewCommand:
    """Tests for the new command."""

    def test_new_directory_exists(
        self, cli_runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that new fails if directory exists."""
        existing_dir = temp_dir / "existing-project"
        existing_dir.mkdir()

        with patch("fastpy_cli.main.Path.cwd", return_value=temp_dir):
            result = cli_runner.invoke(app, ["new", "existing-project"])

        assert result.exit_code == 1
        assert "already exists" in result.stdout

    @patch("fastpy_cli.main.check_git_installed")
    def test_new_git_not_installed(
        self, mock_git: MagicMock, cli_runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that new fails if git is not installed."""
        mock_git.return_value = False

        with patch("fastpy_cli.main.Path.cwd", return_value=temp_dir):
            result = cli_runner.invoke(app, ["new", "test-project"])

        assert result.exit_code == 1
        assert "git" in result.stdout.lower()

    @patch("fastpy_cli.main.clone_repository")
    @patch("fastpy_cli.main.check_git_installed")
    def test_new_clone_fails(
        self,
        mock_git: MagicMock,
        mock_clone: MagicMock,
        cli_runner: CliRunner,
        temp_dir: Path,
    ) -> None:
        """Test that new fails if clone fails."""
        mock_git.return_value = True
        mock_clone.return_value = False

        with patch("fastpy_cli.main.Path.cwd", return_value=temp_dir):
            result = cli_runner.invoke(app, ["new", "test-project"])

        assert result.exit_code == 1
        assert "failed" in result.stdout.lower()


class TestDoctorCommand:
    """Tests for the doctor command."""

    def test_doctor_runs(self, cli_runner: CliRunner) -> None:
        """Test that doctor command runs."""
        result = cli_runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "Python" in result.stdout

    def test_doctor_checks_git(self, cli_runner: CliRunner) -> None:
        """Test that doctor checks git installation."""
        result = cli_runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "Git" in result.stdout


class TestConfigCommand:
    """Tests for the config command."""

    def test_config_shows_settings(self, cli_runner: CliRunner) -> None:
        """Test that config shows settings."""
        result = cli_runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "Provider" in result.stdout

    def test_config_path_flag(self, cli_runner: CliRunner) -> None:
        """Test that config --path shows path."""
        result = cli_runner.invoke(app, ["config", "--path"])
        assert result.exit_code == 0
        assert "config" in result.stdout.lower()


class TestInitCommand:
    """Tests for the init command."""

    def test_init_creates_config(
        self, cli_runner: CliRunner, clean_config: Path
    ) -> None:
        """Test that init creates config file."""
        result = cli_runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "initialized" in result.stdout.lower() or "created" in result.stdout.lower()


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_check_git_installed(self) -> None:
        """Test git installation check."""
        # This should work on CI/CD environments
        result = check_git_installed()
        assert isinstance(result, bool)

    def test_is_fastpy_project_false(self, temp_dir: Path) -> None:
        """Test is_fastpy_project returns False for non-project."""
        with patch("fastpy_cli.main.Path.cwd", return_value=temp_dir):
            assert is_fastpy_project() is False

    def test_is_fastpy_project_true(self, temp_project: Path) -> None:
        """Test is_fastpy_project returns True for project."""
        with patch("fastpy_cli.main.Path.cwd", return_value=temp_project):
            assert is_fastpy_project() is True


class TestVerboseDebugFlags:
    """Tests for verbose and debug flags."""

    def test_verbose_flag(self, cli_runner: CliRunner) -> None:
        """Test that --verbose flag works."""
        result = cli_runner.invoke(app, ["--verbose", "version"])
        assert result.exit_code == 0

    def test_debug_flag(self, cli_runner: CliRunner) -> None:
        """Test that --debug flag works."""
        result = cli_runner.invoke(app, ["--debug", "version"])
        assert result.exit_code == 0
