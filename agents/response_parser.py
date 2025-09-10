"""
Response Parser for AIOps System

Implements vi-like modal system for AI responses:
- Command Mode: `awesh: <commands>` - for executable commands
- Edit Mode: `awesh: <edit>` - for information display only

This allows the AI to clearly distinguish between what should be executed
and what should be displayed to the user.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ResponseMode(Enum):
    """Response modes for AI output"""
    COMMAND = "command"  # Executable commands
    EDIT = "edit"        # Information display only
    MIXED = "mixed"      # Both command and edit content


@dataclass
class ParsedResponse:
    """Parsed AI response with mode classification"""
    mode: ResponseMode
    commands: List[str]  # Commands to execute
    edit_content: str    # Content to display
    raw_response: str    # Original response
    metadata: Dict[str, Any]


class ResponseParser:
    """
    Parser for AI responses using vi-like modal system.
    
    The AI can respond in two modes:
    1. Command Mode: `awesh: <commands>` - Commands to execute
    2. Edit Mode: `awesh: <edit>` - Information to display
    
    This provides clear separation between executable actions and informational content.
    """
    
    def __init__(self):
        # Patterns for different response modes
        self.command_pattern = re.compile(r'awesh:\s*<commands?>\s*(.*?)(?=awesh:|$)', re.DOTALL | re.IGNORECASE)
        self.edit_pattern = re.compile(r'awesh:\s*<edit>\s*(.*?)(?=awesh:|$)', re.DOTALL | re.IGNORECASE)
        
        # Legacy pattern for backward compatibility
        self.legacy_command_pattern = re.compile(r'awesh:\s*(.*?)(?=awesh:|$)', re.DOTALL | re.IGNORECASE)
    
    def parse_response(self, response: str) -> ParsedResponse:
        """
        Parse AI response and classify into command/edit modes.
        
        Args:
            response: Raw AI response text
            
        Returns:
            ParsedResponse with mode classification and extracted content
        """
        response = response.strip()
        
        # Extract command blocks
        command_blocks = self.command_pattern.findall(response)
        commands = []
        for block in command_blocks:
            # Split commands by newlines and clean them
            block_commands = [cmd.strip() for cmd in block.split('\n') if cmd.strip()]
            commands.extend(block_commands)
        
        # Extract edit blocks
        edit_blocks = self.edit_pattern.findall(response)
        edit_content = '\n\n'.join(edit_blocks).strip()
        
        # Determine mode
        if commands and edit_content:
            mode = ResponseMode.MIXED
        elif commands:
            mode = ResponseMode.COMMAND
        elif edit_content:
            mode = ResponseMode.EDIT
        else:
            # Fallback to legacy parsing
            return self._parse_legacy_response(response)
        
        return ParsedResponse(
            mode=mode,
            commands=commands,
            edit_content=edit_content,
            raw_response=response,
            metadata={
                "command_count": len(commands),
                "has_edit_content": bool(edit_content),
                "parsing_method": "modal"
            }
        )
    
    def _parse_legacy_response(self, response: str) -> ParsedResponse:
        """
        Parse legacy responses that don't use the modal system.
        
        This provides backward compatibility for existing AI responses.
        """
        # Look for legacy awesh: commands
        legacy_commands = self.legacy_command_pattern.findall(response)
        commands = []
        for block in legacy_commands:
            # Split commands by newlines and clean them
            block_commands = [cmd.strip() for cmd in block.split('\n') if cmd.strip()]
            commands.extend(block_commands)
        
        # Remove command blocks from response to get edit content
        edit_content = self.legacy_command_pattern.sub('', response).strip()
        
        # Determine mode
        if commands and edit_content:
            mode = ResponseMode.MIXED
        elif commands:
            mode = ResponseMode.COMMAND
        else:
            mode = ResponseMode.EDIT
            edit_content = response  # Use entire response as edit content
        
        return ParsedResponse(
            mode=mode,
            commands=commands,
            edit_content=edit_content,
            raw_response=response,
            metadata={
                "command_count": len(commands),
                "has_edit_content": bool(edit_content),
                "parsing_method": "legacy"
            }
        )
    
    def format_ai_instructions(self) -> str:
        """
        Get instructions for AI on how to use the modal system.
        
        Returns:
            Instructions string for AI system prompt
        """
        return """
