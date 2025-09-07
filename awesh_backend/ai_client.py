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

from .config import Config


class AweshAIClient:
    """AI client for handling OpenAI API interactions"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.system_prompt = None
        
    async def initialize(self):
        """Initialize the AI client and load system prompt"""
        # Import OpenAI when actually needed
        global AsyncOpenAI
        if AsyncOpenAI is None:
            from openai import AsyncOpenAI
            
        # Initialize OpenAI client
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
        return """You are awesh, an AI-aware interactive shell assistant. Your role is to help users with their computing tasks through natural language interaction.

Key principles:
- Be concise and practical in your responses
- When users ask about files, directories, or system state, suggest specific commands they can run
- If a task requires multiple steps, break it down clearly
- Always prioritize accuracy and safety
- If you're unsure about a command's safety, warn the user and suggest alternatives
- Remember that the user is in an interactive shell environment where they can run commands immediately

You have access to the current working directory and can suggest commands based on the user's context. The user can seamlessly switch between talking to you and running bash commands."""
        
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
            
        # Add context if provided
        if context:
            context_str = self._format_context(context)
            if context_str:
                messages.append({
                    "role": "system",
                    "content": f"Current context:\n{context_str}"
                })
        
        # Add user prompt
        messages.append({
            "role": "user",
            "content": user_prompt
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
                    # Streaming response
                    api_params["stream"] = True
                    if __import__('os').getenv('VERBOSE') == '1':
                        print(f"🔧 AI Client: Starting streaming request with model {self.config.model}", file=__import__('sys').stderr)
                    stream = await self.client.chat.completions.create(**api_params)
                    
                    chunk_count = 0
                    content_chunks = 0
                    async for chunk in stream:
                        chunk_count += 1
                        if chunk.choices[0].delta.content:
                            content_chunks += 1
                            if __import__('os').getenv('VERBOSE') == '1':
                                print(f"🔧 AI Client: Yielding chunk {content_chunks}: '{chunk.choices[0].delta.content[:50]}...'", file=__import__('sys').stderr)
                            yield chunk.choices[0].delta.content
                        else:
                            if __import__('os').getenv('VERBOSE') == '1':
                                print(f"🔧 AI Client: Empty chunk {chunk_count} (no content)", file=__import__('sys').stderr)
                    
                    if __import__('os').getenv('VERBOSE') == '1':
                        print(f"🔧 AI Client: Streaming complete - {chunk_count} total chunks, {content_chunks} with content", file=__import__('sys').stderr)
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
            if __import__('os').getenv('VERBOSE') == '1':
                print(f"🔧 AI Client: Using non-streaming request with model {self.config.model}", file=__import__('sys').stderr)
            response = await self.client.chat.completions.create(**api_params)
            
            content = response.choices[0].message.content
            if __import__('os').getenv('VERBOSE') == '1':
                print(f"🔧 AI Client: Non-streaming response length: {len(content) if content else 0} chars", file=__import__('sys').stderr)
            if content:
                if __import__('os').getenv('VERBOSE') == '1':
                    print(f"🔧 AI Client: Non-streaming preview: '{content[:100]}...'", file=__import__('sys').stderr)
                yield content
            else:
                if __import__('os').getenv('VERBOSE') == '1':
                    print(f"🔧 AI Client: ❌ Non-streaming response is empty!", file=__import__('sys').stderr)
                    
        except Exception as e:
            yield f"Error processing prompt: {e}"
            
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
