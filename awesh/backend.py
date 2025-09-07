#!/usr/bin/env python3
"""
Backend subprocess for awesh - handles all heavy AI operations
This runs as a separate process to keep the frontend shell instant
"""

import os
import sys
import json
import socket
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from ai_client import AweshAIClient
from bash_executor import BashExecutor


class AweshBackend:
    """Backend subprocess that handles AI and command routing"""
    
    def __init__(self):
        self.config = Config.load()
        self.ai_client = None
        self.bash_executor = None
        self.ai_ready = False
        
    async def initialize(self):
        """Initialize heavy AI components"""
        try:
            # Initialize AI client
            self.ai_client = AweshAIClient(self.config)
            await self.ai_client.initialize()
            self.ai_ready = True
            
            # Initialize bash executor
            self.bash_executor = BashExecutor(".")
            
            # Send AI ready signal to parent
            sys.stdout.write("AI_READY\n")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"Backend init error: {e}", file=sys.stderr)
    
    async def process_command(self, command: str) -> dict:
        """Simple routing: bash first, then AI if bash fails"""
        try:
            # Try bash first
            if self.bash_executor:
                exit_code, stdout, stderr = await self.bash_executor.execute(command)
                
                # Bash succeeded - return result
                if exit_code == 0:
                    return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code}
                
                # Bash failed - let AI handle it if ready
                if self.ai_ready:
                    return await self._handle_ai_prompt(command, {"stdout": stdout, "stderr": stderr, "exit_code": exit_code})
                else:
                    return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code}
            else:
                # No bash executor - AI handles everything
                return await self._handle_ai_prompt(command)
                
        except Exception as e:
            return {"stdout": "", "stderr": f"Backend error: {e}\n", "exit_code": 1}
    
    
    async def _handle_ai_prompt(self, prompt: str, bash_failed: dict = None) -> dict:
        """Let AI handle everything - prompts, failed commands, suggestions"""
        if not self.ai_ready:
            return {"stdout": "🔄 AI still loading...\n", "stderr": "", "exit_code": 0}
        
        try:
            # Give AI the context and let it decide what to do
            if bash_failed:
                ai_input = f"User typed: {prompt}\nBash failed with: {bash_failed.get('stderr', '')}\nHelp the user."
            else:
                ai_input = prompt
            
            output = "🤖 "
            async for chunk in self.ai_client.process_prompt(ai_input):
                output += chunk
            output += "\n"
            
            return {"stdout": output, "stderr": "", "exit_code": 0}
        except Exception as e:
            return {"stdout": "", "stderr": f"❌ AI error: {e}\n", "exit_code": 1}


async def main():
    """Main backend process"""
    backend = AweshBackend()
    
    # Send ready signal to parent
    sys.stdout.write("READY\n")
    sys.stdout.flush()
    
    # Initialize in background
    asyncio.create_task(backend.initialize())
    
    # Process commands from stdin
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            # Parse command
            try:
                data = json.loads(line.strip())
                command = data.get("command", "")
                
                if command:
                    # Process command
                    response = await backend.process_command(command)
                    
                    # Send response
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                    
            except json.JSONDecodeError:
                # Invalid JSON, ignore
                continue
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            error_response = {
                "stdout": "",
                "stderr": f"Backend error: {e}\n",
                "exit_code": 1
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(main())
