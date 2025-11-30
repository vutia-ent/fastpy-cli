# Fastpy CLI

Create production-ready FastAPI projects with one command.

[![PyPI version](https://badge.fury.io/py/fastpy-cli.svg)](https://badge.fury.io/py/fastpy-cli)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

### Using pip (recommended)

```bash
pip install fastpy-cli
```

### Using pipx (isolated environment)

```bash
pipx install fastpy-cli
```

### Using Homebrew (macOS)

```bash
brew tap vutia-ent/tap
brew install fastpy
```

## Usage

### Create a new project

```bash
fastpy new my-api
```

This will:
1. Clone the Fastpy template
2. Initialize a fresh git repository
3. Optionally run the interactive setup

### Options

```bash
# Create without running interactive setup
fastpy new my-api --no-setup

# Create without initializing git
fastpy new my-api --no-git

# Create from a specific branch
fastpy new my-api --branch dev
```

### Other commands

```bash
# Show version
fastpy version

# Open documentation
fastpy docs

# Upgrade CLI
fastpy upgrade
```

## What is Fastpy?

Fastpy is a production-ready FastAPI starter template with:

- **FastAPI** - Modern, fast Python web framework
- **SQLModel** - SQL databases with Python type hints
- **JWT Authentication** - Secure auth with refresh tokens
- **MVC Architecture** - Clean, maintainable code structure
- **FastCLI** - Code generator for rapid development
- **PostgreSQL/MySQL** - Multi-database support
- **Alembic** - Database migrations
- **Testing** - pytest with factory-boy

## Documentation

Full documentation available at [fastpy.ve.ke](https://fastpy.ve.ke)

## License

MIT License - see [LICENSE](LICENSE) for details.
