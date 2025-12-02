# Changelog

All notable changes to Fastpy CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.5.0] - 2024-12-02

### Added

- **Laravel-Style Libs**: Complete abstraction library system
  - `Http` - HTTP client with fluent API (GET, POST, PUT, PATCH, DELETE)
  - `Mail` - Email with drivers (SMTP, SendGrid, Mailgun, AWS SES)
  - `Cache` - Caching with drivers (Memory, File, Redis)
  - `Storage` - File storage with drivers (Local, S3, Memory)
  - `Queue` - Job queues with drivers (Sync, Memory, Redis, Database)
  - `Event` - Event dispatcher with listeners and subscribers
  - `Notify` - Multi-channel notifications (Mail, Database, Slack, SMS)
  - `Hash` - Password hashing (bcrypt, Argon2, PBKDF2-SHA256)
  - `Crypt` - Data encryption (Fernet, AES-256-CBC)

- **Service Container**: IoC container for dependency injection
  - Singleton and factory bindings
  - Automatic resolution
  - Named service registration

- **Facade Pattern**: Static interface to container services
  - Clean, expressive API
  - Easy testing with fakes/mocks

- **Libs Command**: New `fastpy libs` command
  - `fastpy libs` - List all available libs
  - `fastpy libs <name>` - View lib details
  - `fastpy libs <name> --usage` - Show usage examples

### Security

- **CRITICAL: Fixed path traversal vulnerability** in Storage LocalDriver
  - Added `.resolve()` and `relative_to()` validation
  - Blocks `../` sequences attempting to escape storage root
  - CVSS: 9.8 (Critical)

- **CRITICAL: Mitigated insecure deserialization** in Queue Jobs
  - Added warning documentation about pickle risks
  - Added `SerializableJob` class with safer JSON serialization
  - Added `ALLOWED_MODULES` allowlist for class loading validation
  - CVSS: 9.8 (Critical)

- **HIGH: Added SSRF protection** to HTTP client
  - Blocks requests to private IP ranges (10.x, 172.16.x, 192.168.x, 127.x)
  - Blocks AWS metadata endpoint (169.254.169.254)
  - Added `is_safe_url()` validation function
  - Added `allow_private_ips()` method for explicit opt-out
  - CVSS: 7.5 (High)

- **MEDIUM: Strengthened password hashing defaults**
  - Bcrypt: Increased rounds from 12 to 13
  - PBKDF2-SHA256: Increased iterations from 100,000 to 600,000 (OWASP 2023)

### Example Usage

```python
from fastpy_cli.libs import Http, Mail, Cache, Storage, Hash, Crypt

# HTTP with SSRF protection (enabled by default)
response = Http.with_token('secret').get('https://api.example.com/data')

# Mail with template
Mail.to('user@example.com').subject('Welcome').send('welcome', {'name': 'John'})

# Cache with remember pattern
users = Cache.remember('users', lambda: fetch_users(), ttl=3600)

# Storage with path traversal protection
Storage.put('uploads/file.pdf', content)  # Safe
# Storage.get('../../../etc/passwd')      # Raises ValueError

# Secure password hashing (bcrypt 13 rounds)
hashed = Hash.make('password')
if Hash.check('password', hashed):
    print('Valid!')

# Data encryption
encrypted = Crypt.encrypt({'user_id': 123, 'token': 'secret'})
data = Crypt.decrypt(encrypted)
```

---

## [0.4.0] - 2024-12-02

### Added

- **Configuration System**: `~/.fastpy/config.toml` support
  - Persistent AI provider settings
  - Default project settings (git, setup, branch)
  - Environment variable overrides
  - `fastpy config` command
  - `fastpy init` to create config

- **Doctor Command**: `fastpy doctor` for diagnostics
  - Python version check
  - Git installation verification
  - AI provider configuration validation
  - Ollama status detection
  - Project-specific checks

- **Logging System**: Comprehensive logging
  - `--verbose` for detailed output
  - `--debug` for debug-level logging
  - Optional file logging

- **Shell Completions**: Built-in support
  - Bash, Zsh, Fish, PowerShell
  - `fastpy --install-completion`

- **Retry Logic**: AI API request retry
  - Exponential backoff
  - Configurable retries and timeout
  - Rate limit handling

- **JSON Schema Validation**: AI response validation
  - Command structure validation
  - Unsafe command filtering

- **Test Suite**: Comprehensive coverage
  - Unit and integration tests
  - pytest with coverage

- **CI/CD Pipeline**: GitHub Actions
  - Multi-platform (Linux, macOS, Windows)
  - Multi-Python (3.9-3.13)
  - Automated PyPI releases

### Changed

- Replaced `shell=True` with safe command execution
- Improved AI provider implementations
- Added `-v` as alias for `--version`

### Fixed

- Improved error messages
- Better network timeout handling
- Fixed markdown parsing in AI responses

### Security

- AI commands validated before execution
- Dangerous command patterns blocked
- Only Fastpy commands allowed in AI mode

---

## [0.3.1] - 2024-11-15

### Fixed

- Fixed version display in CLI

---

## [0.3.0] - 2024-11-10

### Added

- Command proxy to project's `cli.py`
- Automatic Fastpy project detection
- Cross-platform venv support

### Changed

- Commands inside projects forwarded to project CLI

---

## [0.2.0] - 2024-11-01

### Added

- AI-powered generation: `fastpy ai` command
- Provider support: Anthropic, OpenAI, Ollama
- `--execute` flag for auto-execution
- `--dry-run` flag for preview

---

## [0.1.0] - 2024-10-15

### Added

- Initial release
- `fastpy new` - Create projects
- `fastpy version` - Show version
- `fastpy docs` - Open documentation
- `fastpy upgrade` - Self-update
- Git repository initialization
- Interactive setup option

---

[Unreleased]: https://github.com/vutia-ent/fastpy-cli/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/vutia-ent/fastpy-cli/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/vutia-ent/fastpy-cli/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/vutia-ent/fastpy-cli/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/vutia-ent/fastpy-cli/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/vutia-ent/fastpy-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/vutia-ent/fastpy-cli/releases/tag/v0.1.0
