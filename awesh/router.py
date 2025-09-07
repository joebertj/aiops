"""
Command router for awesh - decides whether input goes to Bash or AI
"""

import re
import shutil
import subprocess
from typing import Tuple, Optional, Set


class CommandRouter:
    """Routes commands between Bash and AI based on detection rules"""
    
    def __init__(self):
        self.bash_commands = self._get_bash_commands()
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
                'history', 'fc', 'jobs', 'bg', 'fg', 'disown', 'suspend',
                'kill', 'wait', 'trap', 'type', 'which', 'command', 'builtin',
                'enable', 'help', 'let', 'local', 'readonly', 'declare',
                'typeset', 'getopts', 'hash', 'dirs', 'pushd', 'popd',
                'shopt', 'complete', 'compgen', 'bind', 'caller', 'ulimit'
            ])
        
        # Get commands in PATH
        try:
            result = subprocess.run(['bash', '-c', 'compgen -c'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                path_commands = result.stdout.strip().split('\n')
                # Filter out empty strings and very long lists
                path_commands = [cmd for cmd in path_commands if cmd and len(cmd) < 50]
                commands.update(path_commands[:1000])  # Limit to prevent memory issues
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            # Fallback to common commands
            commands.update([
                'ls', 'cd', 'pwd', 'mkdir', 'rmdir', 'rm', 'cp', 'mv', 'ln',
                'chmod', 'chown', 'chgrp', 'find', 'grep', 'sed', 'awk', 'sort',
                'uniq', 'cut', 'tr', 'head', 'tail', 'cat', 'less', 'more',
                'vim', 'nano', 'emacs', 'git', 'curl', 'wget', 'tar', 'gzip',
                'gunzip', 'zip', 'unzip', 'ps', 'top', 'htop', 'kill', 'killall',
                'man', 'which', 'whereis', 'locate', 'file', 'stat', 'du', 'df',
                'mount', 'umount', 'lsof', 'netstat', 'ss', 'ping', 'traceroute',
                'ssh', 'scp', 'rsync', 'make', 'gcc', 'g++', 'python', 'python3',
                'pip', 'pip3', 'node', 'npm', 'yarn', 'docker', 'kubectl'
            ])
        
        return commands
    
    def route_command(self, line: str) -> Tuple[str, str]:
        """
        Route a command line to either 'bash' or 'ai'
        
        Args:
            line: Input line to route
            
        Returns:
            Tuple of (destination, cleaned_line) where destination is 'bash' or 'ai'
        """
        line = line.strip()
        
        if not line:
            return 'ai', line
        
        # Check for shell syntax patterns first
        for pattern in self.compiled_patterns:
            if pattern.search(line):
                return 'bash', line
        
        # Check if first token is a known bash command
        tokens = line.split()
        if tokens:
            first_token = tokens[0]
            
            # Handle command prefixes (sudo, env, etc.)
            if first_token in ['sudo', 'env', 'time', 'timeout', 'nice', 'nohup']:
                if len(tokens) > 1:
                    first_token = tokens[1]
            
            # Check if it's a known bash command
            if first_token in self.bash_commands:
                return 'bash', line
            
            # Check for executable in PATH
            if shutil.which(first_token):
                return 'bash', line
        
        # Default to AI
        return 'ai', line
    
    def is_builtin_command(self, line: str) -> bool:
        """Check if command is an awesh builtin (cd, pwd, exit)"""
        tokens = line.strip().split()
        if not tokens:
            return False
        return tokens[0] in ['cd', 'pwd', 'exit']
