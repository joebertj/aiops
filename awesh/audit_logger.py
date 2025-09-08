"""
Audit logging system for awesh
Provides comprehensive security and operational logging
"""

import json
import time
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum


class AuditEventType(Enum):
    """Types of audit events"""
    COMMAND_EXECUTED = "command_executed"
    COMMAND_BLOCKED = "command_blocked"
    COMMAND_REQUIRES_APPROVAL = "command_requires_approval"
    AI_INTERACTION = "ai_interaction"
    MCP_TOOL_CALL = "mcp_tool_call"
    MCP_TOOL_BLOCKED = "mcp_tool_blocked"
    POLICY_VIOLATION = "policy_violation"
    SECURITY_ALERT = "security_alert"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    CONFIG_CHANGE = "config_change"
    ERROR = "error"


@dataclass
class AuditEvent:
    """Represents an audit event"""
    timestamp: float
    event_type: AuditEventType
    session_id: str
    user: str
    working_directory: str
    event_data: Dict[str, Any]
    severity: str = "info"  # info, warning, error, critical
    source: str = "awesh"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['iso_timestamp'] = datetime.fromtimestamp(self.timestamp).isoformat()
        return data


class AweshAuditLogger:
    """Audit logging system for awesh"""
    
    def __init__(self, log_file: Path, max_log_size: int = 10485760, redact_sensitive: bool = True):
        self.log_file = log_file
        self.max_log_size = max_log_size
        self.redact_sensitive = redact_sensitive
        self.session_id = self._generate_session_id()
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger('awesh.audit')
        self.logger.setLevel(logging.INFO)
        
        # Sensitive patterns to redact
        self.sensitive_patterns = [
            r'password[=:\s]+\S+',
            r'token[=:\s]+\S+',
            r'key[=:\s]+\S+',
            r'secret[=:\s]+\S+',
            r'api[_-]?key[=:\s]+\S+',
            r'auth[=:\s]+\S+',
            r'bearer\s+\S+',
            r'--password\s+\S+',
            r'-p\s+\S+',
            r'export\s+\w*(?:PASSWORD|TOKEN|KEY|SECRET)\w*=\S+'
        ]
        
        # Compile patterns for performance
        import re
        self.compiled_sensitive_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.sensitive_patterns
        ]
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return hashlib.md5(f"{time.time()}{id(self)}".encode()).hexdigest()[:12]
    
    def _redact_sensitive_data(self, text: str) -> str:
        """Redact sensitive information from text"""
        if not self.redact_sensitive:
            return text
            
        redacted = text
        for pattern in self.compiled_sensitive_patterns:
            redacted = pattern.sub(lambda m: m.group().split('=')[0] + '=[REDACTED]' if '=' in m.group() else '[REDACTED]', redacted)
        
        return redacted
    
    def _rotate_log_if_needed(self):
        """Rotate log file if it exceeds maximum size"""
        try:
            if self.log_file.exists() and self.log_file.stat().st_size > self.max_log_size:
                # Rotate to .old file
                old_file = self.log_file.with_suffix('.jsonl.old')
                if old_file.exists():
                    old_file.unlink()
                self.log_file.rename(old_file)
                
                self.logger.info("Rotated audit log file")
        except Exception as e:
            self.logger.error(f"Failed to rotate log file: {e}")
    
    def _write_event(self, event: AuditEvent):
        """Write audit event to log file"""
        try:
            self._rotate_log_if_needed()
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                json_line = json.dumps(event.to_dict(), ensure_ascii=False)
                f.write(json_line + '\n')
                f.flush()
        except Exception as e:
            self.logger.error(f"Failed to write audit event: {e}")
    
    def log_command_executed(self, command: str, exit_code: int, execution_time: float, 
                           output_size: int, working_dir: str, user: str = "unknown"):
        """Log successful command execution"""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.COMMAND_EXECUTED,
            session_id=self.session_id,
            user=user,
            working_directory=working_dir,
            event_data={
                'command': self._redact_sensitive_data(command),
                'exit_code': exit_code,
                'execution_time_seconds': execution_time,
                'output_size_bytes': output_size,
                'command_hash': hashlib.sha256(command.encode()).hexdigest()[:16]
            },
            severity="info"
        )
        self._write_event(event)
    
    def log_command_blocked(self, command: str, reason: str, policy_rule: str,
                           working_dir: str, user: str = "unknown"):
        """Log blocked command attempt"""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.COMMAND_BLOCKED,
            session_id=self.session_id,
            user=user,
            working_directory=working_dir,
            event_data={
                'command': self._redact_sensitive_data(command),
                'block_reason': reason,
                'policy_rule': policy_rule,
                'command_hash': hashlib.sha256(command.encode()).hexdigest()[:16]
            },
            severity="warning"
        )
        self._write_event(event)
    
    def log_command_requires_approval(self, command: str, reason: str, 
                                    working_dir: str, user: str = "unknown"):
        """Log command that requires approval"""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.COMMAND_REQUIRES_APPROVAL,
            session_id=self.session_id,
            user=user,
            working_directory=working_dir,
            event_data={
                'command': self._redact_sensitive_data(command),
                'approval_reason': reason,
                'command_hash': hashlib.sha256(command.encode()).hexdigest()[:16]
            },
            severity="info"
        )
        self._write_event(event)
    
    def log_ai_interaction(self, prompt: str, response_preview: str, model: str,
                          tokens_used: Optional[int], response_time: float,
                          working_dir: str, user: str = "unknown"):
        """Log AI interaction"""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.AI_INTERACTION,
            session_id=self.session_id,
            user=user,
            working_directory=working_dir,
            event_data={
                'prompt': self._redact_sensitive_data(prompt[:500]),  # Truncate long prompts
                'response_preview': response_preview[:200],  # Preview only
                'model': model,
                'tokens_used': tokens_used,
                'response_time_seconds': response_time,
                'prompt_hash': hashlib.sha256(prompt.encode()).hexdigest()[:16]
            },
            severity="info"
        )
        self._write_event(event)
    
    def log_mcp_tool_call(self, tool_name: str, parameters: Dict[str, Any], 
                         result: Dict[str, Any], execution_time: float,
                         working_dir: str, user: str = "unknown"):
        """Log MCP tool call"""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.MCP_TOOL_CALL,
            session_id=self.session_id,
            user=user,
            working_directory=working_dir,
            event_data={
                'tool_name': tool_name,
                'parameters': self._redact_sensitive_data(str(parameters))[:500],
                'result_ok': result.get('ok', False),
                'result_size': len(str(result)),
                'execution_time_seconds': execution_time,
                'error_code': result.get('error', {}).get('code') if not result.get('ok') else None
            },
            severity="info" if result.get('ok') else "warning"
        )
        self._write_event(event)
    
    def log_mcp_tool_blocked(self, tool_name: str, parameters: Dict[str, Any],
                           reason: str, policy_rule: str,
                           working_dir: str, user: str = "unknown"):
        """Log blocked MCP tool call"""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.MCP_TOOL_BLOCKED,
            session_id=self.session_id,
            user=user,
            working_directory=working_dir,
            event_data={
                'tool_name': tool_name,
                'parameters': self._redact_sensitive_data(str(parameters))[:500],
                'block_reason': reason,
                'policy_rule': policy_rule
            },
            severity="warning"
        )
        self._write_event(event)
    
    def log_policy_violation(self, violation_type: str, rule_name: str, 
                           message: str, severity: str, context: Dict[str, Any],
                           working_dir: str, user: str = "unknown"):
        """Log policy violation"""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.POLICY_VIOLATION,
            session_id=self.session_id,
            user=user,
            working_directory=working_dir,
            event_data={
                'violation_type': violation_type,
                'rule_name': rule_name,
                'message': message,
                'context': self._redact_sensitive_data(str(context))[:500]
            },
            severity=severity
        )
        self._write_event(event)
    
    def log_security_alert(self, alert_type: str, message: str, details: Dict[str, Any],
                          working_dir: str, user: str = "unknown"):
        """Log security alert"""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.SECURITY_ALERT,
            session_id=self.session_id,
            user=user,
            working_directory=working_dir,
            event_data={
                'alert_type': alert_type,
                'message': message,
                'details': self._redact_sensitive_data(str(details))[:500]
            },
            severity="critical"
        )
        self._write_event(event)
    
    def log_session_start(self, config_info: Dict[str, Any], working_dir: str, user: str = "unknown"):
        """Log session start"""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.SESSION_START,
            session_id=self.session_id,
            user=user,
            working_directory=working_dir,
            event_data={
                'config_info': config_info,
                'awesh_version': "0.1.0"
            },
            severity="info"
        )
        self._write_event(event)
    
    def log_session_end(self, session_duration: float, commands_executed: int,
                       working_dir: str, user: str = "unknown"):
        """Log session end"""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.SESSION_END,
            session_id=self.session_id,
            user=user,
            working_directory=working_dir,
            event_data={
                'session_duration_seconds': session_duration,
                'commands_executed': commands_executed
            },
            severity="info"
        )
        self._write_event(event)
    
    def log_error(self, error_type: str, message: str, details: Optional[Dict[str, Any]] = None,
                 working_dir: str = "unknown", user: str = "unknown"):
        """Log error event"""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.ERROR,
            session_id=self.session_id,
            user=user,
            working_directory=working_dir,
            event_data={
                'error_type': error_type,
                'message': message,
                'details': details or {}
            },
            severity="error"
        )
        self._write_event(event)
    
    def get_recent_events(self, limit: int = 100, event_types: Optional[List[AuditEventType]] = None) -> List[Dict[str, Any]]:
        """Get recent audit events"""
        events = []
        
        try:
            if not self.log_file.exists():
                return events
                
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Get last N lines
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            for line in recent_lines:
                try:
                    event_data = json.loads(line.strip())
                    
                    # Filter by event types if specified
                    if event_types:
                        event_type = AuditEventType(event_data.get('event_type'))
                        if event_type not in event_types:
                            continue
                    
                    events.append(event_data)
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to read recent events: {e}")
            
        return events
    
    def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all events for a specific session"""
        events = []
        
        try:
            if not self.log_file.exists():
                return events
                
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        if event_data.get('session_id') == session_id:
                            events.append(event_data)
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Failed to read session events: {e}")
            
        return events
    
    def get_security_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get security alerts from the last N hours"""
        cutoff_time = time.time() - (hours * 3600)
        alerts = []
        
        try:
            if not self.log_file.exists():
                return alerts
                
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        if (event_data.get('timestamp', 0) >= cutoff_time and
                            event_data.get('event_type') in [
                                AuditEventType.SECURITY_ALERT.value,
                                AuditEventType.COMMAND_BLOCKED.value,
                                AuditEventType.POLICY_VIOLATION.value
                            ] and
                            event_data.get('severity') in ['error', 'critical']):
                            alerts.append(event_data)
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Failed to read security alerts: {e}")
            
        return alerts
