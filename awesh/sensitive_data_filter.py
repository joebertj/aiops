"""
Sensitive data filter for awesh
Prevents sensitive information from being sent to AI as context
"""

import re
from typing import Tuple, List, Optional, Dict, Any


class SensitiveDataFilter:
    """Filters sensitive data from being sent to AI"""
    
    def __init__(self):
        # Patterns for sensitive data detection
        self.sensitive_patterns = [
            # API Keys and Tokens
            (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*[\'"]?([a-zA-Z0-9_\-]{20,})[\'"]?', 'API key'),
            (r'(?i)(access[_-]?token|accesstoken)\s*[=:]\s*[\'"]?([a-zA-Z0-9_\-]{20,})[\'"]?', 'Access token'),
            (r'(?i)(bearer\s+)([a-zA-Z0-9_\-\.]{20,})', 'Bearer token'),
            (r'(?i)(token)\s*[=:]\s*[\'"]?([a-zA-Z0-9_\-]{20,})[\'"]?', 'Token'),
            
            # AWS/Cloud Keys
            (r'(AKIA[0-9A-Z]{16})', 'AWS Access Key ID'),
            (r'([0-9a-zA-Z/+]{40})', 'AWS Secret Access Key pattern'),
            (r'(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*[=:]\s*[\'"]?([a-zA-Z0-9/+=]{40})[\'"]?', 'AWS Secret'),
            
            # GitHub/Git tokens
            (r'(ghp_[a-zA-Z0-9]{36})', 'GitHub Personal Access Token'),
            (r'(gho_[a-zA-Z0-9]{36})', 'GitHub OAuth Token'),
            (r'(ghu_[a-zA-Z0-9]{36})', 'GitHub User Token'),
            (r'(ghs_[a-zA-Z0-9]{36})', 'GitHub Server Token'),
            (r'(ghr_[a-zA-Z0-9]{36})', 'GitHub Refresh Token'),
            
            # Database passwords
            (r'(?i)(password|passwd|pwd)\s*[=:]\s*[\'"]?([^\s\'"]{8,})[\'"]?', 'Password'),
            (r'(?i)(db[_-]?password|database[_-]?password)\s*[=:]\s*[\'"]?([^\s\'"]{4,})[\'"]?', 'Database password'),
            (r'(?i)(mysql[_-]?password|postgres[_-]?password|redis[_-]?password)\s*[=:]\s*[\'"]?([^\s\'"]{4,})[\'"]?', 'Database password'),
            
            # SSH/Private Keys
            (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', 'Private key'),
            (r'-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----', 'SSH private key'),
            (r'-----BEGIN\s+EC\s+PRIVATE\s+KEY-----', 'EC private key'),
            (r'-----BEGIN\s+DSA\s+PRIVATE\s+KEY-----', 'DSA private key'),
            (r'-----BEGIN\s+PGP\s+PRIVATE\s+KEY\s+BLOCK-----', 'PGP private key'),
            
            # Certificates and secrets
            (r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*[\'"]?([a-zA-Z0-9_\-+=]{16,})[\'"]?', 'Secret key'),
            (r'(?i)(private[_-]?key|privatekey)\s*[=:]\s*[\'"]?([a-zA-Z0-9_\-+=]{16,})[\'"]?', 'Private key'),
            (r'(?i)(client[_-]?secret|clientsecret)\s*[=:]\s*[\'"]?([a-zA-Z0-9_\-]{16,})[\'"]?', 'Client secret'),
            
            # JWT tokens
            (r'(eyJ[a-zA-Z0-9_\-]*\.eyJ[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*)', 'JWT token'),
            
            # Generic secrets in environment variables
            (r'(?i)(export\s+\w*(?:secret|key|token|password|passwd)\w*\s*=\s*[\'"]?)([^\s\'"]+)', 'Environment secret'),
            
            # Credit card patterns (basic)
            (r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b', 'Credit card number'),
            
            # Social Security Numbers (US)
            (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN'),
            (r'\b\d{3}\s\d{2}\s\d{4}\b', 'SSN'),
            
            # Email addresses in sensitive contexts
            (r'(?i)(smtp[_-]?password|email[_-]?password|mail[_-]?password)\s*[=:]\s*[\'"]?([^\s\'"]+)[\'"]?', 'Email password'),
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [
            (re.compile(pattern, re.MULTILINE | re.DOTALL), description)
            for pattern, description in self.sensitive_patterns
        ]
        
        # File extensions that commonly contain sensitive data
        self.sensitive_file_extensions = {
            '.key', '.pem', '.p12', '.pfx', '.crt', '.cer', '.der',
            '.ssh', '.gpg', '.pgp', '.asc', '.keystore', '.jks',
            '.env', '.secret', '.credentials', '.password'
        }
        
        # File names that commonly contain sensitive data
        self.sensitive_file_names = {
            'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519',
            'authorized_keys', 'known_hosts', 'ssh_config',
            '.env', '.env.local', '.env.production', '.env.staging',
            'secrets.json', 'credentials.json', 'keyfile.json',
            'password.txt', 'passwords.txt', 'secrets.txt',
            '.netrc', '.pgpass', '.my.cnf', 'wallet.dat'
        }
        
        # Directories that commonly contain sensitive data
        self.sensitive_directories = {
            '.ssh', '.gnupg', '.aws', '.config/gcloud',
            '.docker', '.kube', '.terraform.d'
        }

    def contains_sensitive_data(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check if text contains sensitive data
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (contains_sensitive, list_of_detected_types)
        """
        detected_types = []
        
        for pattern, description in self.compiled_patterns:
            if pattern.search(text):
                detected_types.append(description)
        
        return len(detected_types) > 0, detected_types

    def filter_sensitive_data(self, text: str) -> str:
        """
        Filter out sensitive data from text
        
        Args:
            text: Text to filter
            
        Returns:
            Filtered text with sensitive data redacted
        """
        filtered_text = text
        
        for pattern, description in self.compiled_patterns:
            filtered_text = pattern.sub(f'[REDACTED {description.upper()}]', filtered_text)
        
        return filtered_text

    def is_sensitive_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a file path indicates sensitive content
        
        Args:
            file_path: Path to check
            
        Returns:
            Tuple of (is_sensitive, reason)
        """
        import os
        
        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        if ext in self.sensitive_file_extensions:
            return True, f"Sensitive file extension: {ext}"
        
        # Check file name
        filename = os.path.basename(file_path.lower())
        if filename in self.sensitive_file_names:
            return True, f"Sensitive file name: {filename}"
        
        # Check if in sensitive directory
        dir_path = os.path.dirname(file_path)
        for sensitive_dir in self.sensitive_directories:
            if sensitive_dir in dir_path:
                return True, f"File in sensitive directory: {sensitive_dir}"
        
        return False, None

    def filter_command_output(self, command: str, output: str) -> str:
        """
        Filter sensitive data from command output based on command type
        
        Args:
            command: The command that was executed
            output: The output from the command
            
        Returns:
            Filtered output
        """
        # Commands that commonly output sensitive data
        sensitive_commands = {
            'cat', 'less', 'more', 'head', 'tail', 'grep', 'awk', 'sed',
            'printenv', 'env', 'export', 'set'
        }
        
        command_parts = command.strip().split()
        if not command_parts:
            return output
        
        base_command = command_parts[0]
        
        # If it's a potentially sensitive command, filter the output
        if base_command in sensitive_commands:
            # Check if we're reading a sensitive file
            for part in command_parts[1:]:
                if not part.startswith('-'):  # Skip flags
                    is_sensitive, reason = self.is_sensitive_file(part)
                    if is_sensitive:
                        return f"[REDACTED: Output from {reason}]"
            
            # Filter sensitive patterns from output
            return self.filter_sensitive_data(output)
        
        # For environment commands, always filter
        if base_command in ['printenv', 'env', 'export', 'set']:
            return self.filter_sensitive_data(output)
        
        return output

    def should_block_from_ai(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Determine if text should be completely blocked from AI
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (should_block, reason)
        """
        contains_sensitive, detected_types = self.contains_sensitive_data(text)
        
        if contains_sensitive:
            # Block if contains high-risk sensitive data
            high_risk_types = {
                'Private key', 'SSH private key', 'Password', 'Secret key',
                'API key', 'Access token', 'Bearer token', 'AWS Secret',
                'Credit card number', 'SSN'
            }
            
            for detected_type in detected_types:
                if detected_type in high_risk_types:
                    return True, f"Contains {detected_type.lower()}"
        
        return False, None

    def create_safe_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a safe version of context for AI by filtering sensitive data
        
        Args:
            context: Original context dictionary
            
        Returns:
            Filtered context safe for AI
        """
        safe_context = {}
        
        for key, value in context.items():
            if isinstance(value, str):
                # Check if this context item should be blocked entirely
                should_block, reason = self.should_block_from_ai(value)
                if should_block:
                    safe_context[key] = f"[BLOCKED: {reason}]"
                else:
                    # Filter sensitive data but keep the content
                    safe_context[key] = self.filter_sensitive_data(value)
            else:
                # Non-string values, pass through (but could add more filtering)
                safe_context[key] = value
        
        return safe_context

    def get_redaction_summary(self, original_text: str, filtered_text: str) -> str:
        """
        Get a summary of what was redacted
        
        Args:
            original_text: Original text
            filtered_text: Filtered text
            
        Returns:
            Summary of redactions
        """
        if original_text == filtered_text:
            return "No sensitive data detected"
        
        _, detected_types = self.contains_sensitive_data(original_text)
        
        if detected_types:
            return f"Redacted: {', '.join(set(detected_types))}"
        else:
            return "Content filtered for safety"
