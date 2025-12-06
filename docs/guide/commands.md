# Commands Reference

## Global Commands

These commands work from anywhere.

### fastpy new

Create a new Fastpy project.

```bash
fastpy new <project-name> [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--install, -i` | Auto-setup venv and install dependencies |
| `--branch, -b` | Clone from specific branch (default: main) |
| `--no-git` | Skip git repository initialization |

**Examples:**
```bash
fastpy new my-api                    # Create project
fastpy new my-api --install          # Create + auto-setup
fastpy new my-api -b dev             # Clone from dev branch
```

### fastpy install

Install project dependencies and run setup wizard. Run this inside a Fastpy project.

```bash
fastpy install [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--skip-setup` | Skip the interactive setup wizard |
| `--skip-venv` | Skip virtual environment creation |
| `-r, --requirements` | Requirements file (default: requirements.txt) |

**Examples:**
```bash
fastpy install                       # Full install + setup
fastpy install --skip-setup          # Install deps only
fastpy install -r requirements-dev.txt
```

### fastpy version

Show CLI version.

```bash
fastpy version
```

### fastpy upgrade

Upgrade Fastpy CLI to latest version.

```bash
fastpy upgrade
```

### fastpy doctor

Diagnose environment issues.

```bash
fastpy doctor
```

Checks:
- Python version
- Git installation
- Config file status
- AI provider setup
- Virtual environment (if in project)
- .env file (if in project)

### fastpy docs

Open documentation in browser.

```bash
fastpy docs
```

### fastpy config

Show or initialize configuration.

```bash
fastpy config [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--init` | Create config file |
| `--path` | Show config file path |

### fastpy init

Initialize Fastpy configuration file at `~/.fastpy/config.toml`.

```bash
fastpy init [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--force, -f` | Overwrite existing config |

### fastpy libs

Explore available libs (Laravel-style facades).

```bash
fastpy libs [name] [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--list, -l` | List all libs |
| `--usage, -u` | Show usage examples |
| `--all, -a` | Show all libs info |

**Examples:**
```bash
fastpy libs                          # List all libs
fastpy libs http                     # Show http lib info
fastpy libs http --usage             # Show usage examples
```

---

## Setup Commands

Run these inside a Fastpy project directory.

### fastpy setup

Complete interactive project setup wizard.

```bash
fastpy setup [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--skip-db` | Skip database configuration |
| `--skip-migrations` | Skip running migrations |
| `--skip-admin` | Skip admin user creation |
| `--skip-hooks` | Skip pre-commit hooks |

### fastpy setup:env

Initialize .env file from .env.example.

```bash
fastpy setup:env
```

### fastpy setup:db

Configure database connection.

```bash
fastpy setup:db [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-d, --driver` | Database driver (mysql, postgresql, sqlite) |
| `-h, --host` | Database host |
| `-p, --port` | Database port |
| `-u, --username` | Database username |
| `--password` | Database password |
| `-n, --database` | Database name |
| `--no-create` | Don't auto-create database |
| `-y, --yes` | Non-interactive mode |

**Examples:**
```bash
fastpy setup:db                      # Interactive
fastpy setup:db -d mysql             # MySQL with defaults
fastpy setup:db -d sqlite -n dev     # SQLite for development
fastpy setup:db -d mysql -h localhost -u root -n myapp -y
```

### fastpy setup:secret

Generate secure JWT secret key.

```bash
fastpy setup:secret [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-l, --length` | Secret key length (default: 64) |

### fastpy setup:hooks

Install pre-commit hooks.

```bash
fastpy setup:hooks
```

---

## AI Commands

### fastpy ai

Generate resources using AI.

```bash
fastpy ai "<prompt>" [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-p, --provider` | AI provider (anthropic, openai, ollama) |
| `-e, --execute` | Execute commands automatically |
| `-d, --dry-run` | Preview commands without executing |

**Examples:**
```bash
fastpy ai "Create a blog with posts and categories"
fastpy ai "E-commerce with products and orders" --execute
fastpy ai "User management" --provider ollama --dry-run
```

### fastpy ai:config

Configure AI provider and API keys.

```bash
fastpy ai:config [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-p, --provider` | Set provider (anthropic, openai, google, groq, ollama) |
| `-k, --key` | Set API key (saves to .env) |
| `-t, --test` | Test connection |
| `-e, --env` | Path to .env file |

**Examples:**
```bash
fastpy ai:config                     # Show current config
fastpy ai:config -p anthropic        # Set provider
fastpy ai:config -k sk-xxx           # Set API key
fastpy ai:config --test              # Test connection
```

---

## Project Commands

> These commands are proxied to your project's `cli.py`. Run inside a Fastpy project.

### Development

| Command | Description |
|---------|-------------|
| `fastpy serve` | Start development server |
| `fastpy test` | Run tests |
| `fastpy route:list` | List all routes |

### Code Generation

| Command | Description |
|---------|-------------|
| `fastpy make:resource <name>` | Generate complete resource (model, controller, service, routes) |
| `fastpy make:model <name>` | Generate model |
| `fastpy make:controller <name>` | Generate controller |
| `fastpy make:service <name>` | Generate service |
| `fastpy make:route <name>` | Generate route |
| `fastpy make:admin` | Create admin user |

### Database

| Command | Description |
|---------|-------------|
| `fastpy db:migrate` | Run database migrations |
| `fastpy db:rollback` | Rollback last migration |
| `fastpy db:seed` | Seed the database |
| `fastpy db:fresh` | Drop all tables and re-run migrations |
