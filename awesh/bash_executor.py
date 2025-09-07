"""
Bash command executor for awesh
"""

import os
import subprocess
import asyncio
from typing import Tuple, Optional


class BashExecutor:
    """Executes bash commands with proper error handling"""
    
    def __init__(self, cwd: Optional[str] = None):
        self.cwd = cwd or os.getcwd()
    
    async def execute(self, command: str) -> Tuple[int, str, str]:
        """
        Execute a bash command
        
        Args:
            command: The command to execute
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            # Use asyncio subprocess for non-blocking execution
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=self.cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            return (
                process.returncode or 0,
                stdout.decode('utf-8', errors='replace'),
                stderr.decode('utf-8', errors='replace')
            )
            
        except Exception as e:
            return (1, "", f"awesh: {command}: {str(e)}")
    
    def set_cwd(self, new_cwd: str):
        """Update the current working directory"""
        self.cwd = new_cwd
