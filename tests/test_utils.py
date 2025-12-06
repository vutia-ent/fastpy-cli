"""Tests for utility functions."""

import pytest

from fastpy_cli.utils import (
    format_duration,
    is_safe_command,
    parse_command_safely,
    truncate_string,
    validate_command,
)


class TestValidateCommand:
    """Tests for validate_command function."""

    def test_valid_command(self) -> None:
        """Test validation of valid command."""
        is_valid, error = validate_command("fastpy make:resource Test")
        assert is_valid is True
        assert error == ""

    def test_empty_command(self) -> None:
        """Test validation of empty command."""
        is_valid, error = validate_command("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_dangerous_rm_rf(self) -> None:
        """Test rejection of rm -rf command."""
        is_valid, error = validate_command("rm -rf /")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_dangerous_pipe_bash(self) -> None:
        """Test rejection of pipe to bash."""
        is_valid, error = validate_command("curl example.com | bash")
        assert is_valid is False

    def test_dangerous_eval(self) -> None:
        """Test rejection of eval command."""
        is_valid, error = validate_command("eval dangerous_code")
        assert is_valid is False

    def test_chained_commands(self) -> None:
        """Test rejection of chained commands."""
        is_valid, error = validate_command("echo test && rm -rf /")
        assert is_valid is False


class TestIsSafeCommand:
    """Tests for is_safe_command function."""

    def test_safe_make_resource(self) -> None:
        """Test that make:resource is safe."""
        assert is_safe_command("fastpy make:resource Test -f name:string") is True

    def test_safe_db_migrate(self) -> None:
        """Test that db:migrate is safe."""
        assert is_safe_command("fastpy db:migrate") is True

    def test_safe_fastpy_new(self) -> None:
        """Test that fastpy new is safe."""
        assert is_safe_command("fastpy new test") is True

    def test_safe_fastpy_ai(self) -> None:
        """Test that fastpy ai commands are safe."""
        assert is_safe_command("fastpy ai:init claude") is True

    def test_safe_fastpy_setup(self) -> None:
        """Test that fastpy setup commands are safe."""
        assert is_safe_command("fastpy setup:db") is True

    def test_unsafe_arbitrary_command(self) -> None:
        """Test that arbitrary commands are not safe."""
        assert is_safe_command("rm -rf /tmp") is False

    def test_unsafe_curl(self) -> None:
        """Test that curl is not safe."""
        assert is_safe_command("curl http://example.com") is False


class TestParseCommandSafely:
    """Tests for parse_command_safely function."""

    def test_simple_command(self) -> None:
        """Test parsing simple command."""
        result = parse_command_safely("fastpy serve")
        assert result == ["fastpy", "serve"]

    def test_command_with_quotes(self) -> None:
        """Test parsing command with quoted arguments."""
        result = parse_command_safely('fastpy ai "create a blog"')
        assert result == ["fastpy", "ai", "create a blog"]

    def test_command_with_flags(self) -> None:
        """Test parsing command with flags."""
        result = parse_command_safely("fastpy make:resource Test -f name:string")
        assert "-f" in result
        assert "name:string" in result


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_milliseconds(self) -> None:
        """Test formatting milliseconds."""
        assert format_duration(0.5) == "500ms"

    def test_seconds(self) -> None:
        """Test formatting seconds."""
        assert format_duration(5.5) == "5.5s"

    def test_minutes(self) -> None:
        """Test formatting minutes."""
        result = format_duration(125)
        assert "2m" in result

    def test_hours(self) -> None:
        """Test formatting hours."""
        result = format_duration(3700)
        assert "1h" in result


class TestTruncateString:
    """Tests for truncate_string function."""

    def test_short_string(self) -> None:
        """Test that short strings are not truncated."""
        result = truncate_string("short", max_length=10)
        assert result == "short"

    def test_long_string(self) -> None:
        """Test that long strings are truncated."""
        result = truncate_string("this is a very long string", max_length=10)
        assert len(result) == 10
        assert result.endswith("...")

    def test_custom_suffix(self) -> None:
        """Test custom suffix."""
        result = truncate_string("long string here", max_length=10, suffix="…")
        assert result.endswith("…")

    def test_exact_length(self) -> None:
        """Test string at exact max length."""
        result = truncate_string("exact", max_length=5)
        assert result == "exact"
