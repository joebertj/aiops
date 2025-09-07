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
        self.current_dir = os.getcwd()  # Track current working directory
        
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
            
            self.bash_executor = BashExecutor(self.current_dir)
            
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
    
    def _handle_cd_command(self, command: str) -> str:
        """Handle cd command and update working directory"""
        debug_log(f"Handling cd command: {command}")
        
        if command == 'cd':
            # cd with no arguments goes to home directory
            new_dir = os.path.expanduser("~")
        else:
            # cd with path argument
            path = command[3:].strip()  # Remove 'cd ' prefix
            if path.startswith('~'):
                new_dir = os.path.expanduser(path)
            elif os.path.isabs(path):
                new_dir = path
            else:
                new_dir = os.path.join(self.current_dir, path)
        
        try:
            # Resolve the path and check if it exists
            new_dir = os.path.abspath(new_dir)
            if os.path.isdir(new_dir):
                self.current_dir = new_dir
                # Update bash executor working directory
                if self.bash_executor:
                    self.bash_executor.set_cwd(self.current_dir)
                debug_log(f"Changed directory to: {self.current_dir}")
                return ""  # cd successful, no output
            else:
                return f"cd: {new_dir}: No such file or directory\n"
        except Exception as e:
            return f"cd: {e}\n"
    
    async def process_command(self, command: str) -> str:
        """Process command and return response"""
        try:
            debug_log(f"process_command: Starting with command: {command}")
            
            # Check for working directory sync from frontend
            if command.startswith('SYNC_CWD:'):
                new_dir = command[9:]  # Remove 'SYNC_CWD:' prefix
                debug_log(f"Syncing working directory to: {new_dir}")
                self.current_dir = new_dir
                if self.bash_executor:
                    self.bash_executor.set_cwd(self.current_dir)
                return ""  # No output for sync command
            
            # Check for cd command first (fallback - should be handled by frontend)
            if command.strip().startswith('cd ') or command.strip() == 'cd':
                debug_log(f"Detected cd command: '{command.strip()}'")
                return self._handle_cd_command(command.strip())
            
            # Check for pwd command
            if command.strip() == 'pwd':
                return f"{self.current_dir}\n"
            
            # Interactive commands - tell frontend to handle directly
            if self._is_interactive_command(command):
                debug_log("process_command: Interactive command detected")
                return f"INTERACTIVE:{command}\n"
            
            # Try bash first
            if self.bash_executor:
                debug_log("process_command: Executing bash command")
                exit_code, stdout, stderr = await self.bash_executor.execute(command)
                debug_log(f"process_command: Bash result - exit: {exit_code}, stdout: {len(stdout) if stdout else 0} chars")
                
                # Success cases - return bash output directly (bypass AI)
                if exit_code == 0:
                    if stdout and not stderr:
                        debug_log("process_command: Clean success, returning bash output")
                        return stdout
                    elif stdout:  # Has output but also has stderr - still successful
                        debug_log("process_command: Success with warnings, returning bash output")
                        return stdout + (stderr if stderr else "")
                    elif not stderr:  # No output, no errors (like cd)
                        debug_log("process_command: Empty success, returning empty")
                        return ""
                
                # Command failed - let AI handle if ready, otherwise show bash output
                debug_log(f"process_command: Command failed (exit={exit_code}), ai_ready: {self.ai_ready}")
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
                
                # Handle empty response with retry
                if not response or len(response.strip()) == 0:
                    debug_log("❌ Empty AI response received! Retrying once...")
                    debug_log(f"Raw response: '{response}'")
                    
                    # Wait a moment and retry
                    await asyncio.sleep(1)
                    debug_log("🔄 Retrying AI request...")
                    
                    try:
                        retry_response = await asyncio.wait_for(collect_response(), timeout=300)
                        debug_log(f"Retry response: {len(retry_response)} chars")
                        
                        if retry_response and len(retry_response.strip()) > 0:
                            debug_log("✅ Retry succeeded!")
                            response = retry_response
                        else:
                            debug_log("❌ Retry also returned empty response")
                            debug_log(f"Retry raw response: '{retry_response}'")
                            return "❌ AI returned empty response twice - please check AI configuration or try again later\n"
                    except Exception as retry_error:
                        debug_log(f"❌ Retry failed with error: {retry_error}")
                        return f"❌ AI returned empty response and retry failed: {retry_error}\n"
                
                # Show first part of response for debugging
                debug_log(f"AI response preview: '{response[:100]}{'...' if len(response) > 100 else ''}'")
                
                # Check response type and handle accordingly
                if "awesh:" in response:
                    debug_log("Found awesh: commands in AI response")
                    return await self._extract_and_execute_commands(response)
                elif await self._contains_questions_or_options(response):
                    debug_log("Found questions/options in AI response")
                    return await self._handle_ai_questions(response)
                else:
                    debug_log("Regular AI response, returning as-is")
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
        """Extract awesh: commands from AI response and execute them using stack approach"""
        import re
        
        debug_log("Extracting awesh: commands from AI response")
        
        # Find all awesh: command patterns
        awesh_commands = re.findall(r'awesh:\s*(.+)', ai_response)
        
        if not awesh_commands:
            debug_log("No awesh: commands found")
            return f"🤖 {ai_response}\n"
        
        debug_log(f"Found {len(awesh_commands)} awesh: commands")
        
        # Create stack of commands (reverse order so we pop from first to last)
        command_stack = [cmd.strip() for cmd in reversed(awesh_commands)]
        failed_commands = []
        
        # Try commands one by one until we find one that works
        while command_stack:
            command = command_stack.pop()
            debug_log(f"Trying command: {command}")
            
            # Execute the command using bash executor
            if self.bash_executor:
                exit_code, stdout, stderr = await self.bash_executor.execute(command)
                
                debug_log(f"Command result: exit={exit_code}, stdout={len(stdout) if stdout else 0} chars, stderr={len(stderr) if stderr else 0} chars")
                
                # Check if command succeeded (exit_code=0 OR has stdout)
                if exit_code == 0 or stdout:
                    debug_log(f"Command succeeded: {command}")
                    return stdout if stdout else "Command executed successfully (no output)\n"
                else:
                    # Command failed, add to failed list and try next
                    debug_log(f"Command failed: {command} (exit={exit_code})")
                    failed_commands.append(command)
        
        # All commands failed, try to get alternatives from AI
        debug_log(f"All {len(failed_commands)} commands failed, requesting alternatives")
        return await self._request_command_alternatives(failed_commands)
    
    async def _request_command_alternatives(self, failed_commands: list) -> str:
        """Request alternative commands from AI when all initial commands fail"""
        debug_log("Requesting alternative commands from AI")
        
        failed_list = "\n".join([f"- {cmd}" for cmd in failed_commands])
        retry_prompt = f"""The following commands failed:
{failed_list}

Please provide alternative awesh: commands that might work better. Return only working bash commands in the format:
awesh: <command>"""
        
        # Send retry request to AI
        try:
            retry_response = await self._handle_ai_prompt(retry_prompt)
            
            # Check if AI provided new awesh: commands
            if "awesh:" in retry_response:
                debug_log("AI provided alternative commands, trying them")
                return await self._extract_and_execute_commands(retry_response)
            else:
                debug_log("AI didn't provide alternative commands")
                return f"❌ All commands failed and no alternatives provided:\n{failed_list}\n\n🤖 {retry_response}\n"
                
        except Exception as e:
            debug_log(f"Error requesting alternatives: {e}")
            return f"❌ All commands failed:\n{failed_list}\n"
    
    async def _contains_questions_or_options(self, response: str) -> bool:
        """Check if AI response contains questions or multiple options"""
        import re
        
        # Look for common question patterns
        question_patterns = [
            r'\?',  # Contains question mark
            r'Which.*do you want',  # "Which do you want"
            r'Do you want to',  # "Do you want to"
            r'Would you like to',  # "Would you like to"
            r'Please specify',  # "Please specify"
            r'Could you clarify',  # "Could you clarify"
            r'What.*do you mean',  # "What do you mean"
            r'Here are.*options?:',  # "Here are some options:"
            r'\d+\.\s',  # Numbered list (1. 2. 3.)
            r'^[a-zA-Z]\)\s',  # Lettered list (a) b) c))
            r'Choose from:',  # "Choose from:"
            r'Select.*option',  # "Select an option"
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, response, re.IGNORECASE | re.MULTILINE):
                debug_log(f"Found question pattern: {pattern}")
                return True
                
        return False
    
    async def _handle_ai_questions(self, ai_response: str) -> str:
        """Handle AI questions/options by automatically trying each option until we get a clean result"""
        import re
        
        debug_log("Processing AI questions/options automatically")
        
        # Extract numbered or lettered options
        options = []
        
        # Look for numbered options (1. 2. 3.)
        numbered_options = re.findall(r'(\d+\.\s*[^\n]+)', ai_response)
        if numbered_options:
            # Clean up the options (remove numbers/bullets)
            cleaned_options = [re.sub(r'^\d+\.\s*', '', opt).strip() for opt in numbered_options]
            options.extend(cleaned_options)
            debug_log(f"Found {len(numbered_options)} numbered options")
        
        # Look for lettered options (a) b) c))
        lettered_options = re.findall(r'([a-zA-Z]\)\s*[^\n]+)', ai_response)
        if lettered_options:
            # Clean up the options (remove letters/bullets)
            cleaned_options = [re.sub(r'^[a-zA-Z]\)\s*', '', opt).strip() for opt in lettered_options]
            options.extend(cleaned_options)
            debug_log(f"Found {len(lettered_options)} lettered options")
        
        if options:
            debug_log(f"Found {len(options)} total options, trying them automatically")
            return await self._try_options_stack(options)
        else:
            # No clear options found, but response seems to be a question
            # Try to extract any meaningful phrases to attempt
            debug_log("No clear options found, extracting potential interpretations")
            return await self._extract_and_try_interpretations(ai_response)
    
    async def _try_options_stack(self, options: list) -> str:
        """Try each option in the stack until we get a clean result"""
        debug_log(f"🔄 Starting option stack with {len(options)} options:")
        for i, opt in enumerate(options, 1):
            debug_log(f"   Option {i}: {opt}")
        
        # Create stack of options (reverse order so we pop from first to last)
        option_stack = [opt.strip() for opt in reversed(options)]
        failed_options = []
        option_number = 1
        
        while option_stack:
            option = option_stack.pop()
            debug_log(f"🎯 TRYING OPTION {option_number}/{len(options)}: {option}")
            
            try:
                # Send the option back to AI to get commands
                option_prompt = f"Please provide awesh: commands for: {option}"
                debug_log(f"🤖 Asking AI for commands for option {option_number}")
                option_response = await self._handle_ai_prompt(option_prompt)
                
                # Check if AI provided awesh: commands
                if "awesh:" in option_response:
                    debug_log(f"✅ Option {option_number} provided commands, trying them now")
                    result = await self._extract_and_execute_commands_with_option_context(option_response, option, option_number)
                    
                    # Check if we got a clean result (no error indicators)
                    if not ("❌" in result or "All commands failed" in result):
                        debug_log(f"🎉 SUCCESS! Option {option_number} '{option}' worked perfectly!")
                        return result
                    else:
                        debug_log(f"❌ Option {option_number} '{option}' commands all failed")
                        failed_options.append(option)
                else:
                    debug_log(f"❌ Option {option_number} '{option}' didn't provide any commands")
                    failed_options.append(option)
                    
            except Exception as e:
                debug_log(f"❌ Error trying option {option_number} '{option}': {e}")
                failed_options.append(option)
            
            option_number += 1
        
        # All options failed
        debug_log(f"💥 All {len(failed_options)} options exhausted, none worked")
        failed_list = "\n".join([f"- {opt}" for opt in failed_options])
        return f"❌ All options failed:\n{failed_list}\n"
    
    async def _extract_and_execute_commands_with_option_context(self, ai_response: str, option: str, option_number: int) -> str:
        """Extract awesh: commands from AI response and execute them with enhanced debug logging for option context"""
        import re
        
        debug_log(f"🔍 Extracting commands from option {option_number} response")
        
        # Find all awesh: command patterns
        awesh_commands = re.findall(r'awesh:\s*(.+)', ai_response)
        
        if not awesh_commands:
            debug_log(f"❌ No awesh: commands found in option {option_number} response")
            return f"No awesh: commands found for option: {option}\n"
        
        debug_log(f"📋 Found {len(awesh_commands)} commands for option {option_number} '{option}':")
        for i, cmd in enumerate(awesh_commands, 1):
            debug_log(f"   Command {i}: {cmd.strip()}")
        
        # Create stack of commands (reverse order so we pop from first to last)
        command_stack = [cmd.strip() for cmd in reversed(awesh_commands)]
        failed_commands = []
        command_number = 1
        
        # Try commands one by one until we find one that works
        while command_stack:
            command = command_stack.pop()
            debug_log(f"⚡ TRYING COMMAND {command_number}/{len(awesh_commands)} for option {option_number}: {command}")
            
            # Execute the command using bash executor
            if self.bash_executor:
                exit_code, stdout, stderr = await self.bash_executor.execute(command)
                
                debug_log(f"📊 Command {command_number} result: exit={exit_code}, stdout={len(stdout) if stdout else 0} chars, stderr={len(stderr) if stderr else 0} chars")
                
                # Check if command succeeded (exit_code=0 OR has stdout)
                if exit_code == 0 or stdout:
                    debug_log(f"🎉 JACKPOT! Command {command_number} in option {option_number} succeeded: {command}")
                    debug_log(f"✨ First try success - option {option_number}, command {command_number} worked perfectly!")
                    return stdout if stdout else "Command executed successfully (no output)\n"
                else:
                    # Command failed, add to failed list and try next
                    debug_log(f"❌ Command {command_number} failed: {command} (exit={exit_code})")
                    if stderr:
                        debug_log(f"   stderr: {stderr[:100]}...")  # Show first 100 chars of stderr
                    failed_commands.append(command)
            
            command_number += 1
        
        # All commands for this option failed
        debug_log(f"💥 All {len(failed_commands)} commands failed for option {option_number} '{option}'")
        return await self._request_command_alternatives(failed_commands)
    
    async def _extract_and_try_interpretations(self, ai_response: str) -> str:
        """Extract potential interpretations from unclear AI response and try them"""
        debug_log("Extracting interpretations from unclear response")
        
        # Try to send the response back to AI for clarification
        clarify_prompt = f"The previous response was: {ai_response}\n\nPlease provide specific awesh: commands to help with this request."
        
        try:
            clarify_response = await self._handle_ai_prompt(clarify_prompt)
            
            if "awesh:" in clarify_response:
                debug_log("Got commands from clarification, trying them")
                return await self._extract_and_execute_commands(clarify_response)
            else:
                debug_log("No commands from clarification")
                return f"🤖 {ai_response}\n\n❌ Could not determine specific actions to take.\n"
                
        except Exception as e:
            debug_log(f"Error getting clarification: {e}")
            return f"🤖 {ai_response}\n\n❌ Could not process request: {e}\n"
    
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
