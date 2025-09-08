"""
Policy enforcement system for awesh
Implements strict guardrails as specified in specs.md
"""

import os
import re
import yaml
import time
import logging
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PolicyAction(Enum):
    """Actions the policy system can take"""
    ALLOW = "allow"
    DENY = "deny" 
    REQUIRE_APPROVAL = "require_approval"
    DRY_RUN_ONLY = "dry_run_only"


@dataclass
class PolicyViolation:
    """Represents a policy violation"""
    rule_name: str
    violation_type: str
    message: str
    severity: str  # "low", "medium", "high", "critical"
    suggested_action: str


@dataclass 
class CommandContext:
    """Context information for command evaluation"""
    command: str
    args: List[str]
    working_directory: str
    user: str
    environment: Dict[str, str]
    session_id: str
    timestamp: float


class AweshPolicyEngine:
    """Policy enforcement engine for awesh"""
    
    def __init__(self, policy_path: Optional[Path] = None):
        self.policy_path = policy_path or Path.home() / '.awesh_policy.yaml'
        self.policy_data = {}
        self.load_policy()
        
        # Security patterns - these are ALWAYS enforced regardless of policy
        self.critical_security_patterns = [
            # Privilege escalation attempts
            (r'sudo\s+su\s*-', "Privilege escalation attempt"),
            (r'sudo\s+.*passwd\s+root', "Root password change attempt"),
            (r'chmod\s+[47]77', "Dangerous permission setting"),
            
            # System modification
            (r'rm\s+-rf\s+/', "Dangerous recursive delete"),
            (r'rm\s+-rf\s+\*', "Dangerous wildcard delete"),
            (r'dd\s+if=.*of=/dev/', "Direct device write attempt"),
            (r'mkfs\s+', "Filesystem creation attempt"),
            
            # Network security
            (r'nc\s+.*-l.*-e', "Netcat backdoor attempt"),
            (r'bash\s+-i\s+>&', "Reverse shell attempt"),
            (r'python.*socket.*exec', "Python reverse shell attempt"),
            
            # Credential access
            (r'cat\s+.*shadow', "Shadow file access attempt"),
            (r'cat\s+.*passwd', "Password file access attempt"),
            (r'grep\s+.*password.*\*', "Password search attempt"),
            
            # Process manipulation
            (r'kill\s+-9\s+1\b', "Init process kill attempt"),
            (r'killall\s+-9\s+.*', "Mass process kill attempt"),
            
            # System information gathering (suspicious patterns)
            (r'find\s+/.*-name.*\*\.key', "Key file search"),
            (r'find\s+/.*-name.*\*\.pem', "Certificate search"),
            (r'locate\s+.*password', "Password file location"),
        ]
        
        # Compile patterns for performance
        self.compiled_security_patterns = [
            (re.compile(pattern, re.IGNORECASE), desc) 
            for pattern, desc in self.critical_security_patterns
        ]
        
        # High-risk commands that require approval
        self.high_risk_commands = {
            'rm', 'rmdir', 'mv', 'chmod', 'chown', 'chgrp', 'dd', 'fdisk',
            'mkfs', 'mount', 'umount', 'iptables', 'ufw', 'systemctl',
            'service', 'init', 'reboot', 'shutdown', 'halt', 'poweroff',
            'passwd', 'useradd', 'userdel', 'usermod', 'groupadd', 'groupdel',
            'crontab', 'at', 'batch', 'kill', 'killall', 'pkill'
        }
        
        # Commands that should never be run via AI
        self.forbidden_ai_commands = {
            'sudo', 'su', 'passwd', 'visudo', 'crontab -e', 'fdisk', 'parted',
            'mkfs', 'fsck', 'mount', 'umount', 'iptables', 'ufw', 'systemctl stop',
            'systemctl disable', 'service stop', 'init 0', 'init 6', 'reboot',
            'shutdown', 'halt', 'poweroff'
        }

    def load_policy(self):
        """Load policy configuration from YAML file"""
        try:
            if self.policy_path.exists():
                with open(self.policy_path, 'r') as f:
                    self.policy_data = yaml.safe_load(f) or {}
                logger.info(f"Loaded policy from {self.policy_path}")
            else:
                self.policy_data = self._get_default_policy()
                self._create_default_policy_file()
                logger.info("Created default policy file")
        except Exception as e:
            logger.error(f"Failed to load policy: {e}")
            self.policy_data = self._get_default_policy()

    def _get_default_policy(self) -> Dict[str, Any]:
        """Get default security policy"""
        return {
            'version': '1.0',
            'security': {
                'enable_command_filtering': True,
                'enable_path_restrictions': True,
                'enable_audit_logging': True,
                'require_approval_for_destructive': True,
                'block_privilege_escalation': True,
                'max_command_length': 1000,
                'timeout_seconds': 30,
                'max_output_size': 1048576,  # 1MB
            },
            'command_policies': {
                'allowed_commands': [],  # Empty = allow all not explicitly forbidden
                'forbidden_commands': [
                    'sudo su -', 'passwd root', 'rm -rf /', 'rm -rf *',
                    'dd if=/dev/zero', 'mkfs', 'fdisk', 'parted',
                    'iptables -F', 'ufw --force', 'init 0', 'init 6',
                    'shutdown -h now', 'reboot', 'halt', 'poweroff'
                ],
                'require_approval': [
                    'rm -rf', 'chmod 777', 'chown root', 'systemctl stop',
                    'service stop', 'kill -9', 'killall', 'crontab'
                ],
                'dry_run_only': [
                    'rm -rf *', 'chmod -R 777', 'chown -R root'
                ]
            },
            'path_policies': {
                'forbidden_paths': [
                    '/etc/shadow', '/etc/passwd', '/etc/sudoers',
                    '/boot', '/sys', '/proc/sys', '/dev/sd*', '/dev/hd*'
                ],
                'read_only_paths': [
                    '/etc', '/usr', '/opt', '/var/log'
                ],
                'allowed_write_paths': [
                    '~', '/tmp', '/var/tmp', '/home'
                ]
            },
            'mcp_policies': {
                'allowed_tools': [
                    'list_dir', 'read_file', 'git_status', 'git_diff', 
                    'git_log', 'find_files', 'grep_files'
                ],
                'forbidden_tools': [
                    'run_shell', 'execute_command', 'write_file', 'delete_file',
                    'modify_system', 'install_package', 'change_permissions'
                ],
                'require_approval_tools': [
                    'run', 'execute', 'write', 'delete', 'modify'
                ],
                'tool_timeouts': {
                    'default': 10,
                    'run': 30,
                    'execute': 30
                }
            },
            'audit': {
                'log_all_commands': True,
                'log_ai_interactions': True,
                'log_policy_violations': True,
                'log_file': '~/.awesh_audit.jsonl',
                'max_log_size': 10485760,  # 10MB
                'redact_sensitive_data': True
            }
        }

    def _create_default_policy_file(self):
        """Create default policy file"""
        try:
            self.policy_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.policy_path, 'w') as f:
                yaml.dump(self.policy_data, f, default_flow_style=False, indent=2)
            logger.info(f"Created default policy at {self.policy_path}")
        except Exception as e:
            logger.error(f"Failed to create policy file: {e}")

    def validate_command(self, context: CommandContext) -> Tuple[PolicyAction, List[PolicyViolation]]:
        """
        Validate a command against security policies
        
        Args:
            context: Command context information
            
        Returns:
            Tuple of (action, violations)
        """
        violations = []
        
        # Check critical security patterns first
        for pattern, description in self.compiled_security_patterns:
            if pattern.search(context.command):
                violations.append(PolicyViolation(
                    rule_name="critical_security_pattern",
                    violation_type="security",
                    message=f"Critical security violation: {description}",
                    severity="critical",
                    suggested_action="Command blocked for security"
                ))
                return PolicyAction.DENY, violations

        # Check command length
        max_length = self.policy_data.get('security', {}).get('max_command_length', 1000)
        if len(context.command) > max_length:
            violations.append(PolicyViolation(
                rule_name="max_command_length",
                violation_type="security",
                message=f"Command exceeds maximum length ({max_length} chars)",
                severity="medium",
                suggested_action="Shorten command or break into multiple commands"
            ))

        # Check forbidden commands
        forbidden = self.policy_data.get('command_policies', {}).get('forbidden_commands', [])
        for forbidden_cmd in forbidden:
            if self._command_matches_pattern(context.command, forbidden_cmd):
                violations.append(PolicyViolation(
                    rule_name="forbidden_command",
                    violation_type="security", 
                    message=f"Command matches forbidden pattern: {forbidden_cmd}",
                    severity="high",
                    suggested_action="Use alternative command or request approval"
                ))
                return PolicyAction.DENY, violations

        # Check require approval commands
        require_approval = self.policy_data.get('command_policies', {}).get('require_approval', [])
        for approval_cmd in require_approval:
            if self._command_matches_pattern(context.command, approval_cmd):
                violations.append(PolicyViolation(
                    rule_name="requires_approval",
                    violation_type="policy",
                    message=f"Command requires approval: {approval_cmd}",
                    severity="medium", 
                    suggested_action="Request human approval before execution"
                ))
                return PolicyAction.REQUIRE_APPROVAL, violations

        # Check dry-run only commands
        dry_run_only = self.policy_data.get('command_policies', {}).get('dry_run_only', [])
        for dry_run_cmd in dry_run_only:
            if self._command_matches_pattern(context.command, dry_run_cmd):
                violations.append(PolicyViolation(
                    rule_name="dry_run_only",
                    violation_type="policy",
                    message=f"Command only allowed in dry-run mode: {dry_run_cmd}",
                    severity="medium",
                    suggested_action="Add --dry-run flag or equivalent"
                ))
                return PolicyAction.DRY_RUN_ONLY, violations

        # Check path restrictions
        path_violations = self._check_path_restrictions(context)
        violations.extend(path_violations)
        
        if any(v.severity == "critical" for v in path_violations):
            return PolicyAction.DENY, violations

        # If we have violations but nothing critical, require approval
        if violations:
            return PolicyAction.REQUIRE_APPROVAL, violations

        return PolicyAction.ALLOW, violations

    def validate_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Tuple[PolicyAction, List[PolicyViolation]]:
        """
        Validate MCP tool call against policies
        
        Args:
            tool_name: Name of the MCP tool
            parameters: Tool parameters
            
        Returns:
            Tuple of (action, violations)
        """
        violations = []
        mcp_policies = self.policy_data.get('mcp_policies', {})

        # Check forbidden tools
        forbidden_tools = mcp_policies.get('forbidden_tools', [])
        if tool_name in forbidden_tools:
            violations.append(PolicyViolation(
                rule_name="forbidden_mcp_tool",
                violation_type="security",
                message=f"MCP tool is forbidden: {tool_name}",
                severity="high",
                suggested_action="Use alternative tool or request policy change"
            ))
            return PolicyAction.DENY, violations

        # Check if tool requires approval
        require_approval_tools = mcp_policies.get('require_approval_tools', [])
        for approval_pattern in require_approval_tools:
            if approval_pattern in tool_name:
                violations.append(PolicyViolation(
                    rule_name="mcp_tool_requires_approval",
                    violation_type="policy",
                    message=f"MCP tool requires approval: {tool_name}",
                    severity="medium",
                    suggested_action="Request human approval before execution"
                ))
                return PolicyAction.REQUIRE_APPROVAL, violations

        # Check allowed tools (if specified)
        allowed_tools = mcp_policies.get('allowed_tools', [])
        if allowed_tools and tool_name not in allowed_tools:
            violations.append(PolicyViolation(
                rule_name="mcp_tool_not_allowed",
                violation_type="policy",
                message=f"MCP tool not in allowed list: {tool_name}",
                severity="medium",
                suggested_action="Add tool to allowed list or use alternative"
            ))
            return PolicyAction.DENY, violations

        return PolicyAction.ALLOW, violations

    def _command_matches_pattern(self, command: str, pattern: str) -> bool:
        """Check if command matches a pattern (supports wildcards)"""
        # Convert shell-style wildcards to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        try:
            return bool(re.search(regex_pattern, command, re.IGNORECASE))
        except re.error:
            # If regex fails, do simple substring match
            return pattern.lower() in command.lower()

    def _check_path_restrictions(self, context: CommandContext) -> List[PolicyViolation]:
        """Check command against path restrictions"""
        violations = []
        path_policies = self.policy_data.get('path_policies', {})
        
        # Extract paths from command
        paths = self._extract_paths_from_command(context.command)
        
        for path in paths:
            # Check forbidden paths
            forbidden_paths = path_policies.get('forbidden_paths', [])
            for forbidden_path in forbidden_paths:
                if self._path_matches(path, forbidden_path):
                    violations.append(PolicyViolation(
                        rule_name="forbidden_path_access",
                        violation_type="security",
                        message=f"Access to forbidden path: {path}",
                        severity="critical",
                        suggested_action="Use alternative path or request approval"
                    ))
                    break

        return violations

    def _extract_paths_from_command(self, command: str) -> List[str]:
        """Extract file/directory paths from command"""
        # Simple path extraction - could be enhanced
        paths = []
        tokens = command.split()
        
        for token in tokens:
            # Skip flags/options
            if token.startswith('-'):
                continue
            
            # Check if token looks like a path
            if ('/' in token or token.startswith('~') or 
                token.startswith('.') or token == '..'):
                paths.append(token)
        
        return paths

    def _path_matches(self, path: str, pattern: str) -> bool:
        """Check if path matches a pattern"""
        # Expand ~ and resolve path
        try:
            expanded_path = str(Path(path).expanduser().resolve())
            expanded_pattern = str(Path(pattern).expanduser().resolve())
            return expanded_path.startswith(expanded_pattern)
        except Exception:
            # Fallback to simple string matching
            return pattern in path

    def is_ai_command_allowed(self, command: str) -> Tuple[bool, Optional[str]]:
        """Check if command is allowed to be suggested/executed by AI"""
        first_token = command.strip().split()[0] if command.strip() else ""
        
        # Check against forbidden AI commands
        if first_token in self.forbidden_ai_commands:
            return False, f"Command '{first_token}' is forbidden for AI execution"
        
        # Check full command patterns
        for forbidden_cmd in self.forbidden_ai_commands:
            if self._command_matches_pattern(command, forbidden_cmd):
                return False, f"Command matches forbidden AI pattern: {forbidden_cmd}"
        
        return True, None

    def get_timeout_for_tool(self, tool_name: str) -> int:
        """Get timeout for specific MCP tool"""
        mcp_policies = self.policy_data.get('mcp_policies', {})
        timeouts = mcp_policies.get('tool_timeouts', {})
        return timeouts.get(tool_name, timeouts.get('default', 10))

    def should_audit_command(self, command: str) -> bool:
        """Check if command should be audited"""
        audit_config = self.policy_data.get('audit', {})
        return audit_config.get('log_all_commands', True)

    def should_audit_ai_interaction(self) -> bool:
        """Check if AI interactions should be audited"""
        audit_config = self.policy_data.get('audit', {})
        return audit_config.get('log_ai_interactions', True)
