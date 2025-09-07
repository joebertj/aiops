#!/bin/bash
# Installation script for awesh

set -e

echo "🚀 Installing awesh - AI-aware Interactive Shell"
echo "================================================"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Installing from: $SCRIPT_DIR"

# Install in development mode
echo "📦 Installing awesh package..."
pip install -e "$SCRIPT_DIR"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Usage:"
echo "  awesh                    # Start interactive shell"
echo "  awesh --help            # Show help"
echo "  awesh --config ~/.myrc  # Use custom config"
echo ""
echo "Configuration will be created at ~/.aweshrc on first run."
