"""
Main shell implementation for awesh
"""

import os
import sys
import asyncio
import threading
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
    """Frontend: Just shows messages, waits for input, shows output"""
    
    def __init__(self, config: Config):
        self.config = config
        self.current_dir = Path.cwd()
        self.running = True
        self.last_exit_code = 0
        self.last_command = None
        
        # Backend status - starts as down
        self.backend_ready = False
        
        # Start backend in parallel - don't wait for it
        self.backend = AweshBackend(config)
        threading.Thread(target=self._start_backend, daemon=True).start()
        
    def run(self):
        """Frontend: Show messages, wait for input, show output"""
        # Show MOTD immediately
        print(f"awesh v0.1.0 - Awe-Inspired Workspace Environment Shell (AI-aware Interactive Shell)")
        print(f"Model: {self.config.model}")
        print()
        
        # Simple frontend loop - instant
        while self.running:
            try:
                # Show prompt immediately
                print(self.config.prompt_label, end='', flush=True)
                line = input()
                
                if not line.strip():
                    continue
                
                # Process command - frontend logic only
                self._handle_command(line)
                    
            except KeyboardInterrupt:
                print()
                continue
            except EOFError:
                break
        
        print("Goodbye!")
    
    def _start_backend(self):
        """Start backend in parallel"""
        self.backend.start()
        self.backend_ready = True
        print("✅ AI backend ready!")
    
    def _handle_command(self, line: str):
        """Frontend command handling - instant decisions"""
        # Handle builtins immediately (frontend)
        if self._is_builtin(line):
            self._handle_builtin(line)
            return
        
        # Backend down? Redirect everything to bash
        if not self.backend_ready:
            self._execute_bash_direct(line)
            return
        
        # Backend up? Send to backend with rules
        self.backend.process_command(line)
    
    def _is_builtin(self, line: str) -> bool:
        """Quick builtin check"""
        return line.strip().split()[0] in ['cd', 'pwd', 'exit'] if line.strip() else False
                
    def _handle_builtin(self, command: str):
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
    
    def _execute_bash_direct(self, line: str):
        """Execute bash directly (frontend fallback)"""
        import subprocess
        try:
            result = subprocess.run(
                line, shell=True, capture_output=True, text=True,
                cwd=str(self.current_dir), timeout=30
            )
            if result.stdout:
                print(result.stdout, end='')
            if result.stderr:
                print(result.stderr, end='', file=sys.stderr)
            self.last_exit_code = result.returncode
            self.last_command = line
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
    
    def _looks_obviously_like_bash(self, line: str) -> bool:
        """Ultra-fast bash detection - only obvious cases"""
        # Check for obvious bash syntax first
        if any(char in line for char in '|><;&$`'):
            return True
        
        # Check first word against common commands
        first_word = line.strip().split()[0].lower() if line.strip() else ""
        common_commands = {'ls', 'cat', 'grep', 'find', 'cd', 'pwd', 'mkdir', 'rm', 'cp', 'mv', 'chmod', 'chown'}
        if first_word in common_commands:
            return True
            
        # If starts with ./ or has sudo/time prefix
        if first_word.startswith('./') or first_word in {'sudo', 'time', 'nice'}:
            return True
            
        # Default to AI for anything unclear
        return False
    
    def _execute_bash_fast(self, line: str):
        """Execute bash command immediately"""
        exit_code, stdout, stderr = asyncio.run(self.bash_executor.execute(line))
        
        if stdout:
            print(stdout, end='')
        if stderr:
            print(stderr, end='', file=sys.stderr)
            
        self.last_exit_code = exit_code
        self.last_command = line
                
    def _handle_bash_command(self, command: str):
        """Handle bash command execution - make it synchronous for speed"""
        # Use synchronous execution to avoid asyncio overhead
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(self.current_dir),
                timeout=30
            )
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr
        except subprocess.TimeoutExpired:
            exit_code = 124
            stdout = ""
            stderr = "Command timed out\n"
        except Exception as e:
            exit_code = 1
            stdout = ""
            stderr = f"Error: {e}\n"
        
        if stdout:
            print(stdout, end='')
        if stderr:
            print(stderr, end='', file=sys.stderr)
            
        self.last_exit_code = exit_code
        self.last_command = command
        
    def _handle_ai_prompt(self, prompt: str):
        """Handle AI prompt processing"""
        if not self.ai_ready:
            print("🔄 AI client still initializing... Please wait a moment and try again.")
            return
            
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
            
            # Process prompt and stream response (run in new event loop)
            print("🤖 ", end="", flush=True)
            
            async def process_ai():
                response_chunks = []
                async for chunk in self.ai_client.process_prompt(prompt, context):
                    print(chunk, end="", flush=True)
                    response_chunks.append(chunk)
                print()  # New line after response
            
            asyncio.run(process_ai())
            
        except KeyboardInterrupt:
            print("\n⏹️  AI response interrupted")
        except Exception as e:
            print(f"\n❌ Error processing AI prompt: {e}")
    
    def _smart_route_command(self, line: str):
        """Smart routing: try bash first, then AI validation if available"""
        # Always try bash execution first (capture output silently)
        exit_code, stdout, stderr = asyncio.run(self.bash_executor.execute(line))
        
        if not self.ai_ready:
            # AI not loaded yet - show bash results regardless
            if stdout:
                print(stdout, end='')
            if stderr:
                print(stderr, end='', file=sys.stderr)
            self.last_exit_code = exit_code
            self.last_command = line
            return
        
        # AI is available - ask it to validate if this was a real bash command
        if exit_code == 0 or self._looks_like_bash_command(line):
            # Command succeeded or looks like bash - show bash output
            if stdout:
                print(stdout, end='')
            if stderr:
                print(stderr, end='', file=sys.stderr)
            self.last_exit_code = exit_code
            self.last_command = line
        else:
            # Command failed and might be a natural language prompt
            # Use simple heuristics first for speed
            if self._quick_bash_check(line):
                # Looks like a bash command that just failed
                if stdout:
                    print(stdout, end='')
                if stderr:
                    print(stderr, end='', file=sys.stderr)
                self.last_exit_code = exit_code
                self.last_command = line
            else:
                # Looks like natural language - treat as prompt
                self._handle_ai_prompt(line)
    
    def _looks_like_bash_command(self, line: str) -> bool:
        """Quick heuristic to check if line looks like a bash command"""
        # If it has obvious bash syntax, it's probably bash
        bash_indicators = ['|', '>', '>>', '<', '&&', '||', ';', '$', '`']
        return any(indicator in line for indicator in bash_indicators)
    
    def _quick_bash_check(self, line: str) -> bool:
        """Fast heuristic check if line looks like a bash command"""
        line = line.strip().lower()
        
        # If it has obvious bash syntax, it's probably bash
        if self._looks_like_bash_command(line):
            return True
            
        # Check for common command patterns
        words = line.split()
        if not words:
            return False
            
        first_word = words[0]
        
        # Common command patterns that might not be in PATH but are bash-like
        bash_patterns = [
            # Commands that commonly fail
            'lss', 'lsl', 'sl',  # common typos of ls
            'cta', 'catl',       # common typos of cat  
            'grpe', 'gerp',      # common typos of grep
            'mkdri', 'mdkir',    # common typos of mkdir
            'chmdo', 'chomd',    # common typos of chmod
        ]
        
        # If it's a common typo, treat as bash
        if first_word in bash_patterns:
            return True
            
        # If it starts with typical bash prefixes
        bash_prefixes = ['sudo', 'time', 'nice', 'nohup', './']
        if any(first_word.startswith(prefix) for prefix in bash_prefixes):
            return True
            
        # If it looks like a question or natural language
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'should', 'would', 'could']
        if first_word in question_words:
            return False
            
        # If it has multiple words and looks conversational
        if len(words) > 3 and any(word in ['the', 'this', 'that', 'these', 'those', 'a', 'an'] for word in words):
            return False
            
        # Default: if it's a single word or short phrase, assume it's a bash command attempt
        return len(words) <= 2
            
    def _load_ai_libraries_background(self):
        """Load heavy AI libraries in background after prompt is shown"""
        try:
            # Import heavy libraries only when needed
            global openai, AsyncOpenAI
            import openai
            from openai import AsyncOpenAI
            
            # Now initialize the AI client
            asyncio.run(self.ai_client.initialize())
            self.ai_ready = True
            print("✅ AI client ready!")
        except Exception as e:
            print(f"⚠️  AI client failed to load: {e}")
            print("AI features disabled. Check OPENAI_API_KEY in ~/.aweshrc")
            
    async def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'backend'):
            await self.backend.cleanup()


