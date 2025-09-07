#!/bin/bash
# Installation script for awesh

set -e

echo "🚀 Installing awesh - AI-aware Interactive Shell (Clean Install)"
echo "================================================================"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Installing from: $SCRIPT_DIR"

# Clean install - remove any existing installations first
echo "🧹 Performing clean install..."
echo "   - Removing existing Python package..."
pip uninstall -y awesh-backend 2>/dev/null || true
pip uninstall -y awesh 2>/dev/null || true

echo "   - Cleaning build artifacts..."
cd "$SCRIPT_DIR"
make clean 2>/dev/null || true
rm -rf build/ dist/ *.egg-info/ __pycache__/ 2>/dev/null || true

echo "   - Removing existing binary..."
rm -f ~/.local/bin/awesh 2>/dev/null || true

# Build C frontend
echo "🔨 Building C frontend..."
make awesh

# Install in development mode
echo "📦 Installing Python backend package..."
pip install -e "$SCRIPT_DIR"

# Copy binary to user's local bin
echo "📋 Installing binary to ~/.local/bin..."
mkdir -p ~/.local/bin
cp awesh ~/.local/bin/
chmod +x ~/.local/bin/awesh

echo ""
echo "🎉 Clean installation complete!"
echo ""
echo "Usage:"
echo "  awesh                    # Start interactive shell"
echo "  awesh --help            # Show help"
echo "  awesh --config ~/.myrc  # Use custom config"
echo ""
echo "Configuration will be created at ~/.aweshrc on first run."
