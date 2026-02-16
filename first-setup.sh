#!/bin/bash
set -e

# Check if being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "This script must be sourced to update your current shell."
    echo "Run: source first-setup.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$SCRIPT_DIR/bin"

echo "Setting up pi-bridge CLI..."

# Make bin scripts executable
chmod +x "$BIN_DIR/pi-bridge"

# Detect shell config file
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.bashrc"
fi

# Check if already added
if grep -q "pi-bridge" "$SHELL_RC" 2>/dev/null; then
    echo "pi-bridge already in PATH ($SHELL_RC)"
else
    echo "" >> "$SHELL_RC"
    echo "# Pi Bridge CLI" >> "$SHELL_RC"
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
    echo "Added pi-bridge to PATH in $SHELL_RC"
fi

# Source the updated config to apply PATH now
source "$SHELL_RC"

echo ""
echo "pi-bridge is now available."
echo ""
echo "Usage:"
echo "  pi-bridge setup              # interactive setup"
echo "  pi-bridge setup --use-defaults   # use all defaults"
