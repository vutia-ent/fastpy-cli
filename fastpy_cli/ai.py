"""AI service for generating Fastpy resources."""

import json
import os
from abc import ABC, abstractmethod
from typing import Optional

from rich.console import Console

console = Console()

SYSTEM_PROMPT = """You are a Fastpy CLI assistant that generates FastAPI resources.

When given a description, output ONLY a JSON array of commands to run. Each command should be a dict with:
- "command": the full CLI command to run
- "description": brief description of what it creates

Available field types: string, text, integer, float, boolean, datetime, email, url, json, uuid, decimal, money, percent, date, time, phone, slug, ip, color, file, image

Available field rules: required, nullable, unique, index, max:N, min:N, foreign:table.column

Example output for "Create a blog with posts and categories":
[
  {"command": "python cli.py make:resource Category -f name:string:required,unique -f slug:string:unique -f description:text:nullable -m", "description": "Category model with name, slug, description"},
  {"command": "python cli.py make:resource Post -f title:string:required,max:200 -f slug:string:unique -f body:text:required -f published_at:datetime:nullable -f category_id:integer:foreign:categories.id -m -p", "description": "Post model with title, body, and category relation"}
]

Rules:
1. Output ONLY valid JSON, no markdown, no explanation
2. Use snake_case for field names
3. Add foreign keys for relationships (e.g., category_id:integer:foreign:categories.id)
4. Use -m flag to generate migrations
5. Use -p flag for protected routes when appropriate
6. Order resources so dependencies come first (e.g., Category before Post)
"""


class AIProvider(ABC):
    """Base class for AI providers."""

    @abstractmethod
    def generate(self, prompt: str) -> Optional[str]:
        """Generate a response from the AI."""
        pass


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str) -> Optional[str]:
        try:
            import httpx
        except ImportError:
            console.print("[red]Error:[/red] httpx not installed. Run: pip install httpx")
            return None

        try:
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1024,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        except Exception as e:
            console.print(f"[red]Anthropic API error:[/red] {e}")
            return None


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str) -> Optional[str]:
        try:
            import httpx
        except ImportError:
            console.print("[red]Error:[/red] httpx not installed. Run: pip install httpx")
            return None

        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 1024,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            console.print(f"[red]OpenAI API error:[/red] {e}")
            return None


class OllamaProvider(AIProvider):
    """Ollama local LLM provider."""

    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    def generate(self, prompt: str) -> Optional[str]:
        try:
            import httpx
        except ImportError:
            console.print("[red]Error:[/red] httpx not installed. Run: pip install httpx")
            return None

        try:
            response = httpx.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{SYSTEM_PROMPT}\n\nUser request: {prompt}",
                    "stream": False,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["response"]
        except httpx.ConnectError:
            console.print("[red]Error:[/red] Cannot connect to Ollama. Is it running?")
            console.print("[dim]Start Ollama with: ollama serve[/dim]")
            return None
        except Exception as e:
            console.print(f"[red]Ollama error:[/red] {e}")
            return None


def get_provider(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Optional[AIProvider]:
    """Get the appropriate AI provider based on configuration."""

    # Check environment variables if not provided
    if provider is None:
        provider = os.environ.get("FASTPY_AI_PROVIDER", "anthropic")

    provider = provider.lower()

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
        model = os.environ.get("OLLAMA_MODEL", "llama3.2")
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        return OllamaProvider(model=model, host=host)

    else:
        console.print(f"[red]Error:[/red] Unknown provider: {provider}")
        console.print("[dim]Available: anthropic, openai, ollama[/dim]")
        return None


def parse_ai_response(response: str) -> list[dict]:
    """Parse the AI response into a list of commands."""
    try:
        # Try to extract JSON from the response
        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1])

        commands = json.loads(response)
        if isinstance(commands, list):
            return commands
        return []
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing AI response:[/red] {e}")
        console.print(f"[dim]Response was: {response[:200]}...[/dim]")
        return []
