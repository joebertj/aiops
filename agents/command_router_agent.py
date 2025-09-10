"""
Command Router Agent for AIOps System

This agent routes commands between Bash execution and AI processing based on
command detection rules. It's the final agent in the chain that determines
whether a prompt should be executed as a shell command or sent to AI.
"""

import re
import shutil
import subprocess
from typing import Dict, Any, Set, Tuple, Optional
from .base_agent import BaseAgent, AgentResult


class CommandRouterAgent(BaseAgent):
    """
    Command Router Agent that decides between Bash and AI execution.
    
    This agent:
    1. Detects shell commands vs natural language prompts
    2. Routes shell commands to Bash execution
    3. Routes natural language to AI processing
    4. Handles built-in commands (cd, pwd, exit)
    """
    
    def __init__(self):
        super().__init__("Command Router Agent", priority=100)  # Lowest priority - runs last
        
        # Get bash commands and builtins
        self.bash_commands = self._get_bash_commands()
        
        # Shell syntax patterns that indicate Bash execution
        self.shell_syntax_patterns = [
            r'\|',              # pipes
            r'>|>>',            # redirects  
            r'&$',              # backgrounding
            r'\$\(',            # command substitution
            r'`[^`]+`',         # backtick command substitution
            r'\$\{[^}]+\}',     # parameter expansion
            r'\$[A-Za-z_][A-Za-z0-9_]*',  # environment variable references
            r'[*?[\]]',         # glob patterns
            r'[A-Za-z_][A-Za-z0-9_]*=',   # assignments
            r'\(',              # subshells
            r'&&|\|\|',         # logical operators
            r';',               # command separators
            r'~',               # home directory expansion
        ]
        self.compiled_patterns = [re.compile(pattern) for pattern in self.shell_syntax_patterns]
        
        # Built-in commands handled by the agent itself
        self.builtin_commands = {'cd', 'pwd', 'exit'}
    
    def _get_bash_commands(self) -> Set[str]:
        """Get set of available bash commands, builtins, and aliases"""
        commands = set()
        
        # Get bash builtins
        try:
            result = subprocess.run(['bash', '-c', 'compgen -b'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                commands.update(result.stdout.strip().split('\n'))
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            # Fallback to common builtins if compgen fails
            commands.update([
                'cd', 'pwd', 'echo', 'printf', 'read', 'test', '[', 'export',
                'unset', 'set', 'shift', 'source', '.', 'eval', 'exec', 'exit',
                'return', 'break', 'continue', 'if', 'then', 'else', 'elif', 
                'fi', 'case', 'esac', 'while', 'until', 'for', 'do', 'done',
                'function', 'time', 'coproc', 'select', 'alias', 'unalias',
                'bg', 'fg', 'jobs', 'kill', 'wait', 'trap', 'type', 'hash',
                'help', 'history', 'fc', 'pushd', 'popd', 'dirs', 'let',
                'local', 'declare', 'readonly', 'getopts', 'command', 'builtin'
            ])
        
        # Get available commands from PATH
        try:
            result = subprocess.run(['bash', '-c', 'compgen -c'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                commands.update(result.stdout.strip().split('\n'))
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            # Fallback to common commands
            commands.update([
                'ls', 'cat', 'grep', 'find', 'awk', 'sed', 'sort', 'uniq',
                'head', 'tail', 'less', 'more', 'vim', 'nano', 'emacs',
                'cp', 'mv', 'rm', 'mkdir', 'rmdir', 'touch', 'chmod', 'chown',
                'ps', 'top', 'htop', 'kill', 'killall', 'pkill', 'pgrep',
                'netstat', 'ss', 'ping', 'traceroute', 'nslookup', 'dig',
                'curl', 'wget', 'git', 'docker', 'kubectl', 'helm', 'k3d',
                'python', 'python3', 'node', 'npm', 'pip', 'pip3',
                'make', 'gcc', 'g++', 'clang', 'gdb', 'valgrind'
            ])
        
        return commands
    
    def should_handle(self, prompt: str, context: Dict[str, Any]) -> bool:
        """
        Command router should always handle prompts to determine routing.
        """
        return True  # Always process to determine routing
    
    async def process(self, prompt: str, context: Dict[str, Any]) -> AgentResult:
        """
        Process the prompt and determine if it should go to Bash or AI.
        """
        prompt = prompt.strip()
        if not prompt:
            return AgentResult(handled=False, response="")
        
        # Check for built-in commands first
        if self._is_builtin_command(prompt):
            return await self._handle_builtin_command(prompt, context)
        
        # Check if it's a shell command
        if self._is_shell_command(prompt):
            return AgentResult(
                handled=True,
                response=f"🖥️ **Executing as Bash command:** `{prompt}`\n\n"
                        f"This will be executed in the shell environment.",
                metadata={"routing": "bash", "command": prompt}
            )
        
        # Default to AI processing
        return AgentResult(
            handled=True,
            response=f"🤖 **Processing with AI:** `{prompt}`\n\n"
                    f"This will be sent to the AI model for natural language processing.",
            metadata={"routing": "ai", "prompt": prompt}
        )
    
    def _is_builtin_command(self, prompt: str) -> bool:
        """Check if the prompt is a built-in command"""
        tokens = prompt.split()
        if not tokens:
            return False
        
        first_token = tokens[0]
        return first_token in self.builtin_commands
    
    def _is_shell_command(self, prompt: str) -> bool:
        """
        Determine if the prompt should be executed as a shell command.
        
        Returns True if:
        1. First token is a known bash command/builtin/alias
        2. Contains shell syntax patterns
        """
        tokens = prompt.split()
        if not tokens:
            return False
        
        first_token = tokens[0]
        
        # Check if first token is a known command
        if first_token in self.bash_commands:
            return True
        
        # Check for shell syntax patterns
        for pattern in self.compiled_patterns:
            if pattern.search(prompt):
                return True
        
        return False
    
    async def _handle_builtin_command(self, prompt: str, context: Dict[str, Any]) -> AgentResult:
        """Handle built-in commands"""
        tokens = prompt.split()
        command = tokens[0]
        args = tokens[1:] if len(tokens) > 1 else []
        
        if command == 'cd':
            if args:
                target_dir = args[0]
                try:
                    import os
                    os.chdir(target_dir)
                    return AgentResult(
                        handled=True,
                        response=f"📁 Changed directory to: {os.getcwd()}",
                        metadata={"routing": "builtin", "command": "cd", "directory": target_dir}
                    )
                except Exception as e:
                    return AgentResult(
                        handled=True,
                        response=f"❌ Failed to change directory: {e}",
                        metadata={"routing": "builtin", "command": "cd", "error": str(e)}
                    )
            else:
                return AgentResult(
                    handled=True,
                    response="❌ cd: missing directory argument",
                    metadata={"routing": "builtin", "command": "cd", "error": "missing_argument"}
                )
        
        elif command == 'pwd':
            import os
            current_dir = os.getcwd()
            return AgentResult(
                handled=True,
                response=f"📁 Current directory: {current_dir}",
                metadata={"routing": "builtin", "command": "pwd", "directory": current_dir}
            )
        
        elif command == 'exit':
            return AgentResult(
                handled=True,
                response="👋 Goodbye!",
                metadata={"routing": "builtin", "command": "exit"}
            )
        
        else:
            # Unknown builtin - shouldn't happen
            return AgentResult(
                handled=True,
                response=f"❌ Unknown builtin command: {command}",
                metadata={"routing": "builtin", "command": command, "error": "unknown_builtin"}
            )
    
    def get_help(self) -> str:
        """Get help text for the command router agent"""
        return """
Command Router Agent - Routes commands between Bash and AI execution

This agent is the final step in the processing chain and determines whether
a prompt should be executed as a shell command or sent to AI for processing.

Routing Rules:
• Built-in commands (cd, pwd, exit) are handled directly
• Commands starting with known shell commands go to Bash
• Commands with shell syntax (|, >, $, etc.) go to Bash  
• Everything else goes to AI for natural language processing

Examples:
• "ls -la" → Bash execution
• "what files are here?" → AI processing
• "cd /tmp" → Built-in command
• "find . -name '*.py' | grep test" → Bash execution
• "explain this error" → AI processing

The agent provides clear feedback about which routing decision was made.
"""
