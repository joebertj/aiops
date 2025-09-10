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
# Bash execution moved to C frontend for better performance
from command_safety import CommandSafetyFilter
from sensitive_data_filter import SensitiveDataFilter

# Import agent system (Security Agent now in C)
from agents import (
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
        # Bash execution moved to C frontend
        self.ai_ready = False
        self.safety_filter = CommandSafetyFilter()
        self.sensitive_filter = SensitiveDataFilter()
        self.pending_confirmation = None  # Store command awaiting confirmation
        
        # Initialize agent system
        self.agent_processor = None
        
        # Security Agent communication (C process)
        self.security_agent_socket = None
        
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
            
            # Bash execution handled by C frontend
            
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
            # Create agents in priority order (Security Agent now in C)
            agents = [
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
    
    def _connect_to_security_agent(self):
        """Connect to C Security Agent"""
        try:
            home = os.path.expanduser("~")
            socket_path = f"{home}/.awesh_security_agent.sock"
            
            self.security_agent_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.security_agent_socket.connect(socket_path)
            return True
        except Exception as e:
            if os.getenv('VERBOSE', '0') == '2':
                print(f"🔒 DEBUG: Security Agent connection failed: {e}")
            return False
    
    def _request_security_clearance(self, prompt):
        """Request security clearance from C Security Agent"""
        if not self.security_agent_socket:
            if not self._connect_to_security_agent():
                return prompt  # Fallback to original prompt
        
        try:
            # Send security check request
            request = f"SECURITY_CHECK:{prompt}"
            self.security_agent_socket.send(request.encode())
            
            # Read response
            response = self.security_agent_socket.recv(4096).decode()
            
            if response.startswith("SECURITY_OK:"):
                return response[12:]  # Return filtered prompt
            elif response.startswith("SECURITY_BLOCKED:"):
                return response[17:]  # Return blocked message
            else:
                return prompt  # Fallback
                
        except Exception as e:
            if os.getenv('VERBOSE', '0') == '2':
                print(f"🔒 DEBUG: Security Agent communication failed: {e}")
            return prompt  # Fallback
    
    async def _handle_process_analysis(self, ps_output: str) -> str:
        """Use AI to analyze process output for suspicious activity"""
        if not self.ai_ready:
            return "NO_THREAT"  # No AI available, assume no threat
        
        try:
            # Create AI prompt for process analysis
            ai_prompt = f"""Analyze this process list for suspicious or malicious activity. Look for:
- Processes with suspicious names (rogue, malware, virus, etc.)
- Unusual process behavior patterns
- Processes that might be security threats
- Any processes that seem out of place

Process list:
{ps_output}

Respond with:
- "THREAT_DETECTED: [description]" if you find suspicious processes
- "NO_THREAT" if everything looks normal

Be thorough but concise. Focus on actual security threats."""

            # Get AI response
            response = await self.ai_client.get_completion(ai_prompt)
            
            # Parse response
            if "THREAT_DETECTED:" in response:
                return response.strip()
            else:
                return "NO_THREAT"
                
        except Exception as e:
            if os.getenv('VERBOSE', '0') == '2':
                print(f"🔒 DEBUG: Process analysis AI error: {e}")
            return "NO_THREAT"  # Fallback to no threat
    
    # Interactive command detection moved to C frontend
    
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
            
            # Send directly to AI agents (bash commands handled by C frontend)
            if self.ai_ready:
                return await self._handle_ai_prompt(command)
            else:
                return {
                    "stdout": "", 
                    "stderr": "💡 AI not ready yet - this might be a natural language query\n", 
                    "exit_code": 1
                }
                
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
                # Bash execution handled by C frontend
                return {
                    "stdout": f"✅ Command confirmed: {command}\n(Execution handled by C frontend)",
                    "stderr": "",
                    "exit_code": 0
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
    
    async def process_ai_query(self, query: str) -> str:
        """Process AI query for mode detection"""
        try:
            # Request security clearance from C Security Agent
            cleared_query = self._request_security_clearance(query)
            
            # Use agent system to process the query
            if self.agent_processor:
                result = await self.agent_processor.process_prompt(cleared_query, {})
                if result.handled:
                    return result.response
            
            # Fallback to direct AI processing
            if self.ai_client:
                # Determine if this should be command or edit mode
                mode_prompt = f"""Determine if this user input should be executed as a command or displayed as informational content.

User input: "{query}"

Respond with exactly one of these formats:
- awesh_cmd: <command> - if this should be executed as a shell command
- awesh_edit: <content> - if this should be displayed as informational content

Examples:
- "ls -la" → awesh_cmd: ls -la
- "write a poem about cats" → awesh_edit: Here's a poem about cats: [poem content]
- "what is docker" → awesh_edit: Docker is a containerization platform that...
- "kill process 123" → awesh_cmd: kill 123

Your response:"""
                
                response = ""
                async for chunk in self.ai_client.process_prompt(mode_prompt):
                    response += chunk
                
                return response.strip()
            
            return "awesh_edit: AI not available"
            
        except Exception as e:
            return f"awesh_edit: Error processing query: {e}"
    
    async def get_process_status(self) -> str:
        """Get process agent status for prompt display"""
        try:
            if self.agent_processor:
                # Find ProcessAgent in the agent list
                for agent in self.agent_processor.agents:
                    if hasattr(agent, 'name') and agent.name == "ProcessAgent":
                        # Get threat status from ProcessAgent
                        if hasattr(agent, 'get_prompt_status'):
                            status = agent.get_prompt_status()
                            if status:
                                return f"THREAT:{status}"
                        break
            
            return "✅ No threats detected"
            
        except Exception as e:
            return f"🔍 Process monitoring error: {e}"


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
                
            line = line.strip()
            
            # Handle QUERY commands (AI mode detection)
            if line.startswith("QUERY:"):
                query = line[6:]  # Remove "QUERY:" prefix
                try:
                    # Process with AI for mode detection
                    response = await backend.process_ai_query(query)
                    sys.stdout.write(response + "\n")
                    sys.stdout.flush()
                    continue
                except Exception as e:
                    sys.stdout.write(f"❌ AI query error: {e}\n")
                    sys.stdout.flush()
                    continue
            
            # Handle PROCESS_STATUS commands
            if line == "PROCESS_STATUS":
                try:
                    # Get process agent status
                    response = await backend.get_process_status()
                    sys.stdout.write(response + "\n")
                    sys.stdout.flush()
                    continue
                except Exception as e:
                    sys.stdout.write(f"❌ Process status error: {e}\n")
                    sys.stdout.flush()
                    continue
            
            # Parse JSON command
            try:
                data = json.loads(line)
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