RESPONSE MODAL SYSTEM:

You can respond in two distinct modes:

1. COMMAND MODE - For executable commands:
   Use: awesh: <commands>
   Example:
   awesh: <commands>
   ls -la
   cd /tmp
   pwd

2. EDIT MODE - For information display only:
   Use: awesh: <edit>
   Example:
   awesh: <edit>
   Here's the analysis of your system:
   - CPU usage is at 45%
   - Memory usage is at 78%
   - Disk space is running low

3. MIXED MODE - For both commands and information:
   awesh: <commands>
   systemctl status nginx
   
   awesh: <edit>
   The nginx service is running. Here's what I found:
   - Service is active and enabled
   - Listening on port 80 and 443
   - Configuration looks correct

IMPORTANT:
- Commands in <commands> blocks will be executed
- Content in <edit> blocks will be displayed to the user
- Use <edit> for explanations, analysis, and informational content
- Use <commands> only for actual executable commands
- You can mix both modes in a single response
"""
    
    def validate_commands(self, commands: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate commands and separate valid from invalid ones.
        
        Args:
            commands: List of commands to validate
            
        Returns:
            Tuple of (valid_commands, invalid_commands)
        """
        valid_commands = []
        invalid_commands = []
        
        for command in commands:
            command = command.strip()
            if not command:
                continue
                
            # Basic validation
            if self._is_valid_command(command):
                valid_commands.append(command)
            else:
                invalid_commands.append(command)
        
        return valid_commands, invalid_commands
    
    def _is_valid_command(self, command: str) -> bool:
        """
        Basic validation for commands.
        
        Args:
            command: Command to validate
            
        Returns:
            True if command appears valid
        """
        # Skip empty commands
        if not command.strip():
            return False
        
        # Skip comments
        if command.strip().startswith('#'):
            return False
        
        # Skip obvious non-commands
        if command.strip().startswith('//') or command.strip().startswith('/*'):
            return False
        
        # Basic checks
        if len(command) > 1000:  # Too long
            return False
        
        # Must have at least one non-whitespace character
        if not command.strip():
            return False
        
        return True
    
    def extract_commands_for_execution(self, response: str) -> List[str]:
        """
        Extract only the commands that should be executed.
        
        Args:
            response: AI response text
            
        Returns:
            List of commands to execute
        """
        parsed = self.parse_response(response)
        valid_commands, _ = self.validate_commands(parsed.commands)
        return valid_commands
    
    def extract_display_content(self, response: str) -> str:
        """
        Extract content that should be displayed to the user.
        
        Args:
            response: AI response text
            
        Returns:
            Content to display to user
        """
        parsed = self.parse_response(response)
        return parsed.edit_content
    
    def get_response_summary(self, response: str) -> Dict[str, Any]:
        """
        Get a summary of the parsed response.
        
        Args:
            response: AI response text
            
        Returns:
            Summary dictionary
        """
        parsed = self.parse_response(response)
        valid_commands, invalid_commands = self.validate_commands(parsed.commands)
        
        return {
            "mode": parsed.mode.value,
            "total_commands": len(parsed.commands),
            "valid_commands": len(valid_commands),
            "invalid_commands": len(invalid_commands),
            "has_edit_content": bool(parsed.edit_content),
            "edit_content_length": len(parsed.edit_content),
            "parsing_method": parsed.metadata.get("parsing_method", "unknown"),
            "commands": valid_commands,
            "invalid_commands": invalid_commands
        }
