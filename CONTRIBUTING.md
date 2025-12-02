# Contributing to Fastpy CLI

Thank you for your interest in contributing to Fastpy CLI! This guide will help you get started.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Adding Features](#adding-features)
- [Security Guidelines](#security-guidelines)
- [Documentation](#documentation)
- [Release Process](#release-process)

---

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone. We expect all contributors to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community

---

## Getting Started

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.9+ |
| Git | 2.x |
| pip/pipx | Latest |

### Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/fastpy-cli.git
cd fastpy-cli

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dev dependencies
pip install -e ".[dev]"

# 4. Verify setup
pytest
```

---

## Development Workflow

### Branch Naming

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feature/` | New features | `feature/add-redis-cache` |
| `fix/` | Bug fixes | `fix/path-traversal` |
| `docs/` | Documentation | `docs/update-readme` |
| `refactor/` | Code refactoring | `refactor/http-client` |
| `security/` | Security fixes | `security/ssrf-protection` |

### Making Changes

```bash
# 1. Create branch
git checkout -b feature/your-feature

# 2. Make changes and test
pytest

# 3. Lint and format
ruff check fastpy_cli/
black fastpy_cli/
mypy fastpy_cli/

# 4. Commit (see commit conventions below)
git commit -m "feat: add your feature"

# 5. Push and create PR
git push origin feature/your-feature
```

### Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

| Type | Description |
|------|-------------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `style:` | Formatting (no code change) |
| `refactor:` | Code refactoring |
| `test:` | Adding tests |
| `chore:` | Maintenance |
| `security:` | Security fix |

**Examples:**
```
feat: add Redis cache driver
fix: prevent path traversal in storage
docs: update README with new libs
security: add SSRF protection to HTTP client
```

---

## Code Style

### Python Guidelines

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all functions
- Maximum line length: 100 characters
- Use docstrings (Google style)

### Example

```python
def create_resource(
    name: str,
    fields: list[str],
    *,
    protected: bool = False,
) -> dict[str, Any]:
    """Create a new resource with the specified fields.

    Args:
        name: The name of the resource.
        fields: List of field definitions.
        protected: Whether to protect the routes.

    Returns:
        Dictionary containing the created resource details.

    Raises:
        ValueError: If name is empty or invalid.
    """
    if not name:
        raise ValueError("Resource name cannot be empty")

    return {"name": name, "fields": fields}
```

### Tools

| Tool | Purpose | Command |
|------|---------|---------|
| Black | Formatting | `black fastpy_cli/` |
| Ruff | Linting | `ruff check fastpy_cli/` |
| mypy | Type checking | `mypy fastpy_cli/` |
| pytest | Testing | `pytest` |

---

## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=fastpy_cli --cov-report=html

# Specific file
pytest tests/test_main.py

# Specific test
pytest tests/test_main.py::test_version_command

# Verbose
pytest -v
```

### Writing Tests

- Place tests in `tests/` directory
- Name files `test_*.py`
- Name functions `test_*`
- Use fixtures from `conftest.py`
- Target >80% code coverage

```python
class TestStorageDriver:
    """Tests for storage driver."""

    def test_blocks_path_traversal(self, temp_dir: Path) -> None:
        """Test that path traversal is blocked."""
        driver = LocalDriver(str(temp_dir))

        with pytest.raises(ValueError, match="Path traversal"):
            driver.get("../../../etc/passwd")

    def test_stores_and_retrieves_file(self, temp_dir: Path) -> None:
        """Test basic file operations."""
        driver = LocalDriver(str(temp_dir))
        driver.put("test.txt", b"hello")

        assert driver.get("test.txt") == b"hello"
```

---

## Adding Features

### New CLI Command

```python
# In main.py
@app.command()
def my_command(
    name: str = typer.Argument(..., help="Resource name"),
    force: bool = typer.Option(False, "--force", "-f", help="Force operation"),
) -> None:
    """Short description for help text."""
    console.print(f"Creating {name}...")
```

### New Lib Facade

1. Create directory structure:
   ```
   fastpy_cli/libs/mylib/
   ├── __init__.py      # Exports
   ├── facade.py        # Static facade class
   ├── manager.py       # Service manager
   └── drivers.py       # Driver implementations
   ```

2. Implement the facade:
   ```python
   # facade.py
   from ..facade import Facade

   class MyLib(Facade):
       @classmethod
       def get_facade_accessor(cls) -> str:
           return "mylib"
   ```

3. Register in container (`__init__.py` of libs)

4. Add to `AVAILABLE_LIBS` in `main.py`

5. Update README and docs

### New AI Provider

```python
# In ai.py
class NewProvider(AIProvider):
    """New AI provider implementation."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str) -> Optional[str]:
        # Implementation
        pass
```

---

## Security Guidelines

When contributing, please follow these security practices:

### Do

- Validate all user input
- Use parameterized queries
- Sanitize file paths with `.resolve()` and `relative_to()`
- Block private IPs in HTTP requests
- Use `secrets` module for random values
- Add type hints and validation

### Don't

- Use `pickle.loads()` on untrusted data
- Use `shell=True` in subprocess calls
- Trust user-provided file paths directly
- Disable SSL verification in production
- Hardcode secrets or API keys
- Use weak hashing (MD5, SHA1 for passwords)

### Security Checklist

Before submitting a PR:

- [ ] No hardcoded credentials
- [ ] Input validation on all user data
- [ ] Path traversal protection for file operations
- [ ] SSRF protection for HTTP requests
- [ ] Safe serialization (prefer JSON over pickle)
- [ ] Dependencies checked for vulnerabilities

---

## Documentation

### When to Update Docs

- `README.md` - User-facing changes
- `CHANGELOG.md` - All notable changes
- `SECURITY.md` - Security-related updates
- Docstrings - API changes

### Changelog Format

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New feature description

### Changed
- Modified behavior description

### Fixed
- Bug fix description

### Security
- Security fix description
```

---

## Release Process

Releases are automated via GitHub Actions:

```bash
# 1. Update version
# Edit: fastpy_cli/__init__.py
# Edit: pyproject.toml

# 2. Update CHANGELOG.md

# 3. Create PR and merge

# 4. Tag release
git tag v0.5.0
git push origin v0.5.0
```

GitHub Actions will:
1. Run tests
2. Build package
3. Publish to PyPI
4. Create GitHub release

---

## Getting Help

- **Bug Reports**: [Open an issue](https://github.com/vutia-ent/fastpy-cli/issues)
- **Questions**: [Start a discussion](https://github.com/vutia-ent/fastpy-cli/discussions)
- **Security Issues**: Email security@ve.ke (do not open public issues)

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

<p align="center">
  Thank you for contributing!
</p>
