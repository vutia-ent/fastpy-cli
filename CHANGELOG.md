# Changelog

All notable changes to Fastpy CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [1.1.8] - 2025-12-06

### Fixed

- Fixed lint errors in libs directory (exception chaining, import sorting, deprecated typing)
- Fixed black formatting issues
- Fixed CI workflow: exclude libs from mypy, add id-token permissions for PyPI publish
- All tests passing on Python 3.9-3.13, Linux, macOS, and Windows

---

## [1.1.2] - 2025-12-06

### Added

- **Google Gemini Provider**: Full support for Google's Gemini 2.0 Flash model
  - Configure with `fastpy ai:config -p google`
  - Set `GOOGLE_API_KEY` environment variable
  - Default model: `gemini-2.0-flash`

- **Groq Provider**: Support for Groq's fast inference API
  - Configure with `fastpy ai:config -p groq`
  - Set `GROQ_API_KEY` environment variable
  - Default model: `llama-3.3-70b-versatile`

### Improved

- **ai:config Command**: Now suggests running `ai:init` when switching to providers that support AI assistant configuration (Claude, Gemini)
- **Provider Selection**: Expanded from 3 to 5 AI providers (anthropic, openai, google, groq, ollama)

---

## [1.1.1] - 2025-12-06

### Added

- **Post-Generation Workflow**: Enhanced `fastpy ai` command with follow-up prompts
  - Detects models created without routes (using `make:model` instead of `make:resource`)
  - Prompts user to generate routes for models that don't have them
  - Prompts user to run database migrations after resource generation
  - Streamlines the complete resource creation workflow

### Improved

- **Developer Experience**: Complete resource setup in a single command flow
  - No need to manually run `make:route` after AI generation
  - No need to remember to run `db:migrate` separately

---

## [1.1.0] - 2025-12-06

### 🎉 First Stable Release

This release marks Fastpy CLI as **production-ready**. After extensive testing and community feedback, we're confident in the stability and feature completeness of the CLI.

### ✨ Highlights

- **Command Normalization**: All commands now consistently use `fastpy` prefix
- **Renamed `init:ai` to `ai:init`**: Follows the `category:action` naming convention
- **Improved Test Coverage**: All tests updated for new command patterns
- **Clean Branch Strategy**: Development files separated from production

### Changed

- **Command Naming Convention**: Standardized all commands to follow `category:action` pattern
  - `init:ai` → `ai:init` (generate AI assistant configuration files)
  - All commands now use `fastpy` prefix consistently

- **Safe Command Prefixes**: Updated allowlist for AI-generated commands
  - Added `fastpy ai:`, `fastpy setup:`, `fastpy deploy:`, `fastpy domain:`, `fastpy env:`, `fastpy service:` prefixes
  - Removed legacy `python cli.py` prefixes

### Fixed

- **Test Suite**: Updated all tests to use `fastpy` command prefix
  - `test_utils.py`: Fixed command validation and safe command tests
  - `test_ai.py`: Updated AI response parsing test data

### Documentation

- Updated all documentation to reflect `ai:init` command
- Fixed JSON syntax highlighting in README (removed invalid `//` comments)

### Internal

- Improved code organization and consistency
- Enhanced command validation for AI-generated commands

---

## [0.6.7] - 2025-12-06

### Fixed

- **AI Command Execution**: Fixed `FileNotFoundError: 'python'` when running AI-generated commands
  - Updated system prompt to use `fastpy` prefix instead of `python cli.py`
  - Added automatic normalization of old-style `python cli.py` commands to `fastpy`
  - Commands now execute correctly on systems without `python` alias

---

## [0.6.6] - 2025-12-06

### Improved

- **User-Friendly API Error Messages**: Clear, actionable error messages for AI commands
  - 401: Invalid API key with link to get a new one
  - 403: Access forbidden with permission guidance
  - 429: Rate limit exceeded with link to check billing/usage
  - 500/502/503: Server errors with appropriate guidance
  - Shows API response message when available
  - Specific error handling for timeout and connection failures

### Changed

- Updated `ai:config --test` to show helpful error details
- Improved error messages in `fastpy ai` command with retry feedback

---

## [0.6.5] - 2025-12-06

### Added

- **CLI API Key Configuration**: Set AI provider and API key directly from CLI
  - `fastpy ai:config -p anthropic -k YOUR_KEY` - Set provider and key together
  - `fastpy ai:config -k YOUR_KEY` - Set key for current provider
  - `--env/-e` flag to specify custom `.env` file path
  - Keys are saved to project's `.env` file for security
  - Automatic environment variable detection per provider

### Changed

- Updated `ai:config` help text with new key management examples
- Improved interactive setup display with key configuration commands

---

## [0.6.4] - 2025-12-06

### Fixed

- Added missing `toml` dependency for `ai:config` command
  - Fixes `ModuleNotFoundError: No module named 'toml'` when configuring AI provider

### Changed

- Added `toml>=0.10.0` to package dependencies

---

## [0.6.3] - 2025-12-06

### Added

- **SQLite Database Support**: Full SQLite support in project templates
  - Added `sqlite` to `db_driver` Literal type in settings
  - Added async URL conversion for SQLite (`sqlite+aiosqlite://`)

### Fixed

- Database settings template now properly supports SQLite driver selection

---

## [0.6.2] - 2025-12-05

### Fixed

- **pip Installation Compatibility**: Fixed psycopg2-binary version constraint
  - Changed from fixed version to flexible `>=2.9.9`
  - Resolves installation failures on newer Python/pip versions

---

## [0.6.1] - 2025-12-04

### Fixed

- Minor bug fixes and stability improvements

---

## [0.6.0] - 2025-12-03

### Added

- **Setup Command**: New `fastpy setup` for project initialization
  - Interactive database selection (PostgreSQL, MySQL, SQLite)
  - Automatic `.env` file generation
  - Secret key generation
  - Virtual environment creation
  - Dependencies installation
  - Database migration execution

- **Setup Sub-commands**:
  - `fastpy setup:env` - Generate `.env` file only
  - `fastpy setup:db` - Run database migrations only
  - `fastpy setup:secret` - Generate new secret key

### Changed

- Improved `fastpy new` to optionally run setup after cloning
- Enhanced project detection for better CLI proxying

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

[Unreleased]: https://github.com/vutia-ent/fastpy-cli/compare/v1.1.1...HEAD
[1.1.1]: https://github.com/vutia-ent/fastpy-cli/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/vutia-ent/fastpy-cli/compare/v0.6.7...v1.1.0
[0.6.7]: https://github.com/vutia-ent/fastpy-cli/compare/v0.6.6...v0.6.7
[0.6.6]: https://github.com/vutia-ent/fastpy-cli/compare/v0.6.5...v0.6.6
[0.6.5]: https://github.com/vutia-ent/fastpy-cli/compare/v0.6.4...v0.6.5
[0.6.4]: https://github.com/vutia-ent/fastpy-cli/compare/v0.6.3...v0.6.4
[0.6.3]: https://github.com/vutia-ent/fastpy-cli/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/vutia-ent/fastpy-cli/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/vutia-ent/fastpy-cli/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/vutia-ent/fastpy-cli/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/vutia-ent/fastpy-cli/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/vutia-ent/fastpy-cli/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/vutia-ent/fastpy-cli/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/vutia-ent/fastpy-cli/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/vutia-ent/fastpy-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/vutia-ent/fastpy-cli/releases/tag/v0.1.0
