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
    
    
    async def execute(self, command: str) -> Tuple[int, str, str]:
        """Execute bash command and return (exit_code, stdout, stderr)"""
        try:
            # All commands are now non-interactive (interactive ones handled by C frontend)
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