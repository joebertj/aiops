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
from command_safety import CommandSafetyFilter
from sensitive_data_filter import SensitiveDataFilter

# Import agent system
from agents import (
    SecurityAgent, 
    ProcessAgent,  # Add process monitoring agent
    KubernetesAgent, 
    ContainerAgent, 
    CommandRouterAgent,
    AgentProcessor
)


class AweshBackend:
    """Backend subprocess that handles AI and command routing"""
    
    def __init__(self):
        self.config = Config.load(Path.home() / '.aweshrc')
        self.ai_client = None
        self.bash_executor = None
        self.ai_ready = False
        self.safety_filter = CommandSafetyFilter()
        self.sensitive_filter = SensitiveDataFilter()
        self.pending_confirmation = None  # Store command awaiting confirmation
        
        # Initialize agent system
        self.agent_processor = None
        
    async def initialize(self):
        """Initialize heavy AI components"""
        try:
            # Send loading signal
            sys.stdout.write("AI_LOADING\n")
            sys.stdout.flush()
            
            # Initialize AI client
            self.ai_client = AweshAIClient(self.config)
            await self.ai_client.initialize()
            self.ai_ready = True
            
            # Initialize bash executor
            self.bash_executor = BashExecutor(".")
            
            # Initialize agent system
            print("🔧 Initializing agent system...", file=sys.stderr)
            self._initialize_agents()
            print("🔧 Agent system initialization complete", file=sys.stderr)
            
            # Send AI ready signal to parent
            sys.stdout.write("AI_READY\n")
            sys.stdout.flush()
            
        except Exception as e:
            # Send failure signal
            sys.stdout.write("AI_FAILED\n")
            sys.stdout.flush()
            print(f"Backend init error: {e}", file=sys.stderr)
    
    def _initialize_agents(self):
        """Initialize the agent system"""
        try:
            # Create agents in priority order
            agents = [
                SecurityAgent(),
                ProcessAgent(),  # Add process monitoring agent
                KubernetesAgent(),
                ContainerAgent(),
                CommandRouterAgent()
            ]
            
            # Initialize agent processor
            self.agent_processor = AgentProcessor(agents)
            
            # Debug output with emojis (D³ principle)
            verbose_level = int(os.getenv('VERBOSE', '1'))
            if verbose_level >= 2:
                print("🐛 DEBUG: Agent system initialized successfully", file=sys.stderr)
                print(f"🐛 DEBUG: {len(agents)} agents loaded", file=sys.stderr)
                for agent in agents:
                    print(f"🐛 DEBUG: - {agent.name} (priority: {agent.priority})", file=sys.stderr)
            else:
                print("✅ Agent system initialized successfully")
            
        except Exception as e:
            verbose_level = int(os.getenv('VERBOSE', '1'))
            if verbose_level >= 2:
                print(f"🐛 DEBUG: Agent system initialization failed: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
            else:
                print(f"⚠️ Agent system initialization failed: {e}")
            self.agent_processor = None
    
    def _is_interactive_command(self, command: str) -> bool:
        """Check if command needs interactive terminal"""
        interactive_commands = {
            'vi', 'vim', 'nano', 'emacs', 'htop', 'top', 'less', 'more', 
            'man', 'ssh', 'ftp', 'telnet', 'mysql', 'psql', 'python', 
            'python3', 'node', 'irb', 'bash', 'sh', 'zsh'
        }
        first_word = command.strip().split()[0] if command.strip() else ""
        return first_word in interactive_commands
    
    async def process_command(self, command: str) -> dict:
        """Smart routing: bypass AI for clean successful commands"""
        try:
            # Check for confirmation responses first
            if command.lower().strip() in ['y', 'yes', 'n', 'no']:
                return await self._handle_confirmation_response(command)
            
            # Process through agent system first
            if self.agent_processor:
                try:
                    verbose_level = int(os.getenv('VERBOSE', '1'))
                    if verbose_level >= 2:
                        print(f"🐛 DEBUG: Processing command through agents: '{command}'", file=sys.stderr)
                    
                    context = {"working_directory": os.getcwd(), "user": os.getenv("USER", "unknown")}
                    success, response, modified_prompt, metadata = await self.agent_processor.process_prompt(command, context)
                    
                    if verbose_level >= 2:
                        print(f"🐛 DEBUG: Agent processing result - success: {success}, response: {bool(response)}, modified: {bool(modified_prompt)}", file=sys.stderr)
                    
                    if not success:
                        # Agent processing failed
                        if verbose_level >= 2:
                            print(f"🐛 DEBUG: Agent processing failed: {response}", file=sys.stderr)
                        return {
                            "stdout": "",
                            "stderr": response + "\n",
                            "exit_code": 1
                        }
                    
                    if response:
                        # Agent handled the prompt and provided a response
                        if verbose_level >= 2:
                            print(f"🐛 DEBUG: Agent handled command, returning response", file=sys.stderr)
                        return {
                            "stdout": response + "\n",
                            "stderr": "",
                            "exit_code": 0
                        }
                    
                    # Agent didn't handle, use modified prompt if available
                    if modified_prompt:
                        if verbose_level >= 2:
                            print(f"🐛 DEBUG: Using modified prompt: '{modified_prompt}'", file=sys.stderr)
                        command = modified_prompt
                    else:
                        if verbose_level >= 2:
                            print(f"🐛 DEBUG: No agent handled command, proceeding to bash", file=sys.stderr)
                        
                except Exception as e:
                    verbose_level = int(os.getenv('VERBOSE', '1'))
                    if verbose_level >= 2:
                        print(f"🐛 DEBUG: Agent processing error: {e}", file=sys.stderr)
                        import traceback
                        traceback.print_exc(file=sys.stderr)
                    else:
                        print(f"⚠️ Agent processing error: {e}", file=sys.stderr)
                    # Continue with original command if agent processing fails
            else:
                verbose_level = int(os.getenv('VERBOSE', '1'))
                if verbose_level >= 2:
                    print("🐛 DEBUG: No agent processor available, skipping agent processing", file=sys.stderr)
            
            # Check command safety before executing
            is_safe, unsafe_reason = self.safety_filter.is_command_safe(command)
            if not is_safe:
                return {
                    "stdout": f"🚫 Command blocked for safety: {unsafe_reason}\n",
                    "stderr": "",
                    "exit_code": 1
                }
            
            # Check if command requires confirmation
            needs_confirm, confirm_reason = self.safety_filter.requires_confirmation(command)
            if needs_confirm:
                self.pending_confirmation = command
                return {
                    "stdout": f"⚠️  WARNING: {confirm_reason}\n🔍 Command: {command}\n❓ Are you sure you want to run this? (y/n): ",
                    "stderr": "",
                    "exit_code": 0
                }
            
            # Try bash first
            if self.bash_executor:
                exit_code, stdout, stderr = await self.bash_executor.execute(command)
                
                # Interactive commands - always return directly (no AI processing)
                if self._is_interactive_command(command):
                    return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code}
                
                # Clean success (exit 0, has stdout, no stderr) - bypass AI
                if exit_code == 0 and stdout and not stderr:
                    return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code}
                
                # Command failed - send to AI if ready (after filtering sensitive data)
                if self.ai_ready:
                    # Filter sensitive data from command output before sending to AI
                    filtered_stdout = self.sensitive_filter.filter_command_output(command, stdout)
                    filtered_stderr = self.sensitive_filter.filter_command_output(command, stderr)
                    
                    bash_result = {"stdout": filtered_stdout, "stderr": filtered_stderr, "exit_code": exit_code}
                    return await self._handle_ai_prompt(command, bash_result)
                else:
                    # AI not ready - show bash output + hint
                    return {
                        "stdout": stdout, 
                        "stderr": stderr + "💡 AI not ready yet - this might be a natural language query\n", 
                        "exit_code": exit_code
                    }
            else:
                # No bash executor - AI handles everything
                return await self._handle_ai_prompt(command)
                
        except Exception as e:
            return {"stdout": "", "stderr": f"Backend error: {e}\n", "exit_code": 1}
    
    async def _handle_confirmation_response(self, response: str) -> dict:
        """Handle user confirmation response (y/n)"""
        if not self.pending_confirmation:
            return {
                "stdout": "No command pending confirmation.\n",
                "stderr": "",
                "exit_code": 0
            }
        
        response_lower = response.lower().strip()
        command = self.pending_confirmation
        self.pending_confirmation = None
        
        if response_lower in ['y', 'yes']:
            # User confirmed - execute the command
            try:
                if self.bash_executor:
                    exit_code, stdout, stderr = await self.bash_executor.execute(command)
                    return {
                        "stdout": f"✅ Executed: {command}\n{stdout}",
                        "stderr": stderr,
                        "exit_code": exit_code
                    }
                else:
                    return {
                        "stdout": "Bash executor not available.\n",
                        "stderr": "",
                        "exit_code": 1
                    }
            except Exception as e:
                return {
                    "stdout": "",
                    "stderr": f"Error executing command: {e}\n",
                    "exit_code": 1
                }
        else:
            # User cancelled
            return {
                "stdout": f"❌ Cancelled: {command}\n",
                "stderr": "",
                "exit_code": 0
            }
    
    async def _handle_ai_prompt(self, prompt: str, bash_result: dict = None) -> dict:
        """Let AI process everything - all bash output goes through AI first"""
        if not self.ai_ready:
            return {"stdout": "🔄 AI still loading...\n", "stderr": "", "exit_code": 0}
        
        try:
            # Give AI full context: command + all bash output
            if bash_result:
                ai_input = f"""User command: {prompt}
Bash result:
- Exit code: {bash_result.get('exit_code', 0)}
- Stdout: {bash_result.get('stdout', '')}
- Stderr: {bash_result.get('stderr', '')}

Process this and respond appropriately."""
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
