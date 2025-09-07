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
            if VERBOSE:
                print("🤖 Backend: Initializing AI client...", file=sys.stderr)
            self.ai_client = AweshAIClient(self.config)
            await self.ai_client.initialize()
            self.ai_ready = True
            if VERBOSE:
                print("✅ Backend: AI client ready!", file=sys.stderr)
            
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
            # Give AI full context
            if bash_result:
                ai_input = f"""User command: {prompt}
Bash result:
- Exit code: {bash_result.get('exit_code', 0)}
- Stdout: {bash_result.get('stdout', '')}
- Stderr: {bash_result.get('stderr', '')}

Process this and respond appropriately. If you provide commands for the user to run, format them as:
awesh: <command>

This allows the system to execute them automatically."""
            else:
                ai_input = f"""{prompt}

If you provide commands for the user to run, format them as:
awesh: <command>

This allows the system to execute them automatically."""
            
            # Collect response with timeout (compatible with older Python)
            output = "🤖 "
            try:
                async def collect_response():
                    result = ""
                    chunk_count = 0
                    debug_log("Starting AI client process_prompt")
                    async for chunk in self.ai_client.process_prompt(ai_input):
                        result += chunk
                        chunk_count += 1
                        debug_log(f"Received chunk {chunk_count}: {chunk[:50]}...")
                    debug_log(f"Total chunks: {chunk_count}, total length: {len(result)}")
                    return result
                
                debug_log("Calling collect_response with timeout")
                response = await asyncio.wait_for(collect_response(), timeout=300)  # 5 minutes
                debug_log(f"Got response: {len(response)} chars")
                
                # Check if AI provided awesh: commands to execute
                if "awesh:" in response:
                    debug_log("Found awesh: commands in AI response")
                    return await self._extract_and_execute_commands(response)
                else:
                    output += response
                    output += "\n"
                    return output
            except asyncio.TimeoutError:
                return f"❌ AI response timeout - request took too long\n"
            except Exception as stream_error:
                # If streaming fails, try non-streaming fallback
                return f"❌ AI streaming error: {stream_error}\n"
                
        except Exception as e:
            return f"❌ AI error: {e}\n"
    
    async def _extract_and_execute_commands(self, ai_response: str) -> str:
        """Extract awesh: commands from AI response and execute them"""
        import re
        
        debug_log("Extracting awesh: commands from AI response")
        
        # Find all awesh: command patterns
        awesh_commands = re.findall(r'awesh:\s*(.+)', ai_response)
        
        if not awesh_commands:
            debug_log("No awesh: commands found")
            return f"🤖 {ai_response}\n"
        
        debug_log(f"Found {len(awesh_commands)} awesh: commands")
        output = ""
        
        for i, command in enumerate(awesh_commands):
            command = command.strip()
            debug_log(f"Executing awesh command {i+1}: {command}")
            
            # Execute the command using bash executor
            if self.bash_executor:
                exit_code, stdout, stderr = await self.bash_executor.execute(command)
                
                if stdout:
                    output += stdout
                if stderr:
                    output += stderr
                
                debug_log(f"Command {i+1} result: exit={exit_code}, stdout={len(stdout) if stdout else 0} chars")
        
        return output if output else "No output from commands\n"
    
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
                    
                    # Handle special commands
                    if command == "STATUS":
                        if self.ai_ready:
                            response = "AI_READY"
                        else:
                            response = "AI_LOADING"
                        debug_log(f"STATUS response: {response}")
                    elif command.startswith("VERBOSE:"):
                        # Toggle verbose mode dynamically
                        verbose_setting = command.split(":", 1)[1].strip()
                        global VERBOSE
                        if verbose_setting in ["1", "true", "on"]:
                            VERBOSE = True
                            response = "🔧 Verbose mode enabled\n"
                        elif verbose_setting in ["0", "false", "off"]:
                            VERBOSE = False
                            response = "🔇 Verbose mode disabled\n"
                        else:
                            response = f"🔧 Verbose mode: {'enabled' if VERBOSE else 'disabled'}\n"
                        debug_log(f"VERBOSE command: {verbose_setting} -> {VERBOSE}")
                    elif command.startswith("AI_PROVIDER:"):
                        # Switch AI provider dynamically
                        provider = command.split(":", 1)[1].strip()
                        if provider in ["openai", "openrouter"]:
                            # Update config and reinitialize AI client
                            self.config.ai_provider = provider
                            response = f"🤖 Switching to {provider}... (restart awesh to take effect)\n"
                        else:
                            response = f"❌ Unknown AI provider: {provider}\n"
                        debug_log(f"AI_PROVIDER command: {provider}")
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
                    if VERBOSE:
                        print(f"❌ Command processing error: {e}", file=sys.stderr)
                    break
                
        except Exception as e:
            if VERBOSE:
                print(f"💥 Client handler error: {e}", file=sys.stderr)
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
        
        if VERBOSE:
            print(f"🔧 Backend: Listening on {SOCKET_PATH}", file=sys.stderr)
        
        # Start AI initialization in background
        asyncio.create_task(self.initialize())
        
        # Set server socket to non-blocking
        self.socket.setblocking(False)
        
        # Accept connections
        loop = asyncio.get_event_loop()
        while True:
            try:
                client_socket, _ = await loop.sock_accept(self.socket)
                if VERBOSE:
                    print("🔌 Backend: Client connected", file=sys.stderr)
                
                # Handle client in background
                asyncio.create_task(self.handle_client(client_socket))
                
            except Exception as e:
                if VERBOSE:
                    print(f"🚨 Server error: {e}", file=sys.stderr)
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
