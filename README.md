<p align="center">
  <img src="https://fastpy.ve.ke/logo.svg" alt="Fastpy CLI" width="120">
</p>

<h1 align="center">Fastpy CLI</h1>

<p align="center">
  <strong>Create production-ready FastAPI projects with one command.</strong>
</p>

<p align="center">
  <a href="https://badge.fury.io/py/fastpy-cli"><img src="https://badge.fury.io/py/fastpy-cli.svg" alt="PyPI version"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/vutia-ent/fastpy-cli/actions/workflows/test.yml"><img src="https://github.com/vutia-ent/fastpy-cli/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
</p>

<p align="center">
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#fastpy-libs">Libs</a> •
  <a href="#documentation">Docs</a>
</p>

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Features](#features)
- [Commands](#commands)
- [AI-Powered Generation](#ai-powered-generation)
- [Fastpy Libs](#fastpy-libs)
  - [Http](#http-client)
  - [Mail](#email)
  - [Cache](#caching)
  - [Storage](#file-storage)
  - [Queue](#job-queues)
  - [Events](#events)
  - [Notifications](#notifications)
  - [Hash](#password-hashing)
  - [Crypt](#encryption)
- [Configuration](#configuration)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

### pip (recommended)

```bash
pip install fastpy-cli
```

### pipx (isolated environment)

```bash
pipx install fastpy-cli
```

### Homebrew (macOS)

```bash
brew tap vutia-ent/tap
brew install fastpy
```

### Verify Installation

```bash
fastpy version
```

### Troubleshooting: pip Not Recognized

If you get `pip: command not found`, use `pip3` instead:

```bash
pip3 install fastpy-cli
```

To create a `pip` alias (optional):

**macOS/Linux:**
```bash
echo 'alias pip=pip3' >> ~/.zshrc  # or ~/.bashrc for Linux
source ~/.zshrc
```

**Windows:** Python 3.x installers usually include both `pip` and `pip3`. If not, reinstall Python and check "Add to PATH".

### Troubleshooting: Command Not Found

If you get `fastpy: command not found` after installing with pip, the Python scripts directory isn't in your PATH.

**macOS:**
```bash
# Add Python scripts to PATH
echo 'export PATH="'$(python3 -m site --user-base)/bin':$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Linux:**
```bash
# Add Python scripts to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
# Find Python scripts path
python -m site --user-site
# Add the Scripts folder (replace USERNAME with your username)
# C:\Users\USERNAME\AppData\Roaming\Python\Python3X\Scripts
# Add this to your PATH via System Properties > Environment Variables
```

**Alternative:** Use pipx (automatically handles PATH):
```bash
pipx install fastpy-cli
```

---

## Quick Start

```bash
# 1. Create a new project
fastpy new my-api

# 2. Navigate to the project
cd my-api

# 3. Generate resources with AI
fastpy ai "Create a blog with posts, categories, and tags"

# 4. Start the development server
fastpy serve
```

---

## Features

| Feature | Description |
|---------|-------------|
| **One-Command Setup** | Production-ready FastAPI project in seconds |
| **AI Code Generation** | Generate resources using natural language |
| **Multiple AI Providers** | Anthropic Claude, OpenAI GPT, Ollama |
| **Laravel-Style Libs** | Http, Mail, Cache, Storage, Queue, Events, and more |
| **Smart Detection** | Seamlessly works inside Fastpy projects |
| **Environment Diagnostics** | Built-in `doctor` command |
| **Shell Completions** | Bash, Zsh, Fish, PowerShell |

---

## Commands

### Global Commands

| Command | Description |
|---------|-------------|
| `fastpy new <name>` | Create a new Fastpy project |
| `fastpy ai <prompt>` | Generate resources using AI |
| `fastpy libs [name]` | Explore Laravel-style libs |
| `fastpy doctor` | Diagnose environment issues |
| `fastpy config` | Show/manage configuration |
| `fastpy init` | Initialize configuration file |
| `fastpy version` | Show CLI version |
| `fastpy docs` | Open documentation |
| `fastpy upgrade` | Upgrade to latest version |

### Project Commands

> Run these inside a Fastpy project directory

| Command | Description |
|---------|-------------|
| `fastpy serve` | Start development server |
| `fastpy make:resource <name>` | Generate complete resource |
| `fastpy make:model <name>` | Generate model |
| `fastpy make:controller <name>` | Generate controller |
| `fastpy make:service <name>` | Generate service |
| `fastpy db:migrate` | Run database migrations |
| `fastpy db:seed` | Seed the database |
| `fastpy route:list` | List all routes |
| `fastpy test` | Run tests |

---

## AI-Powered Generation

Generate resources using natural language with multiple AI providers.

### Basic Usage

```bash
# Generate from description
fastpy ai "Create a blog with posts, categories, and tags"

# Auto-execute commands
fastpy ai "E-commerce with products, orders, and customers" --execute

# Preview without executing
fastpy ai "User management system" --dry-run
```

### Providers

#### Anthropic Claude (Default)

```bash
export ANTHROPIC_API_KEY=your-key
fastpy ai "Create a user authentication system"
```

#### OpenAI GPT

```bash
export OPENAI_API_KEY=your-key
fastpy ai "Create a REST API for tasks" --provider openai
```

#### Ollama (Local)

```bash
ollama serve  # Start Ollama
fastpy ai "Create a blog system" --provider ollama
```

---

## Fastpy Libs

Laravel-style facades for common development tasks. Clean, expressive APIs for HTTP, email, caching, storage, queues, events, notifications, hashing, and encryption.

```bash
# Explore available libs
fastpy libs

# View usage examples
fastpy libs http --usage
```

### Import

```python
from fastpy_cli.libs import Http, Mail, Cache, Storage, Queue, Event, Notify, Hash, Crypt
```

---

### Http Client

Make HTTP requests with a fluent, chainable API.

```python
from fastpy_cli.libs import Http

# Simple requests
response = Http.get('https://api.example.com/users')
data = response.json()

# POST with JSON
response = Http.post('https://api.example.com/users', json={
    'name': 'John',
    'email': 'john@example.com'
})

# With authentication
response = Http.with_token('your-api-token').get('/api/protected')
response = Http.with_basic_auth('user', 'pass').get('/api/auth')

# With headers and timeout
response = Http.with_headers({'X-Custom': 'value'}) \
    .timeout(60) \
    .retry(3) \
    .get('https://api.slow.com/data')

# Async requests
response = await Http.async_().aget('https://api.example.com/data')
```

**Features:** GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS | Bearer/Basic auth | Custom headers | Retry with backoff | Timeouts | Async support | SSRF protection

---

### Email

Send emails with multiple driver support.

```python
from fastpy_cli.libs import Mail

# Send with template
Mail.to('user@example.com') \
    .subject('Welcome to Our App!') \
    .send('emails/welcome', {'name': 'John'})

# Multiple recipients
Mail.to(['user1@example.com', 'user2@example.com']) \
    .cc('manager@example.com') \
    .bcc('archive@example.com') \
    .subject('Team Update') \
    .send('emails/update', {'message': 'Hello team!'})

# Raw HTML
Mail.to('user@example.com') \
    .subject('Hello') \
    .html('<h1>Hello World</h1>') \
    .text('Hello World') \
    .send()

# With attachments
Mail.to('user@example.com') \
    .subject('Your Invoice') \
    .attach('/path/to/invoice.pdf') \
    .send('emails/invoice', {'invoice': invoice})

# Different driver
Mail.driver('sendgrid').to('user@example.com').send('template', data)
```

**Drivers:** SMTP, SendGrid, Mailgun, AWS SES, Log (dev)

---

### Caching

Cache data with multiple backend support.

```python
from fastpy_cli.libs import Cache

# Store and retrieve
Cache.put('key', 'value', ttl=3600)  # 1 hour
value = Cache.get('key', default='fallback')

# Check existence
if Cache.has('key'):
    print('Cached!')

# Remember pattern (get or compute)
users = Cache.remember('all_users', lambda: User.all(), ttl=600)

# Increment/decrement
Cache.increment('page_views')
Cache.decrement('available_seats', 2)

# Delete
Cache.forget('key')
Cache.flush()  # Clear all

# Tagged cache
Cache.tags(['users', 'permissions']).put('user:1:roles', roles)
Cache.tags(['users']).flush()  # Clear all user-related cache

# Different store
Cache.store('redis').put('key', 'value')
```

**Drivers:** Memory, File, Redis

---

### File Storage

Store and retrieve files with multiple backends.

```python
from fastpy_cli.libs import Storage

# Store files
Storage.put('avatars/user-123.jpg', file_content)
Storage.put('documents/report.pdf', pdf_bytes)

# Retrieve
content = Storage.get('avatars/user-123.jpg')
exists = Storage.exists('avatars/user-123.jpg')

# Get URL
url = Storage.url('avatars/user-123.jpg')

# List files
files = Storage.files('avatars/')
all_files = Storage.all_files('documents/')

# File operations
Storage.copy('old.jpg', 'new.jpg')
Storage.move('temp/file.txt', 'permanent/file.txt')
Storage.delete('old-file.txt')

# Directories
Storage.make_directory('uploads/2024')
Storage.delete_directory('temp/')

# Different disk
Storage.disk('s3').put('backups/db.sql', content)
url = Storage.disk('s3').url('backups/db.sql')
```

**Drivers:** Local filesystem, AWS S3, Memory (testing)

---

### Job Queues

Queue background jobs for async processing.

```python
from fastpy_cli.libs import Queue, Job

# Define a job
class SendWelcomeEmail(Job):
    def __init__(self, user_id: int):
        self.user_id = user_id

    def handle(self):
        user = User.find(self.user_id)
        Mail.to(user.email).send('welcome', {'user': user})

# Dispatch immediately
Queue.push(SendWelcomeEmail(user_id=123))

# Delay execution
Queue.later(60, SendWelcomeEmail(user_id=123))  # 60 seconds

# Named queue
Queue.on('emails').push(SendWelcomeEmail(user_id=123))

# Chain jobs (sequential execution)
Queue.chain([
    ProcessPayment(order_id=1),
    SendConfirmation(order_id=1),
    UpdateInventory(order_id=1),
])

# Job configuration
class SlowJob(Job):
    queue = 'slow'       # Queue name
    tries = 5            # Max attempts
    timeout = 300        # 5 minutes
```

**Drivers:** Sync, Memory, Redis, Database

---

### Events

Dispatch and listen to application events.

```python
from fastpy_cli.libs import Event

# Register listeners
Event.listen('user.registered', lambda data: send_welcome_email(data['user']))
Event.listen('order.placed', lambda data: notify_warehouse(data['order']))

# Dispatch events
Event.dispatch('user.registered', {'user': user})

# Wildcard listeners
Event.listen('user.*', lambda data: log_user_activity(data))
Event.listen('*.created', lambda data: log_creation(data))

# Event subscribers
class UserEventSubscriber:
    def subscribe(self, events):
        events.listen('user.registered', self.on_registered)
        events.listen('user.login', self.on_login)
        events.listen('user.deleted', self.on_deleted)

    def on_registered(self, data):
        send_welcome_email(data['user'])

    def on_login(self, data):
        log_login(data['user'], data['ip'])

    def on_deleted(self, data):
        cleanup_user_data(data['user_id'])

Event.subscribe(UserEventSubscriber())
```

---

### Notifications

Send notifications through multiple channels.

```python
from fastpy_cli.libs import Notify, Notification

# Define a notification
class OrderShipped(Notification):
    def __init__(self, order):
        self.order = order

    def via(self, notifiable) -> list:
        return ['mail', 'database', 'slack']

    def to_mail(self, notifiable) -> dict:
        return {
            'subject': 'Your order has shipped!',
            'template': 'emails/order-shipped',
            'data': {'order': self.order, 'user': notifiable}
        }

    def to_database(self, notifiable) -> dict:
        return {
            'type': 'order_shipped',
            'data': {'order_id': self.order.id}
        }

    def to_slack(self, notifiable) -> dict:
        return {
            'text': f'Order #{self.order.id} has been shipped!',
            'channel': '#orders'
        }

# Send to user
Notify.send(user, OrderShipped(order))

# Send to multiple users
Notify.send(users, OrderShipped(order))

# On-demand notification (no user model)
Notify.route('mail', 'guest@example.com') \
    .route('slack', '#general') \
    .notify(OrderShipped(order))
```

**Channels:** Mail, Database, Slack, SMS (Twilio/Nexmo)

---

### Password Hashing

Securely hash and verify passwords.

```python
from fastpy_cli.libs import Hash

# Hash a password
hashed = Hash.make('secret-password')

# Verify a password
if Hash.check('secret-password', hashed):
    print('Password is correct!')
else:
    print('Invalid password')

# Check if rehash needed (e.g., after upgrading algorithm)
if Hash.needs_rehash(hashed):
    new_hash = Hash.make('secret-password')
    user.password = new_hash
    user.save()

# Use specific algorithm
hashed = Hash.driver('argon2').make('password')  # Recommended
hashed = Hash.driver('bcrypt').make('password')  # Default

# Configure bcrypt rounds
Hash.configure('bcrypt', {'rounds': 14})
```

**Algorithms:** bcrypt (default), Argon2 (recommended), PBKDF2-SHA256

---

### Encryption

Encrypt and decrypt sensitive data.

```python
from fastpy_cli.libs import Crypt

# Generate a key (do once, save to .env)
key = Crypt.generate_key()
# Add to .env: APP_KEY=<key>

# Set the key
Crypt.set_key(key)  # Or use APP_KEY environment variable

# Encrypt/decrypt strings
encrypted = Crypt.encrypt('sensitive data')
decrypted = Crypt.decrypt(encrypted)

# Encrypt complex data (auto JSON serialized)
encrypted = Crypt.encrypt({
    'user_id': 123,
    'session_token': 'abc123',
    'expires_at': '2024-12-31'
})
data = Crypt.decrypt(encrypted)  # Returns dict

# Different driver
encrypted = Crypt.driver('aes').encrypt('secret')
```

**Algorithms:** Fernet (AES-128-CBC with HMAC), AES-256-CBC

---

## Configuration

### Config File

Fastpy uses `~/.fastpy/config.toml`:

```toml
[ai]
provider = "anthropic"    # anthropic, openai, ollama
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

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `llama2` |
| `FASTPY_AI_PROVIDER` | Default AI provider | `anthropic` |
| `APP_KEY` | Encryption key for Crypt | - |

### Commands

```bash
# Initialize config file
fastpy init

# Show current configuration
fastpy config

# Show config file path
fastpy config --path

# Run environment diagnostics
fastpy doctor
```

---

## Security

Fastpy CLI takes security seriously. See [SECURITY.md](SECURITY.md) for:

- Security vulnerability fixes
- Best practices for using the libs
- Reporting security issues

### Key Security Features

- **SSRF Protection**: HTTP client blocks requests to private IPs
- **Path Traversal Protection**: Storage prevents directory escape
- **Secure Defaults**: bcrypt with 13 rounds, PBKDF2 with 600K iterations
- **Safe Serialization**: JSON-based job serialization option
- **Command Validation**: AI commands validated before execution

---

## Shell Completions

```bash
# Install for your shell
fastpy --install-completion bash
fastpy --install-completion zsh
fastpy --install-completion fish
fastpy --install-completion powershell
```

---

## What is Fastpy?

Fastpy is a production-ready FastAPI starter template featuring:

- **FastAPI** - Modern, high-performance Python web framework
- **SQLModel** - SQL databases with Python type hints
- **JWT Authentication** - Secure auth with access/refresh tokens
- **MVC Architecture** - Clean, maintainable code structure
- **PostgreSQL/MySQL** - Multi-database support
- **Alembic** - Database migrations
- **pytest** - Testing with factory-boy

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Clone and setup
git clone https://github.com/vutia-ent/fastpy-cli.git
cd fastpy-cli
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check fastpy_cli/
black fastpy_cli/
```

---

## Links

- [Documentation](https://fastpy.ve.ke)
- [Changelog](CHANGELOG.md)
- [Security](SECURITY.md)
- [GitHub](https://github.com/vutia-ent/fastpy-cli)
- [PyPI](https://pypi.org/project/fastpy-cli/)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with ❤️ by <a href="https://ve.ke">Vutia Enterprise</a>
</p>
