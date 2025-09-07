#!/usr/bin/env python3
"""
Socket-based backend for awesh C frontend
"""

import os
import sys
import socket
import asyncio
import threading
from pathlib import Path

from .config import Config
from .ai_client import AweshAIClient
from .bash_executor import BashExecutor

# Global verbose setting
VERBOSE = os.getenv('VERBOSE', '0') == '1'

def debug_log(message):
    """Log debug message if verbose mode is enabled"""
    if VERBOSE:
        print(f"🔧 {message}", file=sys.stderr)

import os
SOCKET_PATH = os.path.expanduser("~/.awesh.sock")

class AweshSocketBackend:
    """Socket-based backend for C frontend"""
    
    def __init__(self):
        self.config = Config.load(Path.home() / '.aweshrc')
        self.ai_client = None
        self.bash_executor = None
        self.ai_ready = False
        self.socket = None
        
    async def initialize(self):
        """Initialize AI components"""
        try:
            print("Backend: Initializing AI client...", file=sys.stderr)
            self.ai_client = AweshAIClient(self.config)
            await self.ai_client.initialize()
            self.ai_ready = True
            print("Backend: AI client ready!", file=sys.stderr)
            
            self.bash_executor = BashExecutor(".")
            
        except Exception as e:
            print(f"Backend: AI init failed: {e}", file=sys.stderr)
    
    def _is_interactive_command(self, command: str) -> bool:
        """Check if command needs interactive terminal"""
        interactive_commands = {
            'vi', 'vim', 'nano', 'emacs', 'htop', 'top', 'less', 'more', 
            'man', 'ssh', 'ftp', 'telnet', 'mysql', 'psql', 'python', 
            'python3', 'node', 'irb', 'bash', 'sh', 'zsh'
        }
        first_word = command.strip().split()[0] if command.strip() else ""
        return first_word in interactive_commands
    
    async def process_command(self, command: str) -> str:
        """Process command and return response"""
        try:
            debug_log(f"process_command: Starting with command: {command}")
            
            # Interactive commands - tell frontend to handle directly
            if self._is_interactive_command(command):
                debug_log("process_command: Interactive command detected")
                return f"INTERACTIVE:{command}\n"
            
            # Try bash first
            if self.bash_executor:
                debug_log("process_command: Executing bash command")
                exit_code, stdout, stderr = await self.bash_executor.execute(command)
                debug_log(f"process_command: Bash result - exit: {exit_code}, stdout: {len(stdout) if stdout else 0} chars")
                
                # Clean success - return output directly (bypass AI)
                if exit_code == 0 and stdout and not stderr:
                    debug_log("process_command: Clean success, returning bash output")
                    return stdout
                
                # Success but no output (like cd) - return empty
                if exit_code == 0 and not stdout and not stderr:
                    debug_log("process_command: Empty success, returning empty")
                    return ""
                
                # Command failed - let AI handle if ready, otherwise show bash output
                debug_log(f"process_command: Command needs AI processing, ai_ready: {self.ai_ready}")
                if self.ai_ready:
                    bash_result = {"stdout": stdout, "stderr": stderr, "exit_code": exit_code}
                    debug_log("process_command: Sending to AI")
                    return await self._handle_ai_prompt(command, bash_result)
                else:
                    # AI not ready - return bash output directly
                    debug_log("process_command: AI not ready, returning bash output")
                    result = ""
                    if stdout:
                        result += stdout
                    if stderr:
                        result += stderr
                    return result
            else:
                # No bash executor - AI handles everything
                debug_log("process_command: No bash executor, sending to AI")
                return await self._handle_ai_prompt(command)
                
        except Exception as e:
            debug_log(f"process_command: Exception: {e}")
            return f"Backend error: {e}\n"
    
    async def _handle_ai_prompt(self, prompt: str, bash_result: dict = None) -> str:
        """Handle AI prompt and return response"""
        if not self.ai_ready:
            # AI not ready - if this was a bash failure, show the bash output
            if bash_result:
                result = ""
                if bash_result.get("stdout"):
                    result += bash_result["stdout"]
                if bash_result.get("stderr"):
                    result += bash_result["stderr"]
                return result
            else:
                # Pure AI prompt but AI not ready
                return "❌ AI not ready yet - still loading models\n"
        
        try:
            # For now, return a simple response to test if the issue is with OpenAI API
            return f"🤖 AI received: {prompt}\n(OpenAI integration temporarily disabled for debugging)\n"
            
        except Exception as e:
            return f"❌ AI error: {e}\n"
    
    async def handle_client(self, client_socket):
        """Handle client connection"""
        try:
            # Set socket to non-blocking mode
            client_socket.setblocking(False)
            
            while True:
                # Receive command using asyncio
                loop = asyncio.get_event_loop()
                try:
                    data = await loop.sock_recv(client_socket, 4096)
                    if not data:
                        break
                    
                    command = data.decode('utf-8').strip()
                    if not command:
                        continue
                    
                    # Handle status requests
                    if command == "STATUS":
                        if self.ai_ready:
                            response = "AI_READY"
                        else:
                            response = "AI_LOADING"
                        debug_log(f"STATUS response: {response}")
                    else:
                        # Process regular command
                        debug_log(f"Processing command: {command}")
                        response = await self.process_command(command)
                        debug_log(f"Response ready: {response[:50]}...")

                    # Send response using asyncio
                    debug_log("Sending response...")
                    await loop.sock_sendall(client_socket, response.encode('utf-8'))
                    debug_log("Response sent successfully")
                    
                except ConnectionResetError:
                    break
                except Exception as e:
                    print(f"Command processing error: {e}", file=sys.stderr)
                    break
                
        except Exception as e:
            print(f"Client handler error: {e}", file=sys.stderr)
        finally:
            client_socket.close()
    
    async def run_server(self):
        """Run socket server"""
        # Remove existing socket
        try:
            os.unlink(SOCKET_PATH)
        except OSError:
            pass
        
        # Create socket
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(SOCKET_PATH)
        self.socket.listen(1)
        
        print(f"Backend: Listening on {SOCKET_PATH}", file=sys.stderr)
        
        # Start AI initialization in background
        asyncio.create_task(self.initialize())
        
        # Set server socket to non-blocking
        self.socket.setblocking(False)
        
        # Accept connections
        loop = asyncio.get_event_loop()
        while True:
            try:
                client_socket, _ = await loop.sock_accept(self.socket)
                print("Backend: Client connected", file=sys.stderr)
                
                # Handle client in background
                asyncio.create_task(self.handle_client(client_socket))
                
            except Exception as e:
                print(f"Server error: {e}", file=sys.stderr)
                break
    
    def cleanup(self):
        """Cleanup resources"""
        if self.socket:
            self.socket.close()
        try:
            os.unlink(SOCKET_PATH)
        except OSError:
            pass

async def main():
    backend = AweshSocketBackend()
    
    try:
        await backend.run_server()
    except KeyboardInterrupt:
        print("Backend: Shutting down...", file=sys.stderr)
    finally:
        backend.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
