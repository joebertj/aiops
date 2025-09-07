#!/usr/bin/env python3
"""
Interactive demonstration of awesh bash command functionality
"""

import asyncio
import sys
from pathlib import Path

# Add awesh to path
sys.path.insert(0, str(Path(__file__).parent / "awesh"))

from awesh.config import Config
from awesh.shell import AweshShell


async def simulate_awesh_session():
    """Simulate an interactive awesh session with bash commands"""
    
    print("🚀 awesh v0.1.0 - AI-aware Interactive Shell")
    print("Philosophy: 'AI by default, Bash when I mean Bash'")
    print("Type 'exit' to quit, or use Ctrl+C")
    print()
    print("🎯 Demo: Running bash commands in awesh")
    print("=" * 50)
    
    # Create awesh shell
    config = Config()
    shell = AweshShell(config)
    
    # Demo commands to run
    demo_commands = [
        "pwd",
        "ls -la",
        "echo 'Hello from awesh!'",
        "whoami", 
        "python --version",
        "git status",
        "cd /tmp",
        "pwd",
        "ls -la /home/joebert/AI/aiops | head -3",
        "echo 'This is working perfectly!'"
    ]
    
    for cmd in demo_commands:
        print(f"\n{config.prompt_label}{cmd}")
        
        # Route the command (should all go to bash)
        destination, cleaned_cmd = shell.router.route_command(cmd)
        print(f"[Routing: {destination.upper()}]")
        
        if destination == 'bash':
            if shell.router.is_builtin_command(cleaned_cmd):
                await shell._handle_builtin(cleaned_cmd)
            else:
                await shell._handle_bash_command(cleaned_cmd)
        else:
            await shell._handle_ai_prompt(cleaned_cmd)
        
        # Small delay for readability
        await asyncio.sleep(0.5)
    
    print(f"\n{config.prompt_label}exit")
    print("Goodbye!")
    print()
    print("✅ awesh bash integration working perfectly!")
    print("   You can now run 'awesh' for full interactive mode.")


if __name__ == "__main__":
    asyncio.run(simulate_awesh_session())
