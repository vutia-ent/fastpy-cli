"""AI service for generating Fastpy resources."""

import json
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx
from rich.console import Console

from fastpy_cli.config import get_config
from fastpy_cli.logger import log_debug, log_error, log_info

console = Console()


def get_api_error_message(status_code: int, provider: str) -> tuple[str, str]:
    """Get user-friendly error message for API status codes.

    Args:
        status_code: HTTP status code
        provider: Provider name (Anthropic, OpenAI)

    Returns:
        Tuple of (title, message)
    """
    billing_url = (
        "https://console.anthropic.com/settings/billing"
        if provider == "Anthropic"
        else "https://platform.openai.com/usage"
    )
    key_url = (
        "https://console.anthropic.com"
        if provider == "Anthropic"
        else "https://platform.openai.com/api-keys"
    )

    error_messages = {
        401: (
            "Invalid API key",
            f"Your {provider} API key is invalid or revoked. Get a new key at: {key_url}",
        ),
        403: (
            "Access forbidden",
            "Your API key doesn't have permission for this operation.",
        ),
        429: (
            "Rate limit exceeded",
            f"You've hit the API rate limit (quota/credits exhausted or too many requests). "
            f"Check your usage at: {billing_url}",
        ),
        500: ("Server error", f"{provider} is experiencing issues. Try again later."),
        502: ("Bad gateway", f"{provider} service is temporarily unavailable."),
        503: ("Service unavailable", f"{provider} is under maintenance or overloaded."),
    }

    return error_messages.get(
        status_code, ("API error", f"Unexpected error from {provider} (HTTP {status_code})")
    )


SYSTEM_PROMPT = """You are a Fastpy CLI assistant that generates FastAPI resources.

When given a description, output ONLY a JSON array of commands to run. Each command should be a dict with:
- "command": the full CLI command to run (use "fastpy" as the command prefix)
- "description": brief description of what it creates

Available field types: string, text, integer, float, boolean, datetime, email, url, json, uuid, decimal, money, percent, date, time, phone, slug, ip, color, file, image

Available field rules: required, nullable, unique, index, max:N, min:N, foreign:table.column

Example output for "Create a blog with posts and categories":
[
  {"command": "fastpy make:resource Category -f name:string:required,unique -f slug:string:unique -f description:text:nullable -m", "description": "Category model with name, slug, description"},
  {"command": "fastpy make:resource Post -f title:string:required,max:200 -f slug:string:unique -f body:text:required -f published_at:datetime:nullable -f category_id:integer:foreign:categories.id -m -p", "description": "Post model with title, body, and category relation"}
]

Rules:
1. Output ONLY valid JSON, no markdown, no explanation
2. Use snake_case for field names
3. Add foreign keys for relationships (e.g., category_id:integer:foreign:categories.id)
4. Use -m flag to generate migrations
5. Use -p flag for protected routes when appropriate
6. Order resources so dependencies come first (e.g., Category before Post)
7. Always use "fastpy" as the command prefix (not "python cli.py")
"""

# JSON Schema for validating AI responses
COMMAND_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["command", "description"],
        "properties": {
            "command": {"type": "string", "minLength": 1},
            "description": {"type": "string"},
        },
        "additionalProperties": False,
    },
}


def validate_json_schema(data: Any, schema: dict) -> tuple[bool, str]:
    """Validate data against a JSON schema (simplified validation).

    Args:
        data: Data to validate
        schema: JSON schema dict

    Returns:
        Tuple of (is_valid, error_message)
    """
    schema_type = schema.get("type")

    if schema_type == "array":
        if not isinstance(data, list):
            return False, f"Expected array, got {type(data).__name__}"

        items_schema = schema.get("items", {})
        for i, item in enumerate(data):
            is_valid, error = validate_json_schema(item, items_schema)
            if not is_valid:
                return False, f"Item {i}: {error}"

    elif schema_type == "object":
        if not isinstance(data, dict):
            return False, f"Expected object, got {type(data).__name__}"

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                return False, f"Missing required field: {field}"

        # Validate properties
        properties = schema.get("properties", {})
        for field, value in data.items():
            if field in properties:
                is_valid, error = validate_json_schema(value, properties[field])
                if not is_valid:
                    return False, f"Field '{field}': {error}"

            # Check additionalProperties
            elif schema.get("additionalProperties") is False:
                return False, f"Unexpected field: {field}"

    elif schema_type == "string":
        if not isinstance(data, str):
            return False, f"Expected string, got {type(data).__name__}"
        min_length = schema.get("minLength", 0)
        if len(data) < min_length:
            return False, f"String too short (min {min_length})"

    return True, ""


