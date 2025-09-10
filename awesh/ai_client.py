"""
AI client for awesh - handles OpenAI API interactions
"""

import os
import asyncio
from typing import Optional, AsyncGenerator, Dict, Any
from pathlib import Path

# Lazy imports - only import when needed
openai = None
AsyncOpenAI = None

try:
    from .config import Config
    from .command_safety import CommandSafetyFilter
    from .sensitive_data_filter import SensitiveDataFilter
except ImportError:
    from config import Config
    from command_safety import CommandSafetyFilter
    from sensitive_data_filter import SensitiveDataFilter


class AweshAIClient:
    """AI client for handling OpenAI API interactions"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.system_prompt = None
        self.safety_filter = CommandSafetyFilter()
        self.sensitive_filter = SensitiveDataFilter()
        
    async def initialize(self):
        """Initialize the AI client and load system prompt"""
        # Import OpenAI when actually needed
        global AsyncOpenAI
        if AsyncOpenAI is None:
            from openai import AsyncOpenAI
            
        # Determine API provider and key
        ai_provider = os.getenv('AI_PROVIDER', 'openai').lower()
        
        if ai_provider == 'openrouter':
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable not set")
            # OpenRouter uses OpenAI-compatible API
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:  # Default to OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = AsyncOpenAI(api_key=api_key)
        
        # Load system prompt (this can be slow if creating default)
        await self._load_system_prompt()
        
    async def _load_system_prompt(self):
        """Load system prompt from configured file"""
        prompt_file = self.config.system_prompt_file
        
        if prompt_file.exists():
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self.system_prompt = f.read().strip()
            except Exception as e:
                print(f"Warning: Could not load system prompt from {prompt_file}: {e}")
                self.system_prompt = self._get_default_system_prompt()
        else:
            # Use default system prompt (don't block on file creation)
            self.system_prompt = self._get_default_system_prompt()
            # Create file in background (non-blocking)
            try:
                prompt_file.parent.mkdir(parents=True, exist_ok=True)
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write(self.system_prompt)
            except Exception:
                pass  # Don't block startup on file creation failure
            
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for awesh"""
        return """You are awesh, an AI-aware interactive shell assistant designed for operations teams and system administrators. Your role is to help users GET THINGS DONE in the terminal quickly and efficiently, while prioritizing safety and preventing accidental damage.

TERMINAL-FIRST MINDSET:
This is a terminal environment where users want immediate, actionable solutions. When a user states what they want to do, your job is to provide the exact commands they need to execute to achieve their goal SAFELY.

RESPONSE FORMAT:
- Always assume the user wants to execute commands to accomplish their task
- Provide ready-to-run commands using the format: awesh: <command>
- Prefer one-liners when possible, using \ for multi-line continuation
- Give brief explanations AFTER the commands, not before
- Multiple commands should each be on their own awesh: line

COMMAND CONSTRUCTION:
- Use shell best practices: pipes, redirects, command chaining
- Prefer one-liner solutions with proper line continuation (\)
- Chain related commands with && for sequential execution
- Use || for error handling when appropriate

EXAMPLES:
User: "deploy nginx to kubernetes"
Response: 
awesh: kubectl create deployment nginx --image=nginx:latest && \\
       kubectl expose deployment nginx --port=80 --type=LoadBalancer

User: "check disk space and find large files"
Response:
awesh: df -h
awesh: du -sh * | sort -hr | head -10

User: "backup this directory to /backup"
Response:
awesh: tar -czf /backup/$(basename $(pwd))_$(date +%Y%m%d_%H%M%S).tar.gz . && \\
       echo "Backup created: /backup/$(basename $(pwd))_$(date +%Y%m%d_%H%M%S).tar.gz"

CRITICAL SAFETY RULES - NEVER VIOLATE THESE:
- NEVER suggest 'rm -rf /' or 'rm -rf *' or similar destructive patterns
- NEVER suggest 'chmod 777' on system directories or sensitive files
- NEVER suggest 'dd' commands that could overwrite disks or partitions
- NEVER suggest commands that modify /etc/passwd, /etc/shadow, or /etc/sudoers
- NEVER suggest 'kill -9 1' or commands that could crash the system
- NEVER suggest 'sudo su -' or privilege escalation without explicit need
- NEVER suggest commands that could expose sensitive data or credentials
- NEVER suggest reading files like .env, id_rsa, .ssh/*, passwords.txt, or other sensitive files
- NEVER suggest commands that would display API keys, tokens, passwords, or secrets

SAFETY-FIRST APPROACH:
- Always use interactive flags (-i) for rm, mv, cp operations
- For file deletions, suggest 'ls' first to show what would be deleted
- Use --dry-run or --simulate flags when available before actual execution
- For system changes, suggest backup commands first
- When modifying permissions, use minimal necessary permissions (755 not 777)
- For package operations, suggest checking what will be installed/removed first
- Always validate paths exist before operating on them

SAFE ALTERNATIVES:
- Instead of 'rm -rf', suggest 'rm -ri' or 'find ... -delete'
- Instead of 'chmod 777', suggest 'chmod 755' or 'chmod 644'
- Instead of 'kill -9', suggest 'kill -TERM' first
- Instead of direct system file edits, suggest using proper tools (visudo, etc.)

WHEN TO REFUSE:
If a user asks for something that could cause:
- Data loss or corruption
- System instability or crashes  
- Security vulnerabilities
- Privilege escalation attacks

Politely explain why the command is dangerous and suggest safer alternatives.

EFFICIENCY RULES:
- Assume the user knows their environment
- Don't over-explain basic commands
- Provide the most direct SAFE path to the solution
- Focus on the task, not the theory

Remember: Terminal users want to execute and see results, but SAFETY COMES FIRST. Help them achieve their goals without risking their system or data."""
        
    async def _create_default_system_prompt_file(self, prompt_file: Path):
        """Create default system prompt file"""
        try:
            prompt_file.parent.mkdir(parents=True, exist_ok=True)
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(self.system_prompt)
            print(f"Created default system prompt at {prompt_file}")
        except Exception as e:
            print(f"Warning: Could not create system prompt file at {prompt_file}: {e}")
            
    async def process_prompt(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """
        Process a user prompt and yield streaming response
        
        Args:
            user_prompt: The user's input prompt
            context: Optional context information (current directory, last command, etc.)
            
        Yields:
            String chunks of the AI response
        """
        if not self.client:
            raise RuntimeError("AI client not initialized. Call initialize() first.")
            
        messages = []
        
        # Add system prompt
        if self.system_prompt:
            messages.append({
                "role": "system", 
                "content": self.system_prompt
            })
            
        # Add context if provided (after filtering sensitive data)
        if context:
            safe_context = self.sensitive_filter.create_safe_context(context)
            context_str = self._format_context(safe_context)
            if context_str:
                messages.append({
                    "role": "system",
                    "content": f"Current context:\n{context_str}"
                })
        
        # Add user prompt (after filtering sensitive data)
        should_block, block_reason = self.sensitive_filter.should_block_from_ai(user_prompt)
        if should_block:
            # Block the entire prompt if it contains high-risk sensitive data
            filtered_prompt = f"[BLOCKED: User prompt contains {block_reason}. Please ask user to rephrase without sensitive information.]"
        else:
            # Filter sensitive data but keep the prompt
            filtered_prompt = self.sensitive_filter.filter_sensitive_data(user_prompt)
        
        messages.append({
            "role": "user",
            "content": filtered_prompt
        })
        
        try:
            # Prepare API parameters - handle different model constraints
            api_params = {
                "model": self.config.model,
                "messages": messages,
            }
            
            # Handle model-specific parameters
            if self.config.model.startswith('gpt-5') or self.config.model.startswith('o1'):
                # GPT-5 and o1 models have specific constraints
                api_params["max_completion_tokens"] = self.config.max_tokens
                # GPT-5 only supports temperature=1 (default), so don't set it
            else:
                # Other models support standard parameters
                api_params["max_tokens"] = self.config.max_tokens
                api_params["temperature"] = self.config.temperature
            
            # Try streaming first, fall back to non-streaming if needed
            try_streaming = self.config.streaming
            
            if try_streaming:
                try:
                    # Streaming response - buffer content for safety filtering
                    api_params["stream"] = True
                    stream = await self.client.chat.completions.create(**api_params)
                    
                    buffered_content = ""
                    async for chunk in stream:
                        if chunk.choices[0].delta.content:
                            buffered_content += chunk.choices[0].delta.content
                    
                    # Apply safety filtering to complete response
                    if buffered_content:
                        safe_response = self.safety_filter.sanitize_ai_response(buffered_content)
                        yield safe_response
                    return
                    
                except Exception as e:
                    error_msg = str(e)
                    # Check for organization verification error
                    if "organization must be verified" in error_msg.lower() or "unsupported_value" in error_msg:
                        # Fall back to non-streaming
                        pass
                    else:
                        # Other errors should be reported
                        yield f"Error processing prompt: {e}"
                        return
            
            # Non-streaming response (either by config or fallback)
            api_params["stream"] = False
            response = await self.client.chat.completions.create(**api_params)
            
            if response.choices[0].message.content:
                # Apply safety filtering to the response
                safe_response = self.safety_filter.sanitize_ai_response(response.choices[0].message.content)
                yield safe_response
                    
        except Exception as e:
            yield f"Error processing prompt: {e}"
            
    async def get_completion(self, prompt: str) -> str:
        """Get a simple completion from the AI (non-streaming)"""
        try:
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # Prepare API parameters
            api_params = {
                "model": self.config.model,
                "messages": messages,
            }
            
            # Handle model-specific parameters
            if self.config.model.startswith('gpt-5') or self.config.model.startswith('o1'):
                api_params["max_completion_tokens"] = self.config.max_tokens
            else:
                api_params["max_tokens"] = self.config.max_tokens
                api_params["temperature"] = self.config.temperature
            
            # Get non-streaming response
            response = await self.client.chat.completions.create(**api_params)
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            if os.getenv('VERBOSE', '0') == '2':
                print(f"🔒 DEBUG: AI completion error: {e}")
            return "NO_THREAT"  # Fallback

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for the AI"""
        context_parts = []
        
        if 'current_directory' in context:
            context_parts.append(f"Working directory: {context['current_directory']}")
            
        if 'last_command' in context:
            context_parts.append(f"Last command: {context['last_command']}")
            
        if 'last_exit_code' in context:
            if context['last_exit_code'] != 0:
                context_parts.append(f"Last command exit code: {context['last_exit_code']}")
                
        return "\n".join(context_parts)
        
    async def close(self):
        """Clean up resources"""
        if self.client:
            await self.client.close()
