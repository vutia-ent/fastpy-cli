#!/bin/bash
# Fastpy Shell Integration
# Source this file in your .zshrc or .bashrc:
#   source /path/to/fastpy.sh
# Or install with:
#   fastpy shell:install

# Main fastpy wrapper function
fastpy() {
    # Check if this is a 'new' command with a project name
    if [[ "$1" == "new" && -n "$2" ]]; then
        local project_name=""
        local no_install=false
        local args=("$@")

        # Parse arguments to find project name and --no-install flag
        for ((i=1; i<${#args[@]}; i++)); do
            arg="${args[$i]}"
            if [[ "$arg" == "--no-install" ]]; then
                no_install=true
            elif [[ ! "$arg" =~ ^- && -z "$project_name" ]]; then
                project_name="$arg"
            fi
        done

        # Run the actual fastpy command
        command fastpy "$@"
        local exit_code=$?

        # Auto-cd and activate unless --no-install was used
        if [[ $exit_code -eq 0 && "$no_install" == false && -n "$project_name" ]]; then
            if [[ -d "$project_name" ]]; then
                echo ""
                echo -e "\033[1;34mEntering project directory...\033[0m"
                cd "$project_name" || return 1

                # Activate virtual environment if it exists
                if [[ -f "venv/bin/activate" ]]; then
                    echo -e "\033[1;34mActivating virtual environment...\033[0m"
                    source venv/bin/activate
                    echo -e "\033[1;32m✓ Ready to develop!\033[0m"
                    echo ""
                    echo -e "Start the server with: \033[36mfastpy serve\033[0m"
                elif [[ -f "venv/Scripts/activate" ]]; then
                    # Windows Git Bash
                    echo -e "\033[1;34mActivating virtual environment...\033[0m"
                    source venv/Scripts/activate
                    echo -e "\033[1;32m✓ Ready to develop!\033[0m"
                    echo ""
                    echo -e "Start the server with: \033[36mfastpy serve\033[0m"
                fi
            fi
        fi

        return $exit_code

    # Check if this is 'install' command (activate venv after)
    elif [[ "$1" == "install" ]]; then
        command fastpy "$@"
        local exit_code=$?

        # Activate venv after successful install
        if [[ $exit_code -eq 0 ]]; then
            if [[ -f "venv/bin/activate" ]]; then
                echo ""
                echo -e "\033[1;34mActivating virtual environment...\033[0m"
                source venv/bin/activate
                echo -e "\033[1;32m✓ Virtual environment activated!\033[0m"
            elif [[ -f "venv/Scripts/activate" ]]; then
                echo ""
                echo -e "\033[1;34mActivating virtual environment...\033[0m"
                source venv/Scripts/activate
                echo -e "\033[1;32m✓ Virtual environment activated!\033[0m"
            fi
        fi

        return $exit_code
    else
        # All other commands - just pass through
        command fastpy "$@"
    fi
}

# Convenience aliases
alias fp='fastpy'
alias fps='fastpy serve'
alias fpi='fastpy install'
alias fpn='fastpy new'

# Print success message when sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    echo "Fastpy shell integration loaded. Use 'fastpy' with auto-cd and auto-activate."
fi