class AweshBackend:
    """Backend: Loads AI libraries and handles smart routing"""
    
    def __init__(self, config: Config):
        self.config = config
        self.router = CommandRouter()
        self.bash_executor = BashExecutor(".")
        self.ai_client = None
        self.ai_ready = False
    
    def start(self):
        """Start backend - load heavy libraries"""
        try:
            # Load heavy AI libraries
            global openai, AsyncOpenAI
            import openai
            from openai import AsyncOpenAI
            
            # Initialize AI client
            self.ai_client = AweshAIClient(self.config)
            asyncio.run(self.ai_client.initialize())
            self.ai_ready = True
        except Exception as e:
            print(f"⚠️  Backend AI failed: {e}")
    
    def process_command(self, line: str):
        """Backend command processing with smart routing"""
        # Follow the rules: try bash first, then AI validation
        threading.Thread(target=self._smart_route, args=(line,), daemon=True).start()
    
    def _smart_route(self, line: str):
        """Smart routing: bash first, then AI if available"""
        # Always try bash first (silently)
        exit_code, stdout, stderr = asyncio.run(self.bash_executor.execute(line))
        
        # If bash succeeded or AI not ready, show bash output
        if exit_code == 0 or not self.ai_ready:
            if stdout:
                print(stdout, end='')
            if stderr:
                print(stderr, end='', file=sys.stderr)
            return
        
        # Bash failed and AI ready - use simple heuristics
        if self._looks_like_bash_command(line):
            # Show bash error
            if stdout:
                print(stdout, end='')
            if stderr:
                print(stderr, end='', file=sys.stderr)
        else:
            # Treat as AI prompt
            self._handle_ai_prompt(line)
    
    def _looks_like_bash_command(self, line: str) -> bool:
        """Quick bash detection"""
        return any(char in line for char in '|><;&$`') or \
               line.strip().split()[0].lower() in {'ls', 'cat', 'grep', 'find', 'mkdir', 'rm'}
    
    def _handle_ai_prompt(self, prompt: str):
        """Handle AI prompt"""
        if not self.ai_ready:
            print("🔄 AI still loading...")
            return
        
        try:
            print("🤖 ", end="", flush=True)
            async def process():
                async for chunk in self.ai_client.process_prompt(prompt):
                    print(chunk, end="", flush=True)
                print()
            asyncio.run(process())
        except Exception as e:
            print(f"\n❌ AI error: {e}")
    
    async def cleanup(self):
        """Cleanup backend"""
        if self.ai_client:
            await self.ai_client.close()
