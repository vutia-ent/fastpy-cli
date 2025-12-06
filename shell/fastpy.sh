#!/bin/bash
# Fastpy Shell Integration
# Enables auto-cd, auto-activate, and global venv activation
#
# Install with: fastpy shell:install
# Or manually: source /path/to/fastpy.sh

# Track the last activated venv to avoid re-activating
_FASTPY_LAST_VENV=""

# Check if current directory is a fastpy project
_fastpy_is_project() {
    [[ -f "cli.py" && -d "app" ]] || [[ -f "cli.py" && -f "main.py" ]]
}

# Auto-activate venv when entering a fastpy project
_fastpy_auto_activate() {
    if _fastpy_is_project && [[ -f "venv/bin/activate" ]]; then
        local venv_path="$(pwd)/venv"
        # Only activate if not already in this venv
        if [[ "$VIRTUAL_ENV" != "$venv_path" ]]; then
            source venv/bin/activate
            _FASTPY_LAST_VENV="$venv_path"
            echo -e "\033[1;32m✓ Fastpy venv activated\033[0m"
        fi
    elif [[ -n "$_FASTPY_LAST_VENV" && "$VIRTUAL_ENV" == "$_FASTPY_LAST_VENV" ]]; then
        # Left a fastpy project, deactivate
        deactivate 2>/dev/null
        _FASTPY_LAST_VENV=""
        echo -e "\033[33m○ Venv deactivated\033[0m"
    fi
}

# Override cd to auto-activate/deactivate
cd() {
    builtin cd "$@" && _fastpy_auto_activate
}

# Also check on shell startup (in case terminal opens in a project)
_fastpy_auto_activate

# Fastpy command wrapper
fastpy() {
    if [[ "$1" == "new" && -n "$2" ]]; then
        local project_name="" no_install=false
        for arg in "$@"; do
            [[ "$arg" == "--no-install" ]] && no_install=true
            [[ ! "$arg" =~ ^- && "$arg" != "new" && -z "$project_name" ]] && project_name="$arg"
        done
        command fastpy "$@"
        local rc=$?
        # Auto-cd and activate unless --no-install was used
        if [[ $rc -eq 0 && "$no_install" == false && -d "$project_name" ]]; then
            echo -e "\n\033[1;34mEntering project directory...\033[0m"
            cd "$project_name"
        fi
        return $rc
    elif [[ "$1" == "install" ]]; then
        command fastpy "$@"
        local rc=$?
        [[ $rc -eq 0 ]] && _fastpy_auto_activate
        return $rc
    else
        command fastpy "$@"
    fi
}

# Convenience aliases
alias fp='fastpy'
alias fps='fastpy serve'
alias fpi='fastpy install'
alias fpn='fastpy new'
