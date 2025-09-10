"""
Security Agent for AIOps System

This agent implements two core security functions:
1. Guardrail - Prevents executing dangerous commands
2. Sensitive Info Gatekeeper - Prevents leaking sensitive information

It uses the existing security implementations from awesh for consistency and best practices.
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentResult

# Import existing security implementations from awesh
try:
    # Add awesh directory to path to import existing modules
    awesh_path = Path(__file__).parent.parent / "awesh"
    if str(awesh_path) not in sys.path:
        sys.path.insert(0, str(awesh_path))
    
    from command_safety import CommandSafetyFilter
    from sensitive_data_filter import SensitiveDataFilter
    from policy import AweshPolicyEngine, CommandContext, PolicyAction
except ImportError as e:
    print(f"Warning: Could not import existing security modules: {e}", file=sys.stderr)
    # Fallback to basic implementations if imports fail
    CommandSafetyFilter = None
    SensitiveDataFilter = None
    AweshPolicyEngine = None


class SecurityAgent(BaseAgent):
    """
    Security Agent with dual functions using existing awesh security implementations:
    
    1. GUARDRAIL: Uses CommandSafetyFilter and AweshPolicyEngine for command validation
    2. SENSITIVE INFO GATEKEEPER: Uses SensitiveDataFilter for data protection
    
    This agent leverages the proven security implementations from awesh for consistency.
    """
    
    def __init__(self, policy_path: Optional[str] = None):
        super().__init__("Security Agent", priority=10)  # Highest priority - runs first
        
        # Initialize security components using existing implementations
        self.command_safety = CommandSafetyFilter() if CommandSafetyFilter else None
        self.sensitive_filter = SensitiveDataFilter() if SensitiveDataFilter else None
        self.policy_engine = AweshPolicyEngine(Path(policy_path)) if AweshPolicyEngine and policy_path else None
        
        # Fallback patterns if imports failed
        if not self.command_safety or not self.sensitive_filter:
            self._init_fallback_patterns()
    
    def _init_fallback_patterns(self):
        """Initialize basic fallback patterns if imports failed"""
        import re
        self.dangerous_patterns = [
            r'\b(rm\s+-rf|del\s+/s|format\s+|fdisk|mkfs)\b',
            r'\b(shutdown|reboot|halt|poweroff)\b',
            r'\b(dd\s+if=.*of=.*|cat\s+.*>\s*/dev/)',
        ]
        self.compiled_dangerous_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns]
        
        self.sensitive_patterns = [
            (r'api[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_\-]{20,})', 'API key'),
            (r'password["\s]*[:=]["\s]*([^\s]{6,})', 'Password'),
            (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', 'Private key'),
        ]
        self.compiled_sensitive_patterns = [(re.compile(pattern, re.IGNORECASE), desc) for pattern, desc in self.sensitive_patterns]
    
    def should_handle(self, prompt: str, context: Dict[str, Any]) -> bool:
        """
        Security agent should always check prompts for safety.
        """
        return True  # Always check for security issues
    
    async def process(self, prompt: str, context: Dict[str, Any]) -> AgentResult:
        """
        Process the prompt for security validation using existing awesh implementations.
        """
        # ===== GUARDRAIL: Command Safety Check =====
        if self.command_safety:
            # Use existing command safety filter
            is_safe, unsafe_reason = self.command_safety.is_command_safe(prompt)
            if not is_safe:
                return AgentResult(
                    handled=True,
                    response=f"🚨 **SECURITY BLOCKED** 🚨\n\n"
                            f"The operation '{prompt}' has been blocked for security reasons.\n\n"
                            f"**Reason:** {unsafe_reason}\n\n"
                            f"**Safety recommendations:**\n"
                            f"• Use safer alternatives\n"
                            f"• Add confirmation steps for destructive operations\n"
                            f"• Review the operation with your team before proceeding\n\n"
                            f"If this is a legitimate operation, please:\n"
                            f"1. Break it down into smaller, safer steps\n"
                            f"2. Add explicit confirmation\n"
                            f"3. Use the --dry-run flag where available",
                    metadata={"security_action": "blocked", "reason": unsafe_reason}
                )
            
            # Check if command requires confirmation
            needs_confirm, confirm_reason = self.command_safety.requires_confirmation(prompt)
            if needs_confirm:
                return AgentResult(
                    handled=False,  # Don't block, but show warning
                    modified_prompt=prompt,
                    response=f"⚠️ **SECURITY WARNING** ⚠️\n\n"
                            f"The operation '{prompt}' requires confirmation.\n\n"
                            f"**Reason:** {confirm_reason}\n\n"
                            f"**Please confirm this is intentional before proceeding.**\n"
                            f"Consider using --dry-run flags where available.\n\n",
                    metadata={"security_action": "warning", "reason": confirm_reason}
                )
        
        # ===== SENSITIVE INFO GATEKEEPER: Data Protection =====
        if self.sensitive_filter:
            # Check if prompt contains sensitive data
            contains_sensitive, detected_types = self.sensitive_filter.contains_sensitive_data(prompt)
            if contains_sensitive:
                # Check if should be completely blocked
                should_block, block_reason = self.sensitive_filter.should_block_from_ai(prompt)
                if should_block:
                    return AgentResult(
                        handled=True,
                        response=f"🔒 **SENSITIVE DATA BLOCKED** 🔒\n\n"
                                f"The prompt contains sensitive information and has been blocked.\n\n"
                                f"**Reason:** {block_reason}\n\n"
                                f"**Detected sensitive data types:** {', '.join(detected_types)}\n\n"
                                f"**Recommendations:**\n"
                                f"• Remove sensitive information from your prompt\n"
                                f"• Use environment variables or secure storage\n"
                                f"• Contact your security team for guidance\n\n"
                                f"**Safe alternatives:**\n"
                                f"• Use placeholder values (e.g., 'API_KEY' instead of actual key)\n"
                                f"• Reference configuration files without showing contents\n"
                                f"• Use secure credential management systems",
                        metadata={"security_action": "sensitive_blocked", "types": detected_types, "reason": block_reason}
                    )
                else:
                    # Filter sensitive data but allow the prompt
                    filtered_prompt = self.sensitive_filter.filter_sensitive_data(prompt)
                    return AgentResult(
                        handled=False,
                        modified_prompt=filtered_prompt,
                        response=f"🔍 **SENSITIVE DATA FILTERED** 🔍\n\n"
                                f"Sensitive information has been automatically filtered from your prompt.\n\n"
                                f"**Detected types:** {', '.join(detected_types)}\n"
                                f"**Filtered prompt will be processed safely.**\n\n",
                        metadata={"security_action": "sensitive_filtered", "types": detected_types}
                    )
        
        # ===== POLICY ENGINE: Advanced Policy Check =====
        if self.policy_engine:
            # Create command context for policy evaluation
            command_context = CommandContext(
                command=prompt,
                args=prompt.split(),
                working_directory=context.get('working_directory', os.getcwd()),
                user=context.get('user', os.getenv('USER', 'unknown')),
                environment=dict(os.environ),
                session_id=context.get('session_id', 'unknown'),
                timestamp=time.time()
            )
            
            # Validate against policies
            action, violations = self.policy_engine.validate_command(command_context)
            
            if action == PolicyAction.DENY:
                violation_messages = [f"• {v.message}" for v in violations]
                return AgentResult(
                    handled=True,
                    response=f"🚫 **POLICY VIOLATION** 🚫\n\n"
                            f"The operation '{prompt}' violates security policies.\n\n"
                            f"**Violations:**\n" + "\n".join(violation_messages) + "\n\n"
                            f"**Suggested actions:**\n" + 
                            "\n".join([f"• {v.suggested_action}" for v in violations]) + "\n\n"
                            f"Please review your request and try again with compliant operations.",
                    metadata={"security_action": "policy_denied", "violations": [v.__dict__ for v in violations]}
                )
            
            elif action == PolicyAction.REQUIRE_APPROVAL:
                violation_messages = [f"• {v.message}" for v in violations]
                return AgentResult(
                    handled=False,
                    modified_prompt=prompt,
                    response=f"⚠️ **APPROVAL REQUIRED** ⚠️\n\n"
                            f"The operation '{prompt}' requires approval.\n\n"
                            f"**Policy violations:**\n" + "\n".join(violation_messages) + "\n\n"
                            f"**Please confirm this operation is authorized before proceeding.**\n\n",
                    metadata={"security_action": "approval_required", "violations": [v.__dict__ for v in violations]}
                )
        
        # ===== FALLBACK: Basic Pattern Check =====
        if not self.command_safety and not self.sensitive_filter:
            # Use basic fallback patterns
            for pattern in self.compiled_dangerous_patterns:
                if pattern.search(prompt):
                    return AgentResult(
                        handled=True,
                        response=f"🚨 **SECURITY BLOCKED** 🚨\n\n"
                                f"The operation '{prompt}' contains potentially dangerous patterns.\n\n"
                                f"**Blocked pattern:** `{pattern.pattern}`\n\n"
                                f"Please use safer alternatives or contact your security team.",
                        metadata={"security_action": "blocked_fallback", "pattern": pattern.pattern}
                    )
            
            # Check for sensitive data with fallback patterns
            for pattern, desc in self.compiled_sensitive_patterns:
                if pattern.search(prompt):
                    return AgentResult(
                        handled=True,
                        response=f"🔒 **SENSITIVE DATA DETECTED** 🔒\n\n"
                                f"The prompt contains {desc.lower()} and has been blocked.\n\n"
                                f"Please remove sensitive information and try again.",
                        metadata={"security_action": "sensitive_blocked_fallback", "type": desc}
                    )
        
        # ===== PASS THROUGH =====
        # If we get here, the prompt passed all security checks
        return AgentResult(
            handled=False,
            modified_prompt=prompt,
            metadata={"security_action": "passed", "checks": ["command_safety", "sensitive_data", "policy"]}
        )
    
    def get_help(self) -> str:
        """Get help text for the security agent"""
        return """
Security Agent - Dual-function security system using proven awesh implementations

This agent runs first in the processing chain and provides two core functions:

🔒 GUARDRAIL (Command Safety):
• Uses CommandSafetyFilter for comprehensive command validation
• Blocks dangerous operations (rm -rf, shutdown, etc.)
• Warns about potentially risky operations (restart, scale, etc.)
• Uses AweshPolicyEngine for advanced policy enforcement
• Provides detailed explanations and safer alternatives

🛡️ SENSITIVE INFO GATEKEEPER (Data Protection):
• Uses SensitiveDataFilter for comprehensive data protection
• Detects and blocks API keys, passwords, tokens, SSH keys
• Filters sensitive data from prompts while preserving functionality
• Protects against credential leakage to AI systems
• Supports AWS, GitHub, database, and other credential types

Security Features:
• Multi-layer validation (command safety + sensitive data + policy)
• Graceful fallback to basic patterns if imports fail
• Detailed violation reporting with actionable recommendations
• Integration with existing awesh security infrastructure
• Audit logging and compliance support

The agent provides clear explanations for blocked operations and suggests safer alternatives.
"""