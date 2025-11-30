#!/usr/bin/env python3
"""Fastpy CLI - Create production-ready FastAPI projects."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    name="fastpy",
    help="Create production-ready FastAPI projects",
    add_completion=False,
)
console = Console()

REPO_URL = "https://github.com/vutia-ent/fastpy.git"
DOCS_URL = "https://fastpy.ve.ke"


def run_command(cmd: list, cwd: Optional[Path] = None, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command."""
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
        import shutil
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
    no_setup: bool = typer.Option(False, "--no-setup", help="Don't run the interactive setup"),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch to clone from"),
) -> None:
    """Create a new Fastpy project."""

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
    console.print(Panel.fit(
        f"[bold blue]Creating new Fastpy project:[/bold blue] [green]{project_name}[/green]",
        border_style="blue",
    ))
    console.print()

    # Clone repository
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Cloning Fastpy template...", total=None)

        if not clone_repository(project_name, branch):
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

    # Show next steps
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  1. [cyan]cd {project_name}[/cyan]")

    if no_setup:
        console.print("  2. [cyan]python3 -m venv venv[/cyan]")
        console.print("  3. [cyan]source venv/bin/activate[/cyan]  (or [cyan]venv\\Scripts\\activate[/cyan] on Windows)")
        console.print("  4. [cyan]pip install -r requirements.txt[/cyan]")
        console.print("  5. [cyan]cp .env.example .env[/cyan]")
        console.print("  6. [cyan]python cli.py serve[/cyan]")
    else:
        console.print("  2. [cyan]./setup.sh[/cyan]  (interactive setup)")

    console.print()
    console.print(f"[dim]Documentation: {DOCS_URL}[/dim]")
    console.print()

    # Ask to run setup
    if not no_setup:
        run_setup = typer.confirm("Would you like to run the interactive setup now?", default=True)
        if run_setup:
            os.chdir(project_path)
            console.print()
            subprocess.run(["bash", "setup.sh"])


@app.command()
def version() -> None:
    """Show the Fastpy CLI version."""
    from fastpy_cli import __version__
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
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider: anthropic, openai, ollama"),
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

    console.print()
    console.print(Panel.fit(
        f"[bold blue]AI Resource Generator[/bold blue]",
        border_style="blue",
    ))
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
                result = subprocess.run(command, shell=True)
                if result.returncode != 0:
                    console.print(f"[red]Command failed with exit code {result.returncode}[/red]")
                    if not typer.confirm("Continue with remaining commands?", default=True):
                        break
                console.print()

        console.print("[green]✓[/green] Done!")
    else:
        console.print("[dim]Commands not executed. Use --execute to run automatically.[/dim]")


@app.command()
def config() -> None:
    """Show AI configuration."""
    import os

    console.print()
    console.print("[bold]AI Configuration[/bold]")
    console.print()

    provider = os.environ.get("FASTPY_AI_PROVIDER", "anthropic")
    console.print(f"  Provider: [cyan]{provider}[/cyan]")

    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        status = "[green]Set[/green]" if key else "[red]Not set[/red]"
        console.print(f"  ANTHROPIC_API_KEY: {status}")
    elif provider == "openai":
        key = os.environ.get("OPENAI_API_KEY", "")
        status = "[green]Set[/green]" if key else "[red]Not set[/red]"
        console.print(f"  OPENAI_API_KEY: {status}")
    elif provider == "ollama":
        model = os.environ.get("OLLAMA_MODEL", "llama3.2")
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        console.print(f"  OLLAMA_MODEL: [cyan]{model}[/cyan]")
        console.print(f"  OLLAMA_HOST: [cyan]{host}[/cyan]")

    console.print()
    console.print("[dim]Set provider with: export FASTPY_AI_PROVIDER=anthropic|openai|ollama[/dim]")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
