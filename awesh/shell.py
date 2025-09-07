"""
Main shell implementation for awesh
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional

from .config import Config
from .router import CommandRouter


class AweshShell:
    """Main awesh shell implementation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.router = CommandRouter()
        self.current_dir = Path.cwd()
        self.running = True
        
    async def run(self):
        """Main shell loop"""
        print(f"awesh v0.1.0 - AI-aware Interactive Shell")
        print(f"Philosophy: 'AI by default, Bash when I mean Bash'")
        print(f"Type 'exit' to quit, or use Ctrl+C")
        print()
        
        # TODO: Load history, initialize AI client, start MCP server
        
        while self.running:
            try:
                # Get user input
                line = input(self.config.prompt_label)
                
                if not line.strip():
                    continue
                    
                # Route the command
                destination, cleaned_line = self.router.route_command(line)
                
                if destination == 'bash':
                    if self.router.is_builtin_command(cleaned_line):
                        await self._handle_builtin(cleaned_line)
                    else:
                        await self._handle_bash_command(cleaned_line)
                else:  # destination == 'ai'
                    await self._handle_ai_prompt(cleaned_line)
                    
            except KeyboardInterrupt:
                print()  # New line after ^C
                continue
            except EOFError:
                print("\nGoodbye!")
                break
                
    async def _handle_builtin(self, command: str):
        """Handle awesh builtin commands"""
        tokens = command.strip().split()
        cmd = tokens[0]
        
        if cmd == 'exit':
            self.running = False
            print("Goodbye!")
            
        elif cmd == 'pwd':
            print(self.current_dir)
            
        elif cmd == 'cd':
            if len(tokens) == 1:
                # cd with no args goes to home
                new_dir = Path.home()
            else:
                new_dir = Path(tokens[1]).expanduser()
                
            try:
                if new_dir.is_dir():
                    self.current_dir = new_dir.resolve()
                    os.chdir(self.current_dir)
                else:
                    print(f"awesh: cd: {new_dir}: No such file or directory", file=sys.stderr)
            except PermissionError:
                print(f"awesh: cd: {new_dir}: Permission denied", file=sys.stderr)
                
    async def _handle_bash_command(self, command: str):
        """Handle bash command execution"""
        # TODO: Implement bash executor
        print(f"[BASH] Would execute: {command}")
        print("(Bash executor not yet implemented)")
        
    async def _handle_ai_prompt(self, prompt: str):
        """Handle AI prompt processing"""
        # TODO: Implement AI client
        print(f"[AI] Would process: {prompt}")
        print("(AI client not yet implemented)")
