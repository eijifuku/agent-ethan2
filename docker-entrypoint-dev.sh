#!/bin/bash
set -e

# Install package in editable mode if not already installed or if pyproject.toml changed
if [ ! -f /tmp/.agent_ethan2_installed ] || [ pyproject.toml -nt /tmp/.agent_ethan2_installed ]; then
    echo "Installing agent-ethan2 in editable mode..."
    pip install --user -e ".[dev]" 2>&1 | tail -20
    touch /tmp/.agent_ethan2_installed
else
    echo "agent-ethan2 already installed, skipping..."
fi

# Execute the command
exec "$@"

