"""
Main shell implementation for awesh
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional

try:
    from .config import Config
    from .router import CommandRouter
    from .bash_executor import BashExecutor
    from .ai_client import AweshAIClient
except ImportError:
    from config import Config
    from router import CommandRouter
    from bash_executor import BashExecutor
    from ai_client import AweshAIClient


class AweshShell:
    """Main awesh shell implementation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.router = CommandRouter()
        self.current_dir = Path.cwd()
        self.running = True
        self.bash_executor = BashExecutor(str(self.current_dir))
        self.last_exit_code = 0
        self.ai_client = AweshAIClient(config)
        self.last_command = None
        
    async def run(self):
        """Main shell loop"""
        print(f"awesh v0.1.0 - AI-aware Interactive Shell")
        print(f"Philosophy: 'AI by default, Bash when I mean Bash'")
        print(f"Model: {self.config.model}")
        print(f"Type 'exit' to quit, or use Ctrl+C")
        print()
        
        # Initialize AI client
        try:
            await self.ai_client.initialize()
            print("✅ AI client initialized successfully")
        except Exception as e:
            print(f"⚠️  Warning: AI client initialization failed: {e}")
            print("   AI features will be disabled. Check your OPENAI_API_KEY in ~/.aweshrc")
        
        print()
        
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
                    self.last_command = cleaned_line
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
                        self.bash_executor.set_cwd(str(self.current_dir))
                    else:
                        print(f"awesh: cd: {new_dir}: No such file or directory", file=sys.stderr)
                except PermissionError:
                    print(f"awesh: cd: {new_dir}: Permission denied", file=sys.stderr)
                
    async def _handle_bash_command(self, command: str):
        """Handle bash command execution"""
        exit_code, stdout, stderr = await self.bash_executor.execute(command)
        
        if stdout:
            print(stdout, end='')
        if stderr:
            print(stderr, end='', file=sys.stderr)
            
        # Store exit code for potential use (like $? in bash)
        self.last_exit_code = exit_code
        
    async def _handle_ai_prompt(self, prompt: str):
        """Handle AI prompt processing"""
        if not self.ai_client.client:
            print("❌ AI client not available. Check your OPENAI_API_KEY configuration.")
            return
            
        try:
            # Prepare context for AI
            context = {
                'current_directory': str(self.current_dir),
                'last_exit_code': self.last_exit_code
            }
            
            if self.last_command:
                context['last_command'] = self.last_command
            
            # Process prompt and stream response
            print("🤖 ", end="", flush=True)
            
            response_chunks = []
            async for chunk in self.ai_client.process_prompt(prompt, context):
                print(chunk, end="", flush=True)
                response_chunks.append(chunk)
            
            print()  # New line after response
            
        except KeyboardInterrupt:
            print("\n⏹️  AI response interrupted")
        except Exception as e:
            print(f"\n❌ Error processing AI prompt: {e}")
            
    async def cleanup(self):
        """Clean up resources"""
        if self.ai_client:
            await self.ai_client.close()
