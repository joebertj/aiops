#!/usr/bin/env python3
"""
Test script to demonstrate awesh functionality
"""

import asyncio
import sys
from pathlib import Path

# Add awesh to path
sys.path.insert(0, str(Path(__file__).parent / "awesh"))

from awesh.config import Config
from awesh.shell import AweshShell
from awesh.router import CommandRouter


async def test_routing():
    """Test the command routing logic"""
    print("🧪 Testing awesh command routing...")
    print("=" * 50)
    
    router = CommandRouter()
    
    test_commands = [
        "ls -la",
        "pwd", 
        "cat /etc/hostname",
        "ps aux | grep python",
        "echo 'hello world'",
        "summarize this directory",
        "what files are in this folder?",
        "why is this command failing?",
        "git status",
        "python --version"
    ]
    
    for cmd in test_commands:
        destination, cleaned = router.route_command(cmd)
        print(f"'{cmd}' -> {destination.upper()}")
    
    print()


async def test_bash_execution():
    """Test bash command execution"""
    print("🐚 Testing bash command execution...")
    print("=" * 50)
    
    config = Config()
    shell = AweshShell(config)
    
    bash_commands = [
        "echo 'Hello from awesh!'",
        "pwd",
        "ls -la | head -5",
        "python --version",
        "whoami"
    ]
    
    for cmd in bash_commands:
        print(f"\n$ {cmd}")
        await shell._handle_bash_command(cmd)
    
    print()


async def main():
    """Run tests"""
    print("🚀 awesh - AI-aware Interactive Shell Tests")
    print("=" * 60)
    print()
    
    await test_routing()
    await test_bash_execution()
    
    print("✅ Tests completed! You can now run 'awesh' interactively.")


if __name__ == "__main__":
    asyncio.run(main())
