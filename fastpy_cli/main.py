#!/usr/bin/env python3
"""Fastpy CLI - Create production-ready FastAPI projects."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from fastpy_cli import __version__
from fastpy_cli.config import CONFIG_FILE, get_config, init_config_file
from fastpy_cli.logger import log_debug, log_error, log_info, setup_logger
from fastpy_cli.utils import safe_execute_command, validate_command

app = typer.Typer(
    name="fastpy",
    help="Create production-ready FastAPI projects with one command.",
    add_completion=True,  # Enable shell completions
    no_args_is_help=True,
)
console = Console()

REPO_URL = "https://github.com/vutia-ent/fastpy.git"
DOCS_URL = "https://fastpy.ve.ke"

# Commands that are handled by fastpy CLI itself (not proxied to project cli.py)
FASTPY_COMMANDS = {
    "new",
    "version",
    "docs",
    "upgrade",
    "ai",
    "ai:config",
    "config",
    "doctor",
    "init",
    "install",
    "libs",
    "setup",
    "setup:env",
    "setup:db",
    "setup:secret",
    "setup:hooks",
    "--help",
    "-h",
    "--version",
    "-v",
    "--verbose",
    "--debug",
}

# Available libs for scaffolding
AVAILABLE_LIBS = {
    "http": {
        "name": "Http",
        "description": "HTTP client facade (GET, POST, PUT, DELETE, etc.)",
        "dependencies": ["httpx"],
    },
    "mail": {
        "name": "Mail",
        "description": "Email sending with multiple drivers (SMTP, SendGrid, Mailgun, SES)",
        "dependencies": [],
    },
    "cache": {
        "name": "Cache",
        "description": "Caching with multiple drivers (Memory, File, Redis)",
        "dependencies": [],
    },
    "storage": {
        "name": "Storage",
        "description": "File storage with multiple drivers (Local, S3, Memory)",
        "dependencies": [],
    },
    "queue": {
        "name": "Queue",
        "description": "Job queueing system with multiple drivers (Sync, Memory, Redis)",
        "dependencies": [],
    },
    "events": {
        "name": "Event",
        "description": "Event dispatcher with listeners and subscribers",
        "dependencies": [],
    },
    "notifications": {
        "name": "Notify",
        "description": "Multi-channel notifications (Mail, Database, Slack, SMS)",
        "dependencies": [],
    },
    "hash": {
        "name": "Hash",
        "description": "Password hashing (bcrypt, argon2, sha256)",
        "dependencies": ["bcrypt"],
    },
    "crypt": {
        "name": "Crypt",
        "description": "Data encryption (Fernet, AES-256-CBC)",
        "dependencies": ["cryptography"],
    },
}


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"Fastpy CLI v{__version__}")
        raise typer.Exit()


def verbose_callback(ctx: typer.Context, value: bool) -> None:
    """Enable verbose output."""
    if value:
        config = get_config()
        setup_logger(verbose=True, log_file=config.log_file)


def debug_callback(ctx: typer.Context, value: bool) -> None:
    """Enable debug output."""
    if value:
        config = get_config()
        setup_logger(debug=True, log_file=config.log_file)


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        callback=verbose_callback,
        is_eager=True,
        help="Enable verbose output.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        callback=debug_callback,
        is_eager=True,
        help="Enable debug output with detailed logging.",
    ),
) -> None:
    """Fastpy CLI - Create production-ready FastAPI projects."""
    pass


def is_fastpy_project() -> bool:
    """Check if we're inside a Fastpy project."""
    cli_py = Path.cwd() / "cli.py"
    return cli_py.exists()


def proxy_to_project_cli(args: list[str]) -> int:
    """Proxy command to project's cli.py."""
    cli_py = Path.cwd() / "cli.py"

    # Check for virtual environment (cross-platform)
    if sys.platform == "win32":
        venv_python = Path.cwd() / "venv" / "Scripts" / "python.exe"
    else:
        venv_python = Path.cwd() / "venv" / "bin" / "python"

    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    cmd = [python_cmd, str(cli_py)] + args
    log_debug(f"Proxying to project CLI: {cmd}")
    result = subprocess.run(cmd)
    return result.returncode


def run_command(
    cmd: list, cwd: Optional[Path] = None, capture: bool = False
) -> subprocess.CompletedProcess:
    """Run a shell command."""
    log_debug(f"Running command: {cmd}")
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
    )