class AIProvider(ABC):
    """Base class for AI providers."""

    @abstractmethod
    def generate(self, prompt: str) -> Optional[str]:
        """Generate a response from the AI."""
        pass

    def _make_request_with_retry(
        self,
        request_func: callable,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> Optional[httpx.Response]:
        """Make an HTTP request with retry logic.

        Args:
            request_func: Function that makes the HTTP request
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries

        Returns:
            Response object or None on failure
        """
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                log_debug(f"API request attempt {attempt + 1}/{max_retries}")
                start_time = time.time()

                response = request_func()
                response.raise_for_status()

                elapsed = time.time() - start_time
                log_debug(f"API request succeeded in {elapsed:.2f}s")

                return response

            except httpx.TimeoutException:
                log_error(f"Request timed out (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    console.print(
                        f"[yellow]Request timed out, retrying in {delay:.0f}s...[/yellow]"
                    )
                    time.sleep(delay)
                    delay *= 2

            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                # Don't retry on client errors (4xx) except rate limits
                if status == 429:  # Rate limit
                    retry_after = int(
                        e.response.headers.get("retry-after", str(int(delay)))
                    )
                    log_info(f"Rate limited, waiting {retry_after}s")
                    if attempt < max_retries - 1:
                        console.print(
                            f"[yellow]Rate limited, waiting {retry_after}s...[/yellow]"
                        )
                        time.sleep(retry_after)
                    else:
                        # Final attempt failed with rate limit
                        title, message = get_api_error_message(status, "API")
                        console.print(f"[red]Error:[/red] {title}")
                        console.print(f"[dim]{message}[/dim]")
                        return None
                elif 400 <= status < 500:
                    # Client errors - show user-friendly message
                    title, message = get_api_error_message(status, "API")
                    console.print(f"[red]Error:[/red] {title}")
                    console.print(f"[dim]{message}[/dim]")
                    log_error(f"Client error {status}: {e}")
                    return None
                else:  # Server errors (5xx)
                    log_error(f"Server error {status} (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        console.print(
                            f"[yellow]Server error, retrying in {delay:.0f}s...[/yellow]"
                        )
                        time.sleep(delay)
                        delay *= 2
                    else:
                        title, message = get_api_error_message(status, "API")
                        console.print(f"[red]Error:[/red] {title}")
                        console.print(f"[dim]{message}[/dim]")

            except httpx.ConnectError as e:
                log_error(f"Connection error: {e}")
                if attempt < max_retries - 1:
                    console.print(
                        f"[yellow]Connection failed, retrying in {delay:.0f}s...[/yellow]"
                    )
                    time.sleep(delay)
                    delay *= 2

            except Exception as e:
                log_error(f"Unexpected error: {e}")
                return None

        return None


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        config = get_config()
        self.model = model or config.get("ai", "anthropic_model", "claude-sonnet-4-20250514")
        self.timeout = config.ai_timeout
        self.max_retries = config.ai_max_retries

    def generate(self, prompt: str) -> Optional[str]:
        log_debug(f"Using Anthropic model: {self.model}")

        def make_request():
            return httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 2048,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=float(self.timeout),
            )

        response = self._make_request_with_retry(make_request, self.max_retries)
        if response is None:
            console.print("[red]Error:[/red] Failed to get response from Anthropic API")
            return None

        try:
            data = response.json()
            return data["content"][0]["text"]
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            log_error(f"Failed to parse Anthropic response: {e}")
            console.print("[red]Error:[/red] Invalid response from Anthropic API")
            return None


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        config = get_config()
        self.model = model or config.get("ai", "openai_model", "gpt-4o")
        self.timeout = config.ai_timeout
        self.max_retries = config.ai_max_retries

    def generate(self, prompt: str) -> Optional[str]:
        log_debug(f"Using OpenAI model: {self.model}")

        def make_request():
            return httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 2048,
                },
                timeout=float(self.timeout),
            )

        response = self._make_request_with_retry(make_request, self.max_retries)
        if response is None:
            console.print("[red]Error:[/red] Failed to get response from OpenAI API")
            return None

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            log_error(f"Failed to parse OpenAI response: {e}")
            console.print("[red]Error:[/red] Invalid response from OpenAI API")
            return None


