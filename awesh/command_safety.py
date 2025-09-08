"""
Simple command safety filter for awesh
Prevents AI from suggesting dangerous/destructive commands
"""

import re
from typing import Tuple, List, Optional


class CommandSafetyFilter:
    """Filters dangerous commands from AI suggestions"""
    
    def __init__(self):
        # Destructive commands that should never be suggested by AI
        self.forbidden_commands = {
            # File system destruction
            'rm -rf /', 'rm -rf *', 'rm -rf ~', 'rm -rf .*',
            'rmdir -rf', 'find . -delete', 'find / -delete',
            
            # System modification
            'chmod 777 /', 'chmod -R 777', 'chown -R root',
            'dd if=/dev/zero', 'dd if=/dev/urandom', 'mkfs',
            
            # Process/system control
            'kill -9 1', 'killall -9', 'pkill -9', 'init 0', 'init 6',
            'shutdown', 'reboot', 'halt', 'poweroff',
            
            # Network/security
            'iptables -F', 'ufw --force', 'passwd root',
            'sudo su -', 'sudo -i', 'su -',
            
            # Package management (potentially destructive)
            'apt-get remove --purge', 'yum remove', 'dnf remove',
            'pip uninstall', 'npm uninstall -g'
        }
        
        # Commands that require confirmation
        self.requires_confirmation = {
            # File operations
            'rm', 'rmdir', 'mv', 'cp -r', 'rsync --delete',
            
            # Permissions
            'chmod', 'chown', 'chgrp',
            
            # System services
            'systemctl stop', 'systemctl disable', 'service stop',
            
            # Process management
            'kill', 'killall', 'pkill',
            
            # Package operations
            'apt-get install', 'yum install', 'dnf install',
            'pip install', 'npm install -g'
        }
        
        # Dangerous patterns (regex)
        self.dangerous_patterns = [
            r'rm\s+-rf\s+/',           # rm -rf /anything
            r'rm\s+-rf\s+\*',          # rm -rf *
            r'rm\s+-rf\s+~',           # rm -rf ~
            r'chmod\s+777',            # chmod 777
            r'chmod\s+-R\s+777',       # chmod -R 777
            r'dd\s+if=.*of=/dev/',     # dd to device
            r'find\s+/.*-delete',      # find with delete
            r'>\s*/dev/sd[a-z]',       # redirect to disk device
            r'mkfs\.',                 # make filesystem
            r'fdisk\s+/dev/',          # disk partitioning
            r'kill\s+-9\s+1\b',        # kill init
            r'sudo\s+rm\s+-rf',       # sudo rm -rf
            r'sudo\s+dd',              # sudo dd
            r'curl.*\|\s*sh',          # curl | sh (dangerous downloads)
            r'wget.*\|\s*sh',          # wget | sh
            r':\(\)\{\s*:\|:&\s*\};:', # fork bomb
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns]

    def is_command_safe(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a command is safe for AI to suggest
        
        Args:
            command: The command to check
            
        Returns:
            Tuple of (is_safe, reason_if_unsafe)
        """
        command = command.strip()
        
        # Check against forbidden commands
        for forbidden in self.forbidden_commands:
            if command.lower().startswith(forbidden.lower()):
                return False, f"Forbidden command: {forbidden}"
        
        # Check against dangerous patterns
        for pattern in self.compiled_patterns:
            if pattern.search(command):
                return False, f"Matches dangerous pattern: {pattern.pattern}"
        
        return True, None

    def requires_confirmation(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a command requires user confirmation
        
        Args:
            command: The command to check
            
        Returns:
            Tuple of (requires_confirmation, reason)
        """
        command_lower = command.lower().strip()
        
        # Check if command starts with any that require confirmation
        for confirm_cmd in self.requires_confirmation:
            if command_lower.startswith(confirm_cmd.lower()):
                return True, f"Potentially destructive command: {confirm_cmd}"
        
        # Additional checks for specific patterns
        if 'rm' in command_lower and ('-r' in command_lower or '-f' in command_lower):
            return True, "Recursive or forced file deletion"
        
        if 'chmod' in command_lower and ('777' in command or '666' in command):
            return True, "Setting overly permissive permissions"
        
        if 'sudo' in command_lower:
            return True, "Command requires elevated privileges"
        
        return False, None

    def sanitize_ai_response(self, ai_response: str) -> str:
        """
        Sanitize AI response to add safety warnings and confirmations
        
        Args:
            ai_response: The AI's response containing commands
            
        Returns:
            Sanitized response with safety measures
        """
        lines = ai_response.split('\n')
        sanitized_lines = []
        
        for line in lines:
            # Look for command lines (starting with awesh:)
            if line.strip().startswith('awesh:'):
                command = line.strip()[6:].strip()  # Remove 'awesh:' prefix
                
                # Check if command is safe
                is_safe, unsafe_reason = self.is_command_safe(command)
                if not is_safe:
                    sanitized_lines.append(f"⚠️  BLOCKED: {unsafe_reason}")
                    sanitized_lines.append(f"❌ awesh: # {command}  # COMMAND BLOCKED FOR SAFETY")
                    continue
                
                # Check if command requires confirmation
                needs_confirm, confirm_reason = self.requires_confirmation(command)
                if needs_confirm:
                    sanitized_lines.append(f"⚠️  WARNING: {confirm_reason}")
                    sanitized_lines.append(f"🔍 awesh: {command}")
                    sanitized_lines.append("❓ Would you like me to run this command? (y/n)")
                    continue
            
            # Regular line, pass through
            sanitized_lines.append(line)
        
        return '\n'.join(sanitized_lines)

    def extract_commands_from_response(self, ai_response: str) -> List[str]:
        """
        Extract all commands from AI response
        
        Args:
            ai_response: The AI's response
            
        Returns:
            List of commands found in the response
        """
        commands = []
        lines = ai_response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('awesh:'):
                command = line[6:].strip()  # Remove 'awesh:' prefix
                if command and not command.startswith('#'):  # Skip comments
                    commands.append(command)
        
        return commands

    def get_safe_alternative(self, dangerous_command: str) -> Optional[str]:
        """
        Suggest a safer alternative to a dangerous command
        
        Args:
            dangerous_command: The dangerous command
            
        Returns:
            Safer alternative or None
        """
        cmd_lower = dangerous_command.lower().strip()
        
        # Safe alternatives for common dangerous commands
        alternatives = {
            'rm -rf': 'rm -i',  # Interactive delete
            'chmod 777': 'chmod 755',  # More restrictive permissions
            'chmod -R 777': 'chmod -R 755',
            'dd if=/dev/zero': '# Use truncate or fallocate instead',
            'kill -9': 'kill -TERM',  # Graceful termination first
            'shutdown': 'shutdown -h +5',  # Give time to cancel
            'reboot': 'reboot --help  # Add delay with: shutdown -r +5',
        }
        
        for dangerous, safe in alternatives.items():
            if cmd_lower.startswith(dangerous):
                return safe
        
        return None

    def is_command_reversible(self, command: str) -> bool:
        """
        Check if a command's effects can be easily reversed
        
        Args:
            command: The command to check
            
        Returns:
            True if command is easily reversible
        """
        cmd_lower = command.lower().strip()
        
        # Irreversible operations
        irreversible = [
            'rm', 'rmdir', 'dd', 'mkfs', 'fdisk', 'parted',
            'kill', 'killall', 'pkill', 'shutdown', 'reboot',
            'halt', 'poweroff', 'init'
        ]
        
        for irreversible_cmd in irreversible:
            if cmd_lower.startswith(irreversible_cmd):
                return False
        
        return True
