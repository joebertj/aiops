#!/bin/bash
set -e

# awesh Installation Script
# Installs awesh - AI-aware interactive shell

echo "🚀 Installing awesh - AI-aware Interactive Shell"
echo "=================================================="

# Check if we're on a supported system
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Currently only Linux is supported"
    exit 1
fi

# Check for required system dependencies
echo "📋 Checking dependencies..."

# Check for gcc
if ! command -v gcc &> /dev/null; then
    echo "❌ gcc is required but not installed"
    echo "   Ubuntu/Debian: sudo apt install build-essential"
    echo "   CentOS/RHEL: sudo yum groupinstall 'Development Tools'"
    exit 1
fi

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 is required but not installed"
    echo "   Ubuntu/Debian: sudo apt install python3"
    echo "   CentOS/RHEL: sudo yum install python3"
    exit 1
fi

# Check for pip
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed"
    echo "   Ubuntu/Debian: sudo apt install python3-pip"
    echo "   CentOS/RHEL: sudo yum install python3-pip"
    exit 1
fi

# Check for readline development headers
if ! pkg-config --exists readline 2>/dev/null; then
    echo "❌ readline development headers required but not found"
    echo "   Ubuntu/Debian: sudo apt install libreadline-dev"
    echo "   CentOS/RHEL: sudo yum install readline-devel"
    exit 1
fi

echo "✅ All dependencies satisfied"

# Create installation directory
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

# Add ~/.local/bin to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "📝 Adding ~/.local/bin to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "   Please run: source ~/.bashrc (or restart your terminal)"
fi

echo "🔨 Building C frontend..."
cd awesh
make clean && make

echo "📦 Installing Python backend..."
cd ..
pip3 install --user -e .

echo "📋 Installing awesh binary..."
cp awesh/awesh "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/awesh"

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Quick Start:"
echo "   1. Restart your terminal (or run: source ~/.bashrc)"
echo "   2. Add your OpenAI API key to ~/.aweshrc:"
echo "      echo 'OPENAI_API_KEY=your_key_here' >> ~/.aweshrc"
echo "   3. Run: awesh"
echo ""
echo "📚 Documentation: https://github.com/joebertj/aiops"
echo "🐛 Issues: https://github.com/joebertj/aiops/issues"