class OllamaProvider(AIProvider):
    """Ollama local LLM provider."""

    def __init__(self, model: Optional[str] = None, host: Optional[str] = None):
        config = get_config()
        self.model = model or config.get("ai", "ollama_model", "llama3.2")
        self.host = host or config.get("ai", "ollama_host", "http://localhost:11434")
        self.timeout = config.ai_timeout * 2  # Longer timeout for local models
        self.max_retries = config.ai_max_retries

    def generate(self, prompt: str) -> Optional[str]:
        log_debug(f"Using Ollama model: {self.model} at {self.host}")

        def make_request():
            return httpx.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{SYSTEM_PROMPT}\n\nUser request: {prompt}",
                    "stream": False,
                },
                timeout=float(self.timeout),
            )

        try:
            response = self._make_request_with_retry(make_request, self.max_retries)
            if response is None:
                return None

            data = response.json()
            return data["response"]

        except httpx.ConnectError:
            console.print("[red]Error:[/red] Cannot connect to Ollama. Is it running?")
            console.print("[dim]Start Ollama with: ollama serve[/dim]")
            return None
        except Exception as e:
            log_error(f"Ollama error: {e}")
            console.print(f"[red]Ollama error:[/red] {e}")
            return None


def get_provider(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Optional[AIProvider]:
    """Get the appropriate AI provider based on configuration.

    Args:
        provider: Provider name (anthropic, openai, ollama)
        api_key: Optional API key override

    Returns:
        AIProvider instance or None on error
    """
    config = get_config()

    # Check environment variables if not provided
    if provider is None:
        provider = os.environ.get("FASTPY_AI_PROVIDER") or config.ai_provider

    provider = provider.lower()
    log_debug(f"Using AI provider: {provider}")

    if provider == "anthropic":
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            console.print("[red]Error:[/red] ANTHROPIC_API_KEY not set")
            console.print("[dim]Set it with: export ANTHROPIC_API_KEY=your-key[/dim]")
            return None
        return AnthropicProvider(key)

    elif provider == "openai":
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            console.print("[red]Error:[/red] OPENAI_API_KEY not set")
            console.print("[dim]Set it with: export OPENAI_API_KEY=your-key[/dim]")
            return None
        return OpenAIProvider(key)

    elif provider == "ollama":
        model = os.environ.get("OLLAMA_MODEL") or config.get("ai", "ollama_model")
        host = os.environ.get("OLLAMA_HOST") or config.get("ai", "ollama_host")
        return OllamaProvider(model=model, host=host)

    else:
        console.print(f"[red]Error:[/red] Unknown provider: {provider}")
        console.print("[dim]Available: anthropic, openai, ollama[/dim]")
        return None


def parse_ai_response(response: str) -> list[dict]:
    """Parse the AI response into a list of commands.

    Args:
        response: Raw response string from AI

    Returns:
        List of command dictionaries
    """
    try:
        # Try to extract JSON from the response
        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            # Find the end of the code block
            end_idx = len(lines) - 1
            for i in range(len(lines) - 1, 0, -1):
                if lines[i].startswith("```"):
                    end_idx = i
                    break
            response = "\n".join(lines[1:end_idx])

        log_debug(f"Parsing AI response: {response[:200]}...")

        commands = json.loads(response)

        # Validate against schema
        is_valid, error = validate_json_schema(commands, COMMAND_SCHEMA)
        if not is_valid:
            console.print(f"[red]Error:[/red] Invalid command format: {error}")
            log_error(f"Schema validation failed: {error}")
            return []

        # Additional validation and normalization for command content
        validated_commands = []
        for cmd in commands:
            command = cmd.get("command", "").strip()

            # Normalize old-style commands to use fastpy
            if command.startswith("python cli.py "):
                command = command.replace("python cli.py ", "fastpy ", 1)
                cmd["command"] = command
                log_debug(f"Normalized command: {command}")
            elif command.startswith("python3 cli.py "):
                command = command.replace("python3 cli.py ", "fastpy ", 1)
                cmd["command"] = command
                log_debug(f"Normalized command: {command}")

            # Ensure command starts with expected prefix
            if not command.startswith("fastpy "):
                log_debug(f"Skipping invalid command: {command}")
                continue

            validated_commands.append(cmd)

        if len(validated_commands) < len(commands):
            skipped = len(commands) - len(validated_commands)
            console.print(
                f"[yellow]Warning:[/yellow] {skipped} invalid command(s) were filtered out"
            )

        return validated_commands

    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing AI response:[/red] {e}")
        console.print(f"[dim]Response was: {response[:200]}...[/dim]")
        log_error(f"JSON decode error: {e}")
        return []
