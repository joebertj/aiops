"""
Bash command executor for awesh
"""

import subprocess
import asyncio
import os
import sys
from typing import Tuple


class BashExecutor:
    """Executes bash commands and returns results"""
    
    def __init__(self, cwd: str = "."):
        self.cwd = cwd
    
    def set_cwd(self, cwd: str):
        """Set current working directory"""
        self.cwd = cwd
    
    def _is_interactive_command(self, command: str) -> bool:
        """Check if command needs interactive terminal"""
        interactive_commands = {
            'vi', 'vim', 'nano', 'emacs', 'htop', 'top', 'less', 'more', 
            'man', 'ssh', 'ftp', 'telnet', 'mysql', 'psql', 'python', 
            'python3', 'node', 'irb', 'bash', 'sh', 'zsh', 'sudo'
        }
        first_word = command.strip().split()[0] if command.strip() else ""
        return first_word in interactive_commands
    
    async def execute(self, command: str) -> Tuple[int, str, str]:
        """Execute bash command and return (exit_code, stdout, stderr)"""
        try:
            # For interactive commands, run directly in current terminal
            if self._is_interactive_command(command):
                # Run command directly, inheriting our TTY
                process = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.cwd,
                    env=os.environ.copy(),  # Ensure full environment inheritance
                    # Inherit our stdin/stdout/stderr for interactive commands
                    stdin=None,
                    stdout=None, 
                    stderr=None
                )
                return (process.returncode, "", "")
            else:
                # Non-interactive commands - capture output
                # Use subprocess.run with native timeout (more reliable)
                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        cwd=self.cwd,
                        timeout=2.0,  # 2 second native timeout
                        env=os.environ.copy()  # Ensure full environment inheritance
                    )
                    return (result.returncode, result.stdout, result.stderr)
                except subprocess.TimeoutExpired:
                    return (1, "", f"Command timed out (interactive command? try AI instead)\n")
            
        except Exception as e:
            return (1, "", f"Execution error: {e}\n")