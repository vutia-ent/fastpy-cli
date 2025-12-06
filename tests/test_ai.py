"""Tests for AI module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from fastpy_cli.ai import (
    AnthropicProvider,
    OllamaProvider,
    OpenAIProvider,
    get_provider,
    parse_ai_response,
    validate_json_schema,
    COMMAND_SCHEMA,
)


class TestParseAIResponse:
    """Tests for parse_ai_response function."""

    def test_parse_valid_json(self) -> None:
        """Test parsing valid JSON response."""
        response = json.dumps([
            {"command": "fastpy make:resource Test -f name:string", "description": "Test resource"},
        ])
        result = parse_ai_response(response)
        assert len(result) == 1
        assert result[0]["command"] == "fastpy make:resource Test -f name:string"

    def test_parse_json_with_markdown(self) -> None:
        """Test parsing JSON wrapped in markdown code blocks."""
        response = """```json
[
    {"command": "fastpy make:resource Test -f name:string", "description": "Test"}
]
```"""
        result = parse_ai_response(response)
        assert len(result) == 1

    def test_parse_invalid_json(self) -> None:
        """Test parsing invalid JSON returns empty list."""
        response = "not valid json"
        result = parse_ai_response(response)
        assert result == []

    def test_parse_filters_invalid_commands(self) -> None:
        """Test that invalid commands are filtered out."""
        response = json.dumps([
            {"command": "fastpy make:resource Valid -f name:string", "description": "Valid"},
            {"command": "rm -rf /", "description": "Invalid command"},
        ])
        result = parse_ai_response(response)
        assert len(result) == 1
        assert "make:resource" in result[0]["command"]

    def test_parse_empty_response(self) -> None:
        """Test parsing empty response."""
        result = parse_ai_response("")
        assert result == []


class TestValidateJsonSchema:
    """Tests for JSON schema validation."""

    def test_valid_command_array(self) -> None:
        """Test validation of valid command array."""
        data = [
            {"command": "test", "description": "Test command"},
        ]
        is_valid, error = validate_json_schema(data, COMMAND_SCHEMA)
        assert is_valid is True
        assert error == ""

    def test_invalid_type(self) -> None:
        """Test validation fails for wrong type."""
        data = {"not": "an array"}
        is_valid, error = validate_json_schema(data, COMMAND_SCHEMA)
        assert is_valid is False
        assert "array" in error.lower()

    def test_missing_required_field(self) -> None:
        """Test validation fails for missing required field."""
        data = [{"command": "test"}]  # Missing description
        is_valid, error = validate_json_schema(data, COMMAND_SCHEMA)
        assert is_valid is False
        assert "description" in error.lower()

    def test_empty_command(self) -> None:
        """Test validation fails for empty command."""
        data = [{"command": "", "description": "Test"}]
        is_valid, error = validate_json_schema(data, COMMAND_SCHEMA)
        assert is_valid is False


class TestGetProvider:
    """Tests for get_provider function."""

    def test_get_anthropic_provider(self, mock_env_vars: None) -> None:
        """Test getting Anthropic provider."""
        provider = get_provider("anthropic")
        assert isinstance(provider, AnthropicProvider)

    def test_get_openai_provider(self, mock_env_vars: None) -> None:
        """Test getting OpenAI provider."""
        provider = get_provider("openai")
        assert isinstance(provider, OpenAIProvider)

    def test_get_ollama_provider(self) -> None:
        """Test getting Ollama provider (no API key needed)."""
        provider = get_provider("ollama")
        assert isinstance(provider, OllamaProvider)

    def test_get_unknown_provider(self) -> None:
        """Test getting unknown provider returns None."""
        provider = get_provider("unknown")
        assert provider is None

    def test_get_anthropic_without_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test Anthropic provider fails without API key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        provider = get_provider("anthropic")
        assert provider is None


class TestAnthropicProvider:
    """Tests for AnthropicProvider."""

    def test_init(self) -> None:
        """Test provider initialization."""
        provider = AnthropicProvider("test-key")
        assert provider.api_key == "test-key"
        assert provider.model is not None

    @patch("httpx.post")
    def test_generate_success(self, mock_post: MagicMock) -> None:
        """Test successful generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": '[{"command": "test", "description": "test"}]'}]
        }
        mock_post.return_value = mock_response

        provider = AnthropicProvider("test-key")
        result = provider.generate("test prompt")

        assert result is not None
        assert "command" in result


class TestOpenAIProvider:
    """Tests for OpenAIProvider."""

    def test_init(self) -> None:
        """Test provider initialization."""
        provider = OpenAIProvider("test-key")
        assert provider.api_key == "test-key"
        assert provider.model is not None

    @patch("httpx.post")
    def test_generate_success(self, mock_post: MagicMock) -> None:
        """Test successful generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '[{"command": "test", "description": "test"}]'}}]
        }
        mock_post.return_value = mock_response

        provider = OpenAIProvider("test-key")
        result = provider.generate("test prompt")

        assert result is not None
        assert "command" in result


class TestOllamaProvider:
    """Tests for OllamaProvider."""

    def test_init_defaults(self) -> None:
        """Test provider initialization with defaults."""
        provider = OllamaProvider()
        assert provider.model is not None
        assert "localhost" in provider.host

    def test_init_custom(self) -> None:
        """Test provider initialization with custom values."""
        provider = OllamaProvider(model="custom-model", host="http://custom:1234")
        assert provider.model == "custom-model"
        assert provider.host == "http://custom:1234"
