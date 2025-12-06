# Configuration

## Config File

Fastpy uses `~/.fastpy/config.toml` for global settings.

### Initialize

```bash
fastpy init
```

### Default Configuration

```toml
[ai]
provider = "anthropic"    # anthropic, openai, google, groq, ollama
timeout = 30
max_retries = 3

[ai.models]
anthropic = "claude-sonnet-4-20250514"
openai = "gpt-4"
ollama = "llama2"

[defaults]
git = true
setup = true
branch = "main"

[logging]
level = "INFO"            # DEBUG, INFO, WARNING, ERROR
file = ""                 # Optional log file path
```

## Environment Variables

### AI Providers

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `GOOGLE_API_KEY` | Google AI (Gemini) API key |
| `GROQ_API_KEY` | Groq Cloud API key |
| `OLLAMA_HOST` | Ollama server URL (default: `http://localhost:11434`) |
| `OLLAMA_MODEL` | Ollama model name (default: `llama2`) |

### Application

| Variable | Description |
|----------|-------------|
| `FASTPY_AI_PROVIDER` | Override default AI provider |
| `APP_KEY` | Encryption key for Crypt lib |

## Project Configuration

Each Fastpy project uses a `.env` file for project-specific settings.

### Initialize .env

```bash
fastpy setup:env
```

### Common Project Variables

```ini
# Application
APP_NAME=MyApp
APP_ENV=development
APP_DEBUG=true
SECRET_KEY=your-generated-secret-key

# Database
DB_DRIVER=mysql
DATABASE_URL=mysql://root:password@localhost:3306/myapp

# Server
HOST=0.0.0.0
PORT=8000

# AI (optional)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

## Managing Configuration

### View Current Config

```bash
fastpy config
```

### Show Config Path

```bash
fastpy config --path
```

### Reinitialize Config

```bash
fastpy init --force
```

### AI Configuration

```bash
# Set provider
fastpy ai:config -p anthropic

# Set API key (saves to project .env)
fastpy ai:config -k YOUR_API_KEY

# Test connection
fastpy ai:config --test
```

## Debugging

Enable verbose or debug output:

```bash
fastpy --verbose <command>
fastpy --debug <command>
```

Check environment with doctor:

```bash
fastpy doctor
```

This checks:
- Python version (requires 3.9+)
- Git installation
- Config file existence
- AI provider API keys
- Virtual environment (in project)
- .env file (in project)