def check_git_installed() -> bool:
    """Check if git is installed."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def clone_repository(project_name: str, branch: str = "main") -> bool:
    """Clone the Fastpy repository."""
    result = run_command(
        ["git", "clone", "--depth", "1", "-b", branch, REPO_URL, project_name],
        capture=True,
    )
    return result.returncode == 0


def remove_git_history(project_path: Path) -> None:
    """Remove .git directory to start fresh."""
    git_dir = project_path / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)


def init_git_repo(project_path: Path) -> None:
    """Initialize a fresh git repository."""
    run_command(["git", "init"], cwd=project_path, capture=True)
    run_command(["git", "add", "."], cwd=project_path, capture=True)
    run_command(
        ["git", "commit", "-m", "Initial commit from Fastpy"],
        cwd=project_path,
        capture=True,
    )


@app.command()
def new(
    project_name: str = typer.Argument(..., help="Name of the project to create"),
    no_git: bool = typer.Option(False, "--no-git", help="Don't initialize a git repository"),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch to clone from"),
    install: bool = typer.Option(
        False,
        "--install",
        "-i",
        help="Automatically set up venv, install dependencies, and run setup",
    ),
) -> None:
    """Create a new Fastpy project.

    Example:
        fastpy new my-api
        fastpy new my-api --branch dev
        fastpy new my-api --install  # Create + full setup in one command
    """
    log_info(f"Creating new project: {project_name}")

    project_path = Path.cwd() / project_name

    # Check if directory already exists
    if project_path.exists():
        console.print(f"[red]Error:[/red] Directory '{project_name}' already exists.")
        raise typer.Exit(1)

    # Check git is installed
    if not check_git_installed():
        console.print("[red]Error:[/red] Git is not installed. Please install git first.")
        raise typer.Exit(1)

    console.print()
    console.print(
        Panel.fit(
            f"[bold blue]Creating new Fastpy project:[/bold blue] [green]{project_name}[/green]",
            border_style="blue",
        )
    )
    console.print()

    # Clone repository
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Cloning Fastpy template...", total=None)

        if not clone_repository(project_name, branch):
            log_error("Failed to clone repository")
            console.print("[red]Error:[/red] Failed to clone repository.")
            raise typer.Exit(1)

        progress.update(task, description="Removing git history...")
        remove_git_history(project_path)

        if not no_git:
            progress.update(task, description="Initializing fresh git repository...")
            init_git_repo(project_path)

        progress.update(task, description="Done!", completed=True)

    console.print()
    console.print("[green]✓[/green] Project created successfully!")
    console.print()

    # If --install flag is provided, run the install process
    if install:
        console.print("[bold]Running automatic installation...[/bold]")
        console.print()

        # Change to project directory and run install
        import os

        original_dir = os.getcwd()
        os.chdir(project_path)

        try:
            # Create virtual environment
            venv_path = project_path / "venv"
            console.print("[blue]Creating virtual environment...[/blue]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Creating venv...", total=None)
                result = run_command([sys.executable, "-m", "venv", "venv"], cwd=project_path)
                if result.returncode != 0:
                    console.print("[red]Error:[/red] Failed to create virtual environment")
                    raise typer.Exit(1)
                progress.update(task, description="Done!")
            console.print("[green]✓[/green] Virtual environment created")

            # Determine venv python path
            if sys.platform == "win32":
                venv_python = project_path / "venv" / "Scripts" / "python.exe"
            else:
                venv_python = project_path / "venv" / "bin" / "python"

            python_cmd = str(venv_python)

            # Upgrade pip
            console.print("[blue]Upgrading pip...[/blue]")
            subprocess.run(
                [python_cmd, "-m", "pip", "install", "--upgrade", "pip"],
                cwd=project_path,
                capture_output=True,
            )
            console.print("[green]✓[/green] pip upgraded")

            # Install requirements
            requirements_path = project_path / "requirements.txt"
            if requirements_path.exists():
                console.print("[blue]Installing dependencies...[/blue]")
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Installing packages...", total=None)
                    result = subprocess.run(
                        [python_cmd, "-m", "pip", "install", "-r", "requirements.txt"],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                    )
                    progress.update(task, description="Done!")

                if result.returncode == 0:
                    console.print("[green]✓[/green] Dependencies installed")
                else:
                    console.print("[red]Error:[/red] Failed to install dependencies")
                    console.print(f"[dim]{result.stderr}[/dim]")

            console.print()
            console.print("[green]✓[/green] Installation complete!")
            console.print()
            console.print("[bold]Next steps:[/bold]")
            console.print(f"  1. [cyan]cd {project_name}[/cyan]")
            if sys.platform == "win32":
                console.print("  2. [cyan]venv\\Scripts\\activate[/cyan]")
            else:
                console.print("  2. [cyan]source venv/bin/activate[/cyan]")
            console.print("  3. [cyan]fastpy setup[/cyan]  (configure database & secrets)")
            console.print("  4. [cyan]fastpy serve[/cyan]")

        finally:
            os.chdir(original_dir)
    else:
        # Show manual next steps
        console.print("[bold]Next steps:[/bold]")
        console.print(f"  1. [cyan]cd {project_name}[/cyan]")
        console.print("  2. [cyan]fastpy install[/cyan]  (one command setup)")
        console.print()
        console.print("[dim]Or manually:[/dim]")
        console.print("  2. [cyan]python3 -m venv venv[/cyan]")
        console.print(
            "  3. [cyan]source venv/bin/activate[/cyan]  (or [cyan]venv\\Scripts\\activate[/cyan] on Windows)"
        )
        console.print("  4. [cyan]pip install --upgrade pip[/cyan]")
        console.print("  5. [cyan]pip install -r requirements.txt[/cyan]")
        console.print("  6. [cyan]fastpy setup[/cyan]")
        console.print("  7. [cyan]fastpy serve[/cyan]")

    console.print()
    console.print(f"[dim]Documentation: {DOCS_URL}[/dim]")
    console.print()


@app.command()
def version() -> None:
    """Show the Fastpy CLI version."""
    console.print(f"Fastpy CLI v{__version__}")


@app.command()
def docs() -> None:
    """Open Fastpy documentation in browser."""
    import webbrowser

    webbrowser.open(DOCS_URL)
    console.print(f"[green]✓[/green] Opening documentation: {DOCS_URL}")


@app.command()
def upgrade() -> None:
    """Upgrade Fastpy CLI to the latest version."""
    console.print("Upgrading Fastpy CLI...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "fastpy-cli"],
        capture_output=False,
    )
    if result.returncode == 0:
        console.print("[green]✓[/green] Fastpy CLI upgraded successfully!")
    else:
        console.print("[red]Error:[/red] Failed to upgrade. Try: pip install --upgrade fastpy-cli")


@app.command()
def ai(
    prompt: str = typer.Argument(..., help="Description of resources to generate"),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="AI provider: anthropic, openai, ollama"
    ),
    execute: bool = typer.Option(False, "--execute", "-e", help="Execute commands automatically"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Show commands without executing"),
) -> None:
    """Generate resources using AI.

    Examples:
        fastpy ai "Create a blog with posts, categories, and tags"
        fastpy ai "E-commerce with products, orders, and customers" --execute
        fastpy ai "User management system" --provider ollama
    """
    from fastpy_cli.ai import get_provider, parse_ai_response

    log_info(f"AI generation with prompt: {prompt}")

    console.print()
    console.print(
        Panel.fit(
            "[bold blue]AI Resource Generator[/bold blue]",
            border_style="blue",
        )
    )
    console.print()
    console.print(f"[dim]Prompt:[/dim] {prompt}")
    console.print()

    # Get AI provider
    ai_provider = get_provider(provider)
    if not ai_provider:
        raise typer.Exit(1)

    # Generate response
    with console.status("[bold green]Thinking...[/bold green]"):
        response = ai_provider.generate(prompt)

    if not response:
        console.print("[red]Error:[/red] Failed to get AI response")
        raise typer.Exit(1)

    # Parse commands
    commands = parse_ai_response(response)
    if not commands:
        console.print("[red]Error:[/red] No valid commands generated")
        raise typer.Exit(1)

    # Display commands
    console.print(f"[green]Generated {len(commands)} command(s):[/green]")
    console.print()

    for i, cmd in enumerate(commands, 1):
        console.print(f"  [cyan]{i}.[/cyan] {cmd.get('description', 'No description')}")
        console.print(f"     [dim]{cmd.get('command', '')}[/dim]")
        console.print()

    # Handle execution
    if dry_run:
        console.print("[yellow]Dry run mode - commands not executed[/yellow]")
        return

    if not execute:
        execute = typer.confirm("Execute these commands?", default=False)

    if execute:
        console.print()
        for cmd in commands:
            command = cmd.get("command", "")
            if command:
                console.print(f"[bold]Running:[/bold] {command}")

                # Validate command before execution
                is_valid, error = validate_command(command)
                if not is_valid:
                    console.print(f"[red]Skipping unsafe command:[/red] {error}")
                    continue

                try:
                    # Use safe execution (no shell=True)
                    result = safe_execute_command(command, allow_unsafe=False)
                    if result.returncode != 0:
                        console.print(
                            f"[red]Command failed with exit code {result.returncode}[/red]"
                        )
                        if not typer.confirm("Continue with remaining commands?", default=True):
                            break
                except ValueError as e:
                    console.print(f"[red]Error:[/red] {e}")
                    if not typer.confirm("Continue with remaining commands?", default=True):
                        break

                console.print()

        # Extract model names from executed commands for follow-up prompts
        model_names = []
        for cmd in commands:
            command = cmd.get("command", "")
            # Extract model name from make:model or make:resource commands
            if "make:model" in command or "make:resource" in command:
                parts = command.split()
                for i, part in enumerate(parts):
                    if part in ("make:model", "make:resource") and i + 1 < len(parts):
                        model_name = parts[i + 1]
                        # Skip if it's a flag
                        if not model_name.startswith("-"):
                            model_names.append(model_name)
                        break

        # Prompt to add routes for models without routes
        models_without_routes = []
        for cmd in commands:
            command = cmd.get("command", "")
            # Check if make:model was used (no routes) vs make:resource (has routes)
            if "make:model" in command and "make:route" not in command:
                parts = command.split()
                for i, part in enumerate(parts):
                    if part == "make:model" and i + 1 < len(parts):
                        model_name = parts[i + 1]
                        if not model_name.startswith("-"):
                            models_without_routes.append(model_name)
                        break

        if models_without_routes:
            console.print()
            console.print(
                f"[yellow]Models without routes:[/yellow] {', '.join(models_without_routes)}"
            )
            if typer.confirm("Generate routes for these models?", default=True):
                for model_name in models_without_routes:
                    route_cmd = f"fastpy make:route {model_name} --protected"
                    console.print(f"[bold]Running:[/bold] {route_cmd}")
                    try:
                        result = safe_execute_command(route_cmd, allow_unsafe=False)
                        if result.returncode != 0:
                            console.print(f"[red]Failed to create route for {model_name}[/red]")
                    except ValueError as e:
                        console.print(f"[red]Error:[/red] {e}")
                    console.print()

        # Prompt to run migrations
        console.print()
        if typer.confirm("Run database migrations?", default=True):
            migrate_cmd = "fastpy db:migrate"
            console.print(f"[bold]Running:[/bold] {migrate_cmd}")
            try:
                result = safe_execute_command(migrate_cmd, allow_unsafe=False)
                if result.returncode == 0:
                    console.print("[green]✓[/green] Migrations completed!")
                else:
                    console.print("[red]Migration failed[/red]")
            except ValueError as e:
                console.print(f"[red]Error:[/red] {e}")

        console.print()
        console.print("[green]✓[/green] Done!")
    else:
        console.print("[dim]Commands not executed. Use --execute to run automatically.[/dim]")


@app.command()
def config(
    init: bool = typer.Option(False, "--init", help="Initialize config file"),
    show_path: bool = typer.Option(False, "--path", help="Show config file path"),
) -> None:
    """Show or initialize AI configuration.

    Examples:
        fastpy config           # Show current config
        fastpy config --init    # Create config file
        fastpy config --path    # Show config file path
    """
    if show_path:
        console.print(f"Config file: {CONFIG_FILE}")
        return

    if init:
        path = init_config_file()
        console.print(f"[green]✓[/green] Config file created: {path}")
        console.print("[dim]Edit this file to customize your settings.[/dim]")
        return

    cfg = get_config()

    console.print()
    console.print("[bold]Fastpy Configuration[/bold]")
    console.print()

    # AI settings
    console.print("[bold cyan]AI Settings[/bold cyan]")
    console.print(f"  Provider: [green]{cfg.ai_provider}[/green]")
    console.print(f"  Timeout: {cfg.ai_timeout}s")
    console.print(f"  Max Retries: {cfg.ai_max_retries}")

    provider = cfg.ai_provider
    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        status = "[green]Set[/green]" if key else "[red]Not set[/red]"
        console.print(f"  ANTHROPIC_API_KEY: {status}")
    elif provider == "openai":
        key = os.environ.get("OPENAI_API_KEY", "")
        status = "[green]Set[/green]" if key else "[red]Not set[/red]"
        console.print(f"  OPENAI_API_KEY: {status}")
    elif provider == "ollama":
        console.print(f"  Model: {cfg.get('ai', 'ollama_model', 'llama3.2')}")
        console.print(f"  Host: {cfg.get('ai', 'ollama_host', 'http://localhost:11434')}")

    console.print()
    console.print("[bold cyan]Default Settings[/bold cyan]")
    console.print(f"  Git: {cfg.default_git}")
    console.print(f"  Setup: {cfg.default_setup}")
    console.print(f"  Branch: {cfg.default_branch}")

    console.print()
    console.print(f"[dim]Config file: {CONFIG_FILE}[/dim]")
    if not CONFIG_FILE.exists():
        console.print("[dim]Run 'fastpy config --init' to create config file[/dim]")


def update_env_file(key: str, value: str, env_path: Path = Path(".env")) -> bool:
    """Update or add a key-value pair in the .env file.

    Args:
        key: Environment variable name
        value: Value to set
        env_path: Path to .env file (defaults to current directory)

    Returns:
        True if successful, False otherwise
    """
    try:
        lines = []
        key_found = False

        # Read existing file if it exists
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    # Check if this line contains our key
                    if line.strip().startswith(f"{key}="):
                        lines.append(f"{key}={value}\n")
                        key_found = True
                    else:
                        lines.append(line)

        # Add key if not found
        if not key_found:
            # Add newline if file doesn't end with one
            if lines and not lines[-1].endswith("\n"):
                lines.append("\n")
            lines.append(f"{key}={value}\n")

        # Write back
        with open(env_path, "w") as f:
            f.writelines(lines)

        return True
    except Exception as e:
        console.print(f"[red]Error updating .env:[/red] {e}")
        return False


@app.command("ai:config")
def ai_config_command(
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Set AI provider: anthropic, openai, google, groq, ollama"
    ),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Set API key (saves to .env file)"),
    test: bool = typer.Option(False, "--test", "-t", help="Test the AI connection"),
    env_file: Optional[str] = typer.Option(
        None, "--env", "-e", help="Path to .env file (default: ./.env)"
    ),
) -> None:
    """Configure AI provider and API key for code generation.

    Set up your preferred AI provider for the 'fastpy ai' command.
    API keys are saved to your project's .env file for security.

    Examples:
        fastpy ai:config                              # Interactive setup
        fastpy ai:config -p anthropic                 # Set provider
        fastpy ai:config -p anthropic -k sk-xxx       # Set provider + key
        fastpy ai:config -k sk-xxx                    # Set key for current provider
        fastpy ai:config -p ollama                    # Use local Ollama
        fastpy ai:config --test                       # Test connection

    Supported Providers:
        anthropic  - Claude (requires ANTHROPIC_API_KEY)
        openai     - GPT-4 (requires OPENAI_API_KEY)
        google     - Gemini (requires GOOGLE_API_KEY)
        groq       - Groq Cloud (requires GROQ_API_KEY)
        ollama     - Local LLMs (free, no API key needed)
    """
    import requests

    console.print()
    console.print(Panel.fit("[bold blue]AI Configuration[/bold blue]", border_style="blue"))
    console.print()

    cfg = get_config()
    env_path = Path(env_file) if env_file else Path(".env")

    # Handle API key setting
    if key:
        # Determine which provider the key is for
        target_provider = provider.lower() if provider else cfg.ai_provider

        if target_provider == "ollama":
            console.print("[yellow]Note:[/yellow] Ollama doesn't require an API key")
        else:
            # Determine environment variable name
            env_var = {
                "anthropic": "ANTHROPIC_API_KEY",
                "openai": "OPENAI_API_KEY",
                "google": "GOOGLE_API_KEY",
                "groq": "GROQ_API_KEY",
            }.get(target_provider)

            if not env_var:
                console.print(f"[red]Error:[/red] Unknown provider: {target_provider}")
                console.print("[dim]Available: anthropic, openai, google, groq, ollama[/dim]")
                raise typer.Exit(1)

            # Update .env file
            if update_env_file(env_var, key, env_path):
                console.print(f"[green]✓[/green] {env_var} saved to [cyan]{env_path}[/cyan]")
                # Also set it in current environment for immediate use
                os.environ[env_var] = key
            else:
                raise typer.Exit(1)

    # If provider specified, update config
    if provider:
        provider = provider.lower()
        valid_providers = ["anthropic", "openai", "google", "groq", "ollama"]
        if provider not in valid_providers:
            console.print(f"[red]Error:[/red] Unknown provider: {provider}")
            console.print(f"[dim]Available: {', '.join(valid_providers)}[/dim]")
            raise typer.Exit(1)

        # Update config file
        if not CONFIG_FILE.exists():
            init_config_file()

        import toml

        config_data = toml.load(CONFIG_FILE)
        if "ai" not in config_data:
            config_data["ai"] = {}
        config_data["ai"]["provider"] = provider

        with open(CONFIG_FILE, "w") as f:
            toml.dump(config_data, f)

        console.print(f"[green]✓[/green] AI provider set to: [cyan]{provider}[/cyan]")

        # Provider-specific instructions
        provider_info = {
            "anthropic": {
                "env_var": "ANTHROPIC_API_KEY",
                "key_url": "https://console.anthropic.com",
                "ai_init": "claude",
            },
            "openai": {
                "env_var": "OPENAI_API_KEY",
                "key_url": "https://platform.openai.com/api-keys",
                "ai_init": None,
            },
            "google": {
                "env_var": "GOOGLE_API_KEY",
                "key_url": "https://aistudio.google.com/apikey",
                "ai_init": "gemini",
            },
            "groq": {
                "env_var": "GROQ_API_KEY",
                "key_url": "https://console.groq.com/keys",
                "ai_init": None,
            },
            "ollama": {
                "env_var": None,
                "key_url": None,
                "ai_init": None,
            },
        }

        info = provider_info.get(provider, {})

        # Show next steps only if key wasn't just set
        if not key:
            if info.get("env_var"):
                existing_key = os.environ.get(info["env_var"])
                if not existing_key:
                    console.print()
                    console.print("[yellow]Set your API key:[/yellow]")
                    console.print("  fastpy ai:config -k YOUR_API_KEY")
                    console.print("  [dim]or[/dim]")
                    console.print(f"  export {info['env_var']}=your-key-here")
                    console.print()
                    console.print(f"[dim]Get your key at: {info['key_url']}[/dim]")
            elif provider == "ollama":
                console.print()
                console.print("[dim]Ollama runs locally - no API key needed[/dim]")
                console.print("[dim]Start with: ollama serve[/dim]")
                console.print("[dim]Download at: https://ollama.ai[/dim]")

        # Suggest running ai:init if applicable and in a fastpy project
        if info.get("ai_init"):
            project_cli = Path("cli.py")
            if project_cli.exists():
                console.print()
                console.print("[yellow]Initialize AI assistant config:[/yellow]")
                console.print(f"  fastpy ai:init {info['ai_init']}")

    # Exit if we set provider or key
    if provider or key:
        raise typer.Exit(0)

    # Test connection
    if test:
        current_provider = cfg.ai_provider
        console.print(f"Testing [cyan]{current_provider}[/cyan] connection...")
        console.print()

        def handle_api_error(
            status_code: int, response: "requests.Response", provider: str
        ) -> None:
            """Display user-friendly error messages for API errors."""
            error_messages = {
                401: (
                    "Invalid API key",
                    f"Your {provider} API key is invalid or has been revoked.\n"
                    f"  Get a new key at: {'https://console.anthropic.com' if provider == 'Anthropic' else 'https://platform.openai.com/api-keys'}",
                ),
                403: (
                    "Access forbidden",
                    "Your API key doesn't have permission for this operation.\n"
                    "  Check your account permissions and API key scopes.",
                ),
                429: (
                    "Rate limit exceeded",
                    "You've hit the API rate limit. This usually means:\n"
                    "  • You've exceeded your quota or credit limit\n"
                    "  • Too many requests in a short period\n"
                    f"  Check your usage at: {'https://console.anthropic.com/settings/billing' if provider == 'Anthropic' else 'https://platform.openai.com/usage'}",
                ),
                500: (
                    "Server error",
                    f"{provider} is experiencing issues. Try again in a few minutes.",
                ),
                502: (
                    "Bad gateway",
                    f"{provider} service is temporarily unavailable. Try again shortly.",
                ),
                503: (
                    "Service unavailable",
                    f"{provider} is under maintenance or overloaded. Try again later.",
                ),
            }

            title, message = error_messages.get(
                status_code, ("Unknown error", f"Unexpected error from {provider} API.")
            )

            console.print(f"[red]✗[/red] {title} (HTTP {status_code})")
            console.print()
            for line in message.split("\n"):
                console.print(f"[dim]{line}[/dim]")

            # Try to get more details from response
            try:
                error_body = response.json()
                if "error" in error_body:
                    error_detail = error_body["error"]
                    if isinstance(error_detail, dict):
                        error_msg = error_detail.get("message", "")
                    else:
                        error_msg = str(error_detail)
                    if error_msg:
                        console.print()
                        console.print(f"[dim]API message: {error_msg}[/dim]")
            except Exception:
                pass

        if current_provider == "anthropic":
            key = os.environ.get("ANTHROPIC_API_KEY")
            if not key:
                console.print("[red]✗[/red] ANTHROPIC_API_KEY not set")
                console.print("[dim]Set with: fastpy ai:config -k YOUR_KEY[/dim]")
                raise typer.Exit(1)
            try:
                response = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "Hi"}],
                    },
                    timeout=10,
                )
                if response.status_code == 200:
                    console.print("[green]✓[/green] Anthropic connection successful!")
                else:
                    handle_api_error(response.status_code, response, "Anthropic")
            except requests.exceptions.Timeout:
                console.print("[red]✗[/red] Connection timed out")
                console.print("[dim]The Anthropic API took too long to respond. Try again.[/dim]")
            except requests.exceptions.ConnectionError:
                console.print("[red]✗[/red] Connection failed")
                console.print(
                    "[dim]Could not connect to Anthropic API. Check your internet connection.[/dim]"
                )
            except Exception as e:
                console.print(f"[red]✗[/red] Unexpected error: {e}")

        elif current_provider == "openai":
            key = os.environ.get("OPENAI_API_KEY")
            if not key:
                console.print("[red]✗[/red] OPENAI_API_KEY not set")
                console.print("[dim]Set with: fastpy ai:config -k YOUR_KEY[/dim]")
                raise typer.Exit(1)
            try:
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "Hi"}],
                    },
                    timeout=10,
                )
                if response.status_code == 200:
                    console.print("[green]✓[/green] OpenAI connection successful!")
                else:
                    handle_api_error(response.status_code, response, "OpenAI")
            except requests.exceptions.Timeout:
                console.print("[red]✗[/red] Connection timed out")
                console.print("[dim]The OpenAI API took too long to respond. Try again.[/dim]")
            except requests.exceptions.ConnectionError:
                console.print("[red]✗[/red] Connection failed")
                console.print(
                    "[dim]Could not connect to OpenAI API. Check your internet connection.[/dim]"
                )
            except Exception as e:
                console.print(f"[red]✗[/red] Unexpected error: {e}")

        elif current_provider == "ollama":
            host = cfg.get("ai", "ollama_host", "http://localhost:11434")
            try:
                response = requests.get(f"{host}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    console.print("[green]✓[/green] Ollama is running!")
                    if models:
                        console.print(
                            f"  Available models: {', '.join(m['name'] for m in models[:5])}"
                        )
                else:
                    console.print(f"[red]✗[/red] Ollama error: {response.status_code}")
            except requests.exceptions.ConnectionError:
                console.print("[red]✗[/red] Ollama is not running")
                console.print("[dim]Start with: ollama serve[/dim]")
            except Exception as e:
                console.print(f"[red]✗[/red] Connection failed: {e}")

        raise typer.Exit(0)

    # Interactive setup (default)
    console.print("[bold]Current Configuration[/bold]")
    console.print()

    # Show current provider
    current = cfg.ai_provider
    console.print(f"  Provider: [cyan]{current}[/cyan]")

    # Show API key status
    providers_status = []
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if anthropic_key:
        providers_status.append(("anthropic", "[green]✓[/green] API key set"))
    else:
        providers_status.append(("anthropic", "[yellow]○[/yellow] API key not set"))

    if openai_key:
        providers_status.append(("openai", "[green]✓[/green] API key set"))
    else:
        providers_status.append(("openai", "[yellow]○[/yellow] API key not set"))

    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            providers_status.append(("ollama", "[green]✓[/green] Running locally"))
        else:
            providers_status.append(("ollama", "[yellow]○[/yellow] Not running"))
    except Exception:
        providers_status.append(("ollama", "[yellow]○[/yellow] Not running"))

    console.print()
    console.print("[bold]Available Providers[/bold]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Provider")
    table.add_column("Model")
    table.add_column("Status")

    for name, status in providers_status:
        model = {
            "anthropic": "Claude Sonnet",
            "openai": "GPT-4o",
            "ollama": "Llama 3.2 (local)",
        }[name]
        table.add_row(name, model, status)

    console.print(table)

    console.print()
    console.print("[bold]Quick Setup[/bold]")
    console.print()
    console.print("  # Set provider and API key (saves to .env)")
    console.print("  [cyan]fastpy ai:config -p anthropic -k YOUR_API_KEY[/cyan]")
    console.print()
    console.print("  # Set provider only")
    console.print("  [cyan]fastpy ai:config -p anthropic[/cyan]")
    console.print()
    console.print("  # Set API key for current provider")
    console.print("  [cyan]fastpy ai:config -k YOUR_API_KEY[/cyan]")
    console.print()
    console.print("  # Test connection")
    console.print("  [cyan]fastpy ai:config --test[/cyan]")
    console.print()
    console.print("[dim]Get API keys:[/dim]")
    console.print("[dim]  Anthropic: https://console.anthropic.com[/dim]")
    console.print("[dim]  OpenAI: https://platform.openai.com[/dim]")
    console.print("[dim]  Ollama: https://ollama.ai (free, runs locally)[/dim]")


@app.command()
def doctor() -> None:
    """Diagnose and fix common issues.

    Checks your environment for:
    - Python version
    - Required tools (git, pip)
    - Configuration status
    - AI provider setup
    """
    console.print()
    console.print(
        Panel.fit(
            "[bold blue]Fastpy Doctor[/bold blue]",
            border_style="blue",
        )
    )
    console.print()

    issues = []
    warnings = []

    # Python version check
    py_version = sys.version_info
    py_status = "[green]✓[/green]" if py_version >= (3, 9) else "[red]✗[/red]"
    console.print(f"{py_status} Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version < (3, 9):
        issues.append("Python 3.9 or higher is required")

    # Git check
    git_installed = check_git_installed()
    git_status = "[green]✓[/green]" if git_installed else "[red]✗[/red]"
    console.print(f"{git_status} Git installed")
    if not git_installed:
        issues.append("Git is not installed. Install from https://git-scm.com")

    # Config file check
    config_exists = CONFIG_FILE.exists()
    config_status = "[green]✓[/green]" if config_exists else "[yellow]○[/yellow]"
    console.print(
        f"{config_status} Config file {'exists' if config_exists else 'not found (optional)'}"
    )
    if not config_exists:
        warnings.append("No config file found. Run 'fastpy config --init' to create one")

    # AI Provider checks
    console.print()
    console.print("[bold]AI Providers:[/bold]")

    # Anthropic
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    anthropic_status = "[green]✓[/green]" if anthropic_key else "[yellow]○[/yellow]"
    console.print(f"  {anthropic_status} Anthropic (Claude)")
    if not anthropic_key:
        warnings.append("ANTHROPIC_API_KEY not set")

    # OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY")
    openai_status = "[green]✓[/green]" if openai_key else "[yellow]○[/yellow]"
    console.print(f"  {openai_status} OpenAI (GPT)")
    if not openai_key:
        warnings.append("OPENAI_API_KEY not set")

    # Ollama
    ollama_running = False
    try:
        import httpx

        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        ollama_running = response.status_code == 200
    except Exception:
        pass
    ollama_status = "[green]✓[/green]" if ollama_running else "[yellow]○[/yellow]"
    console.print(f"  {ollama_status} Ollama (Local)")
    if not ollama_running:
        warnings.append("Ollama not running. Start with 'ollama serve'")

    # Project check (if in a project)
    console.print()
    console.print("[bold]Project Status:[/bold]")
    if is_fastpy_project():
        console.print("  [green]✓[/green] Inside a Fastpy project")

        # Check venv
        venv_path = Path.cwd() / "venv"
        venv_status = "[green]✓[/green]" if venv_path.exists() else "[red]✗[/red]"
        console.print(f"  {venv_status} Virtual environment")
        if not venv_path.exists():
            issues.append("Virtual environment not found. Run: python -m venv venv")

        # Check .env
        env_path = Path.cwd() / ".env"
        env_status = "[green]✓[/green]" if env_path.exists() else "[red]✗[/red]"
        console.print(f"  {env_status} .env file")
        if not env_path.exists():
            issues.append(".env file not found. Run: cp .env.example .env")
    else:
        console.print("  [dim]Not inside a Fastpy project[/dim]")

    # Summary
    console.print()
    if issues:
        console.print("[bold red]Issues found:[/bold red]")
        for issue in issues:
            console.print(f"  [red]•[/red] {issue}")
    if warnings:
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for warning in warnings:
            console.print(f"  [yellow]•[/yellow] {warning}")

    if not issues and not warnings:
        console.print("[bold green]All checks passed![/bold green]")
    elif not issues:
        console.print()
        console.print("[green]No critical issues found.[/green]")


@app.command("install")
def install_command(
    skip_setup: bool = typer.Option(False, "--skip-setup", help="Skip running fastpy setup"),
    skip_venv: bool = typer.Option(False, "--skip-venv", help="Skip virtual environment creation"),
    skip_mysql: bool = typer.Option(
        False, "--skip-mysql", help="Skip MySQL packages (use for SQLite/PostgreSQL only)"
    ),
    requirements: str = typer.Option(
        "requirements.txt", "--requirements", "-r", help="Requirements file to install"
    ),
) -> None:
    """Install project dependencies and set up environment.

    Automates the setup process by:
    1. Creating a virtual environment (if it doesn't exist)
    2. Installing dependencies from requirements.txt
    3. Running fastpy setup (interactive project configuration)

    This command should be run inside a Fastpy project directory.

    Examples:
        fastpy install                     # Full install with setup
        fastpy install --skip-setup        # Install deps only
        fastpy install --skip-mysql        # Skip MySQL packages (for SQLite users)
        fastpy install -r requirements-dev.txt  # Use different requirements file
    """
    from fastpy_cli.setup import is_fastpy_project as check_project

    if not check_project():
        console.print("[red]Error:[/red] Not inside a Fastpy project.")
        console.print("[dim]Run this from a directory containing main.py and app/[/dim]")
        raise typer.Exit(1)

    console.print()
    console.print(
        Panel.fit(
            "[bold blue]Fastpy Project Install[/bold blue]\n"
            "[dim]Setting up your development environment[/dim]",
            border_style="blue",
        )
    )
    console.print()

    project_path = Path.cwd()

    # Step 1: Create virtual environment
    if not skip_venv:
        venv_path = project_path / "venv"
        if venv_path.exists():
            console.print("[green]✓[/green] Virtual environment already exists")
        else:
            console.print("[blue]Creating virtual environment...[/blue]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Creating venv...", total=None)
                result = run_command([sys.executable, "-m", "venv", "venv"], cwd=project_path)
                if result.returncode != 0:
                    console.print("[red]Error:[/red] Failed to create virtual environment")
                    raise typer.Exit(1)
                progress.update(task, description="Done!")
            console.print("[green]✓[/green] Virtual environment created")

    # Determine venv python path
    if sys.platform == "win32":
        venv_python = project_path / "venv" / "Scripts" / "python.exe"
        venv_pip = project_path / "venv" / "Scripts" / "pip.exe"
    else:
        venv_python = project_path / "venv" / "bin" / "python"
        venv_pip = project_path / "venv" / "bin" / "pip"

    # Use venv python if it exists, otherwise use current python
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable
    pip_cmd = str(venv_pip) if venv_pip.exists() else f"{python_cmd} -m pip"

    # Step 2: Upgrade pip
    console.print("[blue]Upgrading pip...[/blue]")
    result = subprocess.run(
        [python_cmd, "-m", "pip", "install", "--upgrade", "pip"],
        cwd=project_path,
        capture_output=True,
    )
    if result.returncode == 0:
        console.print("[green]✓[/green] pip upgraded")
    else:
        console.print("[yellow]⚠[/yellow] Could not upgrade pip (continuing anyway)")

    # Step 3: Install requirements
    requirements_path = project_path / requirements
    if requirements_path.exists():
        # MySQL packages to skip if --skip-mysql is set
        mysql_packages = ["mysqlclient", "pymysql", "aiomysql"]

        if skip_mysql:
            console.print(
                f"[blue]Installing dependencies from {requirements} (skipping MySQL packages)...[/blue]"
            )
            # Read requirements and filter out MySQL packages
            with open(requirements_path, "r") as f:
                req_lines = f.readlines()

            filtered_reqs = []
            for line in req_lines:
                line_lower = line.lower().strip()
                # Skip empty lines, comments, and MySQL packages
                if not line_lower or line_lower.startswith("#"):
                    continue
                # Check if it's a MySQL package
                is_mysql_pkg = any(pkg in line_lower for pkg in mysql_packages)
                if not is_mysql_pkg:
                    filtered_reqs.append(line.strip())

            # Create a temporary requirements file
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, dir=project_path
            ) as tmp_file:
                tmp_file.write("\n".join(filtered_reqs))
                tmp_req_path = tmp_file.name

            install_target = tmp_req_path
        else:
            console.print(f"[blue]Installing dependencies from {requirements}...[/blue]")
            install_target = requirements

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Installing packages...", total=None)
            result = subprocess.run(
                [python_cmd, "-m", "pip", "install", "-r", install_target],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            progress.update(task, description="Done!")

        # Clean up temp file if created
        if skip_mysql and "tmp_req_path" in locals():
            try:
                os.unlink(tmp_req_path)
            except Exception:
                pass

        if result.returncode == 0:
            console.print("[green]✓[/green] Dependencies installed")
        else:
            # Check if it's a MySQL-related error
            stderr_lower = result.stderr.lower()
            is_mysql_error = any(
                x in stderr_lower
                for x in ["mysqlclient", "mysql_config", "mariadb_config", "mysql.h"]
            )

            if is_mysql_error:
                console.print()
                console.print(
                    "[yellow]⚠[/yellow] MySQL client installation failed. "
                    "This is common on systems without MySQL development libraries."
                )
                console.print()

                # Detect platform and offer solutions
                if sys.platform == "darwin":
                    console.print("[bold]Options:[/bold]")
                    console.print("  1. Install MySQL client (if using MySQL):")
                    console.print("     [cyan]brew install mysql-client[/cyan]")
                    console.print(
                        "     [cyan]export PATH=\"/opt/homebrew/opt/mysql-client/bin:$PATH\"[/cyan]"
                    )
                    console.print(
                        "     [cyan]export LDFLAGS=\"-L/opt/homebrew/opt/mysql-client/lib\"[/cyan]"
                    )
                    console.print(
                        "     [cyan]export CPPFLAGS=\"-I/opt/homebrew/opt/mysql-client/include\"[/cyan]"
                    )
                    console.print()
                    console.print("  2. Skip MySQL packages (if using SQLite/PostgreSQL):")
                    console.print("     [cyan]fastpy install --skip-mysql[/cyan]")
                elif sys.platform == "linux":
                    console.print("[bold]Options:[/bold]")
                    console.print("  1. Install MySQL client (Debian/Ubuntu):")
                    console.print(
                        "     [cyan]sudo apt-get install libmysqlclient-dev python3-dev[/cyan]"
                    )
                    console.print("  1. Install MySQL client (RHEL/CentOS):")
                    console.print("     [cyan]sudo yum install mysql-devel python3-devel[/cyan]")
                    console.print()
                    console.print("  2. Skip MySQL packages (if using SQLite/PostgreSQL):")
                    console.print("     [cyan]fastpy install --skip-mysql[/cyan]")
                else:
                    console.print("[bold]Options:[/bold]")
                    console.print("  1. Install MySQL client from https://dev.mysql.com/downloads/")
                    console.print("  2. Skip MySQL packages: [cyan]fastpy install --skip-mysql[/cyan]")

                console.print()
                console.print("[dim]If you only need SQLite for development, use --skip-mysql[/dim]")
                raise typer.Exit(1)
            else:
                console.print("[red]Error:[/red] Failed to install dependencies")
                console.print(f"[dim]{result.stderr}[/dim]")
                raise typer.Exit(1)
    else:
        console.print(f"[yellow]⚠[/yellow] {requirements} not found, skipping dependency installation")

    # Step 4: Run setup (optional)
    if not skip_setup:
        console.print()
        console.print("[bold]Running project setup...[/bold]")
        console.print()
        # Import and run full_setup
        from fastpy_cli.setup import full_setup

        full_setup()
    else:
        console.print()
        console.print("[green]✓[/green] Installation complete!")
        console.print()
        console.print("[bold]Next steps:[/bold]")
        if venv_python.exists():
            if sys.platform == "win32":
                console.print("  1. Activate venv: [cyan]venv\\Scripts\\activate[/cyan]")
            else:
                console.print("  1. Activate venv: [cyan]source venv/bin/activate[/cyan]")
        console.print("  2. Run setup: [cyan]fastpy setup[/cyan]")
        console.print("  3. Start server: [cyan]fastpy serve[/cyan]")


@app.command("init")
def init_command(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config"),
) -> None:
    """Initialize Fastpy configuration.

    Creates a config file at ~/.fastpy/config.toml with default settings.

    Examples:
        fastpy init
        fastpy init --force
    """
    if CONFIG_FILE.exists() and not force:
        console.print(f"[yellow]Config file already exists:[/yellow] {CONFIG_FILE}")
        if typer.confirm("Overwrite existing config?", default=False):
            pass
        else:
            console.print("Aborted.")
            raise typer.Exit(0)

    path = init_config_file()
    console.print(f"[green]✓[/green] Config initialized: {path}")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  1. Edit [cyan]{path}[/cyan] to customize settings")
    console.print("  2. Set your API key:")
    console.print("     [cyan]export ANTHROPIC_API_KEY=your-key[/cyan]")
    console.print("  3. Create a new project:")
    console.print("     [cyan]fastpy new my-api[/cyan]")


@app.command("libs")
def libs_command(
    lib_name: Optional[str] = typer.Argument(
        None,
        help="Name of lib to install (http, mail, cache, storage, queue, events, notifications, hash, crypt)",
    ),
    list_libs: bool = typer.Option(False, "--list", "-l", help="List all available libs"),
    all_libs: bool = typer.Option(False, "--all", "-a", help="Install all libs"),
    show_usage: bool = typer.Option(False, "--usage", "-u", help="Show usage examples for a lib"),
) -> None:
    """Install and manage Fastpy libs (Laravel-style abstractions).

    Fastpy libs provide Laravel-style facades for common tasks like HTTP requests,
    email sending, caching, file storage, job queues, and more.

    Examples:
        fastpy libs --list                # List available libs
        fastpy libs http                  # Show info about Http lib
        fastpy libs http --usage          # Show usage examples
        fastpy libs --all                 # Show all libs info
    """
    console.print()

    # List all libs
    if list_libs or (lib_name is None and not all_libs):
        console.print(
            Panel.fit(
                "[bold blue]Fastpy Libs[/bold blue]\n"
                "[dim]Laravel-style abstractions for FastAPI[/dim]",
                border_style="blue",
            )
        )
        console.print()

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Lib", style="green")
        table.add_column("Facade", style="yellow")
        table.add_column("Description")
        table.add_column("Dependencies", style="dim")

        for key, lib in AVAILABLE_LIBS.items():
            deps = ", ".join(lib["dependencies"]) if lib["dependencies"] else "-"
            table.add_row(key, lib["name"], lib["description"], deps)

        console.print(table)
        console.print()
        console.print("[bold]Usage:[/bold]")
        console.print(
            "  [cyan]from fastpy_cli.libs import Http, Mail, Cache, Storage, Queue, Event, Notify, Hash, Crypt[/cyan]"
        )
        console.print()
        console.print("[dim]Run 'fastpy libs <name> --usage' for detailed examples[/dim]")
        return

    # Show all libs info
    if all_libs:
        for key, lib in AVAILABLE_LIBS.items():
            _show_lib_info(key, lib, show_usage)
            console.print()
        return

    # Show specific lib info
    if lib_name:
        lib_name = lib_name.lower()
        if lib_name not in AVAILABLE_LIBS:
            console.print(f"[red]Error:[/red] Unknown lib '{lib_name}'")
            console.print(f"[dim]Available libs: {', '.join(AVAILABLE_LIBS.keys())}[/dim]")
            raise typer.Exit(1)

        _show_lib_info(lib_name, AVAILABLE_LIBS[lib_name], show_usage)


def _show_lib_info(key: str, lib: dict, show_usage: bool = False) -> None:
    """Show information about a specific lib."""
    console.print(
        Panel.fit(
            f"[bold blue]{lib['name']}[/bold blue] - {lib['description']}",
            border_style="blue",
        )
    )

    # Dependencies
    if lib["dependencies"]:
        console.print()
        console.print("[bold]Dependencies:[/bold]")
        for dep in lib["dependencies"]:
            console.print(f"  pip install {dep}")

    # Import
    console.print()
    console.print("[bold]Import:[/bold]")
    console.print(f"  [cyan]from fastpy_cli.libs import {lib['name']}[/cyan]")

    # Usage examples
    if show_usage:
        console.print()
        console.print("[bold]Usage Examples:[/bold]")
        _show_lib_usage(key)


# ============================================
# Setup Commands
# ============================================


@app.command("setup")
def setup_command(
    skip_db: bool = typer.Option(False, "--skip-db", help="Skip database configuration"),
    skip_migrations: bool = typer.Option(
        False, "--skip-migrations", help="Skip running migrations"
    ),
    skip_admin: bool = typer.Option(False, "--skip-admin", help="Skip admin user creation"),
    skip_hooks: bool = typer.Option(
        False, "--skip-hooks", help="Skip pre-commit hooks installation"
    ),
) -> None:
    """Complete interactive project setup wizard.

    Run this after creating a new Fastpy project to configure:
    - Environment variables (.env)
    - Database connection
    - Secret key for JWT tokens
    - Database migrations
    - Admin user (optional)
    - Pre-commit hooks (optional)

    Examples:
        fastpy setup                    # Full interactive setup
        fastpy setup --skip-db          # Skip database configuration
        fastpy setup --skip-migrations  # Skip migrations
    """
    from fastpy_cli.setup import full_setup

    full_setup(
        skip_db=skip_db,
        skip_migrations=skip_migrations,
        skip_admin=skip_admin,
        skip_hooks=skip_hooks,
    )


@app.command("setup:env")
def setup_env_command() -> None:
    """Initialize .env file from .env.example.

    Creates a copy of .env.example as .env. If .env already exists,
    you'll be prompted to backup and recreate it.

    Example:
        fastpy setup:env
    """
    from fastpy_cli.setup import is_fastpy_project, setup_env

    if not is_fastpy_project():
        console.print("[red]Error:[/red] Not inside a Fastpy project.")
        raise typer.Exit(1)

    setup_env()


@app.command("setup:db")
def setup_db_command(
    driver: Optional[str] = typer.Option(
        None, "--driver", "-d", help="Database driver (mysql, postgresql, sqlite)"
    ),
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Database host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Database port"),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="Database username"),
    password: Optional[str] = typer.Option(None, "--password", help="Database password"),
    database: Optional[str] = typer.Option(None, "--database", "-n", help="Database name"),
    no_create: bool = typer.Option(False, "--no-create", help="Don't auto-create database"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Non-interactive mode"),
) -> None:
    """Configure database connection.

    Interactively configure database connection or provide options
    for non-interactive setup.

    Supported drivers:
    - mysql: MySQL/MariaDB (recommended for production)
    - postgresql: PostgreSQL
    - sqlite: SQLite (development only)

    Examples:
        fastpy setup:db                          # Interactive setup
        fastpy setup:db -d mysql                 # MySQL with defaults
        fastpy setup:db -d postgresql -n myapp   # PostgreSQL with custom db name
        fastpy setup:db -d sqlite -n dev         # SQLite for development
        fastpy setup:db -d mysql -h localhost -u root -n myapp --password secret -y
    """
    from fastpy_cli.setup import is_fastpy_project, setup_db

    if not is_fastpy_project():
        console.print("[red]Error:[/red] Not inside a Fastpy project.")
        raise typer.Exit(1)

    setup_db(
        driver=driver,
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        create=not no_create,
        interactive=not yes,
    )


@app.command("setup:secret")
def setup_secret_command(
    length: int = typer.Option(64, "--length", "-l", help="Secret key length (default: 64)"),
) -> None:
    """Generate a secure secret key for JWT tokens.

    Generates a cryptographically secure random key and saves it
    to the SECRET_KEY variable in .env.

    Examples:
        fastpy setup:secret          # Generate 64-character key
        fastpy setup:secret -l 128   # Generate 128-character key
    """
    from fastpy_cli.setup import is_fastpy_project, setup_secret

    if not is_fastpy_project():
        console.print("[red]Error:[/red] Not inside a Fastpy project.")
        raise typer.Exit(1)

    setup_secret(length=length)


@app.command("setup:hooks")
def setup_hooks_command() -> None:
    """Install pre-commit hooks for code quality.

    Installs pre-commit hooks using the .pre-commit-config.yaml file.
    Requires git repository and pre-commit package to be installed.

    Example:
        fastpy setup:hooks
    """
    from fastpy_cli.setup import is_fastpy_project, setup_hooks

    if not is_fastpy_project():
        console.print("[red]Error:[/red] Not inside a Fastpy project.")
        raise typer.Exit(1)

    setup_hooks()


def _show_lib_usage(lib_name: str) -> None:
    """Show usage examples for a lib."""
    examples = {
        "http": """
  # GET request
  response = Http.get('https://api.example.com/users')
  data = response.json()

  # POST with JSON
  response = Http.post('https://api.example.com/users', json={'name': 'John'})

  # With authentication
  response = Http.with_token('your-token').get('https://api.example.com/me')

  # With headers
  response = Http.with_headers({'X-Custom': 'value'}).get(url)

  # Testing (fake responses)
  Http.fake({'https://api.example.com/*': {'status': 200, 'json': {'ok': True}}})
  response = Http.get('https://api.example.com/test')
  Http.assert_sent('https://api.example.com/test')
""",
        "mail": """
  # Send email with template
  Mail.to('user@example.com') \\
      .subject('Welcome!') \\
      .send('welcome', {'name': 'John'})

  # Send to multiple recipients
  Mail.to(['user1@example.com', 'user2@example.com']) \\
      .cc('manager@example.com') \\
      .subject('Team Update') \\
      .send('update', {'message': 'Hello team!'})

  # Send raw HTML
  Mail.to('user@example.com') \\
      .subject('Hello') \\
      .html('<h1>Hello World</h1>') \\
      .send()

  # Use specific driver
  Mail.driver('sendgrid').to('user@example.com').send('template', data)
""",
        "cache": """
  # Store value
  Cache.put('key', 'value', ttl=3600)  # 1 hour

  # Get value
  value = Cache.get('key', default='fallback')

  # Remember (get or compute)
  users = Cache.remember('users', lambda: fetch_users(), ttl=600)

  # Delete
  Cache.forget('key')

  # Cache tags
  Cache.tags(['users', 'active']).put('user:1', user_data)
  Cache.tags(['users']).flush()

  # Use specific driver
  Cache.store('redis').put('key', 'value')
""",
        "storage": """
  # Store file
  Storage.put('avatars/user.jpg', file_content)

  # Get file
  content = Storage.get('avatars/user.jpg')

  # Get URL
  url = Storage.url('avatars/user.jpg')

  # Check existence
  if Storage.exists('avatars/user.jpg'):
      print('File exists')

  # Delete file
  Storage.delete('avatars/user.jpg')

  # Use specific disk
  Storage.disk('s3').put('backups/data.zip', content)
  url = Storage.disk('s3').url('backups/data.zip')
""",
        "queue": """
  # Define a job
  class SendEmailJob(Job):
      def __init__(self, user_id: int):
          self.user_id = user_id

      def handle(self):
          user = get_user(self.user_id)
          send_email(user.email, 'Welcome!')

  # Push job to queue
  Queue.push(SendEmailJob(user_id=1))

  # Delay job
  Queue.later(60, SendEmailJob(user_id=1))  # 60 seconds

  # Chain jobs
  Queue.chain([
      ProcessOrderJob(order_id=1),
      SendConfirmationJob(order_id=1),
      UpdateInventoryJob(order_id=1),
  ])

  # Use specific queue
  Queue.on('emails').push(SendEmailJob(user_id=1))
""",
        "events": """
  # Listen to events
  Event.listen('user.registered', lambda data: send_welcome_email(data['user']))

  # Dispatch event
  Event.dispatch('user.registered', {'user': user})

  # Wildcard listeners
  Event.listen('user.*', lambda data: log_user_activity(data))

  # Event subscriber class
  class UserSubscriber:
      def subscribe(self, events):
          events.listen('user.registered', self.on_registered)
          events.listen('user.deleted', self.on_deleted)

      def on_registered(self, data):
          print(f"User registered: {data['user'].id}")

  Event.subscribe(UserSubscriber())
""",
        "notifications": """
  # Define notification
  class OrderShippedNotification(Notification):
      def __init__(self, order):
          self.order = order

      def via(self, notifiable):
          return ['mail', 'database', 'slack']

      def to_mail(self, notifiable):
          return {
              'subject': 'Your order has shipped!',
              'template': 'order_shipped',
              'data': {'order': self.order}
          }

      def to_slack(self, notifiable):
          return {'text': f'Order #{self.order.id} shipped!'}

  # Send notification
  Notify.send(user, OrderShippedNotification(order))

  # On-demand (anonymous) notification
  Notify.route('mail', 'guest@example.com') \\
      .route('slack', '#orders') \\
      .notify(OrderShippedNotification(order))
""",
        "hash": """
  # Hash a password
  hashed = Hash.make('password')

  # Verify password
  if Hash.check('password', hashed):
      print('Password is valid!')

  # Check if rehash needed
  if Hash.needs_rehash(hashed):
      new_hash = Hash.make('password')

  # Use specific algorithm
  hashed = Hash.driver('argon2').make('password')

  # Configure rounds
  Hash.configure('bcrypt', {'rounds': 14})
""",
        "crypt": """
  # Generate encryption key (do once, save to .env)
  key = Crypt.generate_key()
  # Add to .env: APP_KEY=<key>

  # Set key (or use APP_KEY env var)
  Crypt.set_key(key)

  # Encrypt data
  encrypted = Crypt.encrypt('secret data')

  # Encrypt complex data (auto JSON serialized)
  encrypted = Crypt.encrypt({'user_id': 123, 'token': 'abc'})

  # Decrypt
  data = Crypt.decrypt(encrypted)

  # Use specific driver
  encrypted = Crypt.driver('aes').encrypt('secret')
""",
    }

    if lib_name in examples:
        console.print(examples[lib_name])
    else:
        console.print("  [dim]No examples available[/dim]")


def main() -> None:
    """Entry point for the CLI."""
    # Initialize logger with config
    config = get_config()
    setup_logger(log_file=config.log_file)

    # Check if we should proxy to project cli.py
    if len(sys.argv) > 1:
        command = sys.argv[1]

        # Skip flags when determining command
        if command.startswith("-"):
            # Check for verbose/debug flags early
            if "--verbose" in sys.argv:
                setup_logger(verbose=True, log_file=config.log_file)
            if "--debug" in sys.argv:
                setup_logger(debug=True, log_file=config.log_file)
        else:
            # If it's not a fastpy CLI command and we're in a project, proxy it
            if command not in FASTPY_COMMANDS and is_fastpy_project():
                log_debug(f"Proxying command '{command}' to project CLI")
                exit_code = proxy_to_project_cli(sys.argv[1:])
                sys.exit(exit_code)

    app()


if __name__ == "__main__":
    main()
