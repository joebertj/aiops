"""
Bash command executor for awesh
"""

import subprocess
import asyncio
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
            # Run command in subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd
            )
            
            stdout, stderr = await process.communicate()
            
            return (
                process.returncode,
                stdout.decode('utf-8') if stdout else "",
                stderr.decode('utf-8') if stderr else ""
            )
            
        except Exception as e:
            return (1, "", f"Execution error: {e}\n")