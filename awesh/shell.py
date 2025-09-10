"""
Main shell implementation for awesh
"""

import os
import sys
import socket
import subprocess
import json
import threading
from pathlib import Path
from typing import Optional

try:
    from .config import Config
    from .prompt_manager import PromptManager
except ImportError:
    from config import Config
    from prompt_manager import PromptManager

# Lazy imports - only load when needed
CommandRouter = None
BashExecutor = None
AweshAIClient = None


class AweshShell:
    """Frontend: Just shows messages, waits for input, shows output"""
    
    def __init__(self, config: Config):
        self.config = config
        self.current_dir = Path.cwd()
        self.running = True
        self.last_exit_code = 0
        self.last_command = None
        
        # Initialize prompt manager
        self.prompt_manager = PromptManager()

        # Backend subprocess communication
        self.backend_ready = False
        self.ai_ready = False
        self.backend_socket = None
        self.backend_process = None

        # Start backend subprocess - don't wait for it
        threading.Thread(target=self._start_backend_subprocess, daemon=True).start()
        
    def run(self):
        """Frontend: Show messages, wait for input, show output"""
        # Show MOTD immediately
        print(f"awesh v0.1.0 - Awe-Inspired Workspace Environment Shell (AI-aware Interactive Shell)")
        print(f"Model: {self.config.model}")
        print()
        
        # Show initial prompt immediately
        try:
            prompt = self.prompt_manager.get_prompt(False, "")
        except Exception:
            prompt = self.prompt_manager.get_simple_prompt(False)
        print(prompt, flush=True)
        
        # Simple frontend loop - instant
        while self.running:
            try:
                line = input()

                if not line.strip():
                    continue

                # Process command - frontend logic only
                self._handle_command(line)
                
                # Show prompt for next command
                try:
                    prompt = self.prompt_manager.get_prompt(self.ai_ready, "")
                except Exception:
                    prompt = self.prompt_manager.get_simple_prompt(self.ai_ready)
                print(prompt, flush=True)

            except KeyboardInterrupt:
                print()
                continue
            except EOFError:
                break
        
        print("Goodbye!")
    
    def _start_backend_subprocess(self):
        """Start backend as separate subprocess with socket communication"""
        try:
            # Create socket pair for communication
            parent_sock, child_sock = socket.socketpair()
            parent_sock.setblocking(False)  # Non-blocking socket
            
            # Start backend subprocess
            backend_script = Path(__file__).parent / "backend.py"
            self.backend_process = subprocess.Popen([
                sys.executable, str(backend_script)
            ], stdin=child_sock.fileno(), stdout=child_sock.fileno(), 
               stderr=subprocess.PIPE)
            
            child_sock.close()  # Close child socket in parent
            self.backend_socket = parent_sock
            
            # Check for ready signal in background (non-blocking)
            threading.Thread(target=self._wait_for_backend_ready, daemon=True).start()
            
        except Exception as e:
            print(f"⚠️  Backend subprocess failed: {e}")
    
    def _wait_for_backend_ready(self):
        """Wait for backend ready signals in background"""
        try:
            import select
            while True:
                # Wait for socket to be ready
                ready, _, _ = select.select([self.backend_socket], [], [], 30)  # 30s timeout
                if ready:
                    ready_msg = self.backend_socket.recv(1024).decode()
                    msg = ready_msg.strip()
                    if msg == "READY":
                        self.backend_ready = True
                    elif msg == "AI_LOADING":
                        print("🔄 Loading AI models...")
                    elif msg == "AI_READY":
                        self.ai_ready = True
                        print("✅ AI ready! Natural language queries now supported.")
                        break
                    elif msg == "AI_FAILED":
                        self.ai_ready = False
                        print("❌ AI initialization failed - bash-only mode")
                        break
                else:
                    # Timeout
                    print("⚠️  Backend initialization timeout - bash-only mode")
                    break
        except Exception as e:
            print(f"⚠️  Backend ready check failed: {e}")
    
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
        
        # Backend up? Send to backend subprocess
        self._send_to_backend(line)
    
    def _send_to_backend(self, command: str):
        """Send command to backend subprocess via socket"""
        if not self.backend_socket:
            return
        
        try:
            # Send command as JSON
            message = json.dumps({"command": command}) + "\n"
            self.backend_socket.send(message.encode())
            
            # Start thread to receive response
            threading.Thread(target=self._receive_backend_response, daemon=True).start()
            
        except Exception as e:
            print(f"Backend communication error: {e}")
    
    def _receive_backend_response(self):
        """Receive and display response from backend subprocess"""
        try:
            # Receive response
            data = self.backend_socket.recv(4096).decode()
            if data:
                response = json.loads(data.strip())
                
                # Display output
                stdout = response.get("stdout", "")
                stderr = response.get("stderr", "")
                
                if stdout:
                    print(stdout, end='')
                    
                    # Check if AI is asking for confirmation to run a command
                    if "Would you like me to run this? (y/n)" in stdout:
                        self._handle_command_confirmation(stdout)
                        
                if stderr:
                    print(stderr, end='', file=sys.stderr)
                    
        except Exception as e:
            print(f"Backend response error: {e}")
    
    def _handle_command_confirmation(self, ai_response: str):
        """Simple confirmation handling - let AI format however it wants"""
        try:
            # Just get y/n from user - let AI handle the formatting
            confirmation = input().strip().lower()
            if confirmation in ['y', 'yes']:
                print("✅ Confirmed - send to AI to execute")
                # TODO: Send confirmation back to AI to execute the command
            else:
                print("❌ Cancelled")
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Cancelled")
    
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
    
