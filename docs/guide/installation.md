# Installation

## Requirements

- Python 3.9 or higher
- Git (for cloning templates)

## Install Methods

### pip (Recommended)

```bash
pip install fastpy-cli
```

### pipx (Isolated Environment)

```bash
pipx install fastpy-cli
```

### Homebrew (macOS)

```bash
brew tap vutia-ent/tap
brew install fastpy
```

## Verify Installation

```bash
fastpy version
```

## Troubleshooting

### pip Not Found

If you get `pip: command not found`, use `pip3`:

```bash
pip3 install fastpy-cli
```

To create a `pip` alias:

::: code-group
```bash [macOS/Linux]
echo 'alias pip=pip3' >> ~/.zshrc
source ~/.zshrc
```

```powershell [Windows]
# Python 3.x usually includes both pip and pip3
# Reinstall Python and check "Add to PATH"
```
:::

### fastpy Command Not Found

The Python scripts directory isn't in your PATH.

::: code-group
```bash [macOS]
echo 'export PATH="'$(python3 -m site --user-base)/bin':$PATH"' >> ~/.zshrc
source ~/.zshrc
```

```bash [Linux]
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

```powershell [Windows]
# Find your scripts path
python -m site --user-site
# Add the Scripts folder to PATH via System Properties
```
:::

**Alternative:** Use pipx (automatically handles PATH):
```bash
pipx install fastpy-cli
```

## Upgrading

```bash
fastpy upgrade
# or
pip install --upgrade fastpy-cli
```

## Shell Completions

Enable tab completions for your shell:

```bash
fastpy --install-completion bash   # Bash
fastpy --install-completion zsh    # Zsh
fastpy --install-completion fish   # Fish
fastpy --install-completion powershell  # PowerShell
```
