"""
Secure MCP client for awesh with policy enforcement and audit logging
"""

import json
import time
import asyncio
import subprocess
import logging
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

from .policy import AweshPolicyEngine, PolicyAction, CommandContext
from .audit_logger import AweshAuditLogger

logger = logging.getLogger(__name__)


class SecureMCPClient:
    """Secure MCP client with policy enforcement and audit logging"""
    
    def __init__(self, mcp_server_path: Path, policy_engine: AweshPolicyEngine, 
                 audit_logger: AweshAuditLogger, dry_run: bool = False):
        self.mcp_server_path = mcp_server_path
        self.policy_engine = policy_engine
        self.audit_logger = audit_logger
        self.dry_run = dry_run
        self.mcp_process = None
        self.request_id = 0
        
        # Track MCP server state
        self.server_ready = False
        self.server_capabilities = {}
        
    async def start_mcp_server(self) -> bool:
        """Start the MCP server subprocess"""
        try:
            if not self.mcp_server_path.exists():
                logger.error(f"MCP server not found: {self.mcp_server_path}")
                return False
            
            # Start MCP server process
            self.mcp_process = await asyncio.create_subprocess_exec(
                'python3', str(self.mcp_server_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Initialize MCP server
            init_success = await self._initialize_server()
            if init_success:
                self.server_ready = True
                logger.info("MCP server started and initialized")
                return True
            else:
                await self.stop_mcp_server()
                return False
                
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            self.audit_logger.log_error(
                "mcp_server_start_failed",
                f"Failed to start MCP server: {e}",
                {"server_path": str(self.mcp_server_path)}
            )
            return False
    
    async def stop_mcp_server(self):
        """Stop the MCP server subprocess"""
        if self.mcp_process:
            try:
                self.mcp_process.terminate()
                await asyncio.wait_for(self.mcp_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.mcp_process.kill()
                await self.mcp_process.wait()
            finally:
                self.mcp_process = None
                self.server_ready = False
                logger.info("MCP server stopped")
    
    async def _initialize_server(self) -> bool:
        """Initialize MCP server with handshake"""
        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {
                            "listChanged": False
                        },
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "awesh",
                        "version": "0.1.0"
                    }
                }
            }
            
            response = await self._send_request(init_request)
            if response and not response.get("error"):
                self.server_capabilities = response.get("result", {}).get("capabilities", {})
                
                # Send initialized notification
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                await self._send_notification(initialized_notification)
                
                return True
            else:
                logger.error(f"MCP initialization failed: {response}")
                return False
                
        except Exception as e:
            logger.error(f"MCP initialization error: {e}")
            return False
    
    def _next_request_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    async def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send request to MCP server and get response"""
        if not self.mcp_process or not self.server_ready:
            return None
        
        try:
            # Send request
            request_json = json.dumps(request) + '\n'
            self.mcp_process.stdin.write(request_json.encode())
            await self.mcp_process.stdin.drain()
            
            # Read response
            response_line = await asyncio.wait_for(
                self.mcp_process.stdout.readline(), 
                timeout=30.0
            )
            
            if response_line:
                return json.loads(response_line.decode().strip())
            else:
                return None
                
        except Exception as e:
            logger.error(f"MCP request failed: {e}")
            return None
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send notification to MCP server (no response expected)"""
        if not self.mcp_process or not self.server_ready:
            return
        
        try:
            notification_json = json.dumps(notification) + '\n'
            self.mcp_process.stdin.write(notification_json.encode())
            await self.mcp_process.stdin.drain()
        except Exception as e:
            logger.error(f"MCP notification failed: {e}")
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any],
                       working_dir: str, user: str = "unknown") -> Dict[str, Any]:
        """
        Call MCP tool with security validation and audit logging
        
        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters
            working_dir: Current working directory
            user: User making the request
            
        Returns:
            Tool result or error response
        """
        start_time = time.time()
        
        # Validate tool call against policy
        action, violations = self.policy_engine.validate_mcp_tool(tool_name, parameters)
        
        if action == PolicyAction.DENY:
            # Log blocked tool call
            reason = "; ".join([v.message for v in violations])
            rule_name = violations[0].rule_name if violations else "unknown"
            
            self.audit_logger.log_mcp_tool_blocked(
                tool_name, parameters, reason, rule_name, working_dir, user
            )
            
            return {
                "ok": False,
                "error": {
                    "code": "POLICY_VIOLATION",
                    "message": f"Tool call blocked by policy: {reason}"
                }
            }
        
        if action == PolicyAction.REQUIRE_APPROVAL:
            # Log approval requirement
            reason = "; ".join([v.message for v in violations])
            self.audit_logger.log_command_requires_approval(
                f"mcp_tool:{tool_name}", reason, working_dir, user
            )
            
            return {
                "ok": False,
                "error": {
                    "code": "APPROVAL_REQUIRED",
                    "message": f"Tool call requires approval: {reason}"
                }
            }
        
        # Proceed with tool call
        try:
            if self.dry_run:
                # Simulate tool call in dry-run mode
                result = {
                    "ok": True,
                    "result": {
                        "dry_run": True,
                        "tool_name": tool_name,
                        "parameters": parameters,
                        "message": "Dry run - tool would be executed"
                    }
                }
            else:
                # Make actual tool call
                result = await self._execute_tool_call(tool_name, parameters)
            
            execution_time = time.time() - start_time
            
            # Log successful tool call
            self.audit_logger.log_mcp_tool_call(
                tool_name, parameters, result, execution_time, working_dir, user
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = {
                "ok": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": f"Tool execution failed: {e}"
                }
            }
            
            # Log failed tool call
            self.audit_logger.log_mcp_tool_call(
                tool_name, parameters, error_result, execution_time, working_dir, user
            )
            
            return error_result
    
    async def _execute_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actual MCP tool call"""
        if not self.server_ready:
            return {
                "ok": False,
                "error": {
                    "code": "SERVER_NOT_READY",
                    "message": "MCP server is not ready"
                }
            }
        
        # Get timeout for this tool
        timeout = self.policy_engine.get_timeout_for_tool(tool_name)
        
        try:
            # Prepare tool call request
            tool_request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": parameters
                }
            }
            
            # Execute with timeout
            response = await asyncio.wait_for(
                self._send_request(tool_request),
                timeout=timeout
            )
            
            if response:
                if response.get("error"):
                    return {
                        "ok": False,
                        "error": response["error"]
                    }
                else:
                    return {
                        "ok": True,
                        "result": response.get("result", {})
                    }
            else:
                return {
                    "ok": False,
                    "error": {
                        "code": "NO_RESPONSE",
                        "message": "No response from MCP server"
                    }
                }
                
        except asyncio.TimeoutError:
            return {
                "ok": False,
                "error": {
                    "code": "TIMEOUT",
                    "message": f"Tool call timed out after {timeout} seconds"
                }
            }
        except Exception as e:
            return {
                "ok": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": str(e)
                }
            }
    
    async def list_available_tools(self) -> Dict[str, Any]:
        """Get list of available tools from MCP server"""
        if not self.server_ready:
            return {"ok": False, "error": "Server not ready"}
        
        try:
            tools_request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "tools/list"
            }
            
            response = await self._send_request(tools_request)
            if response and not response.get("error"):
                tools = response.get("result", {}).get("tools", [])
                
                # Filter tools based on policy
                allowed_tools = []
                for tool in tools:
                    tool_name = tool.get("name", "")
                    action, _ = self.policy_engine.validate_mcp_tool(tool_name, {})
                    if action != PolicyAction.DENY:
                        allowed_tools.append(tool)
                
                return {"ok": True, "tools": allowed_tools}
            else:
                return {"ok": False, "error": response.get("error", "Unknown error")}
                
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get MCP server information"""
        return {
            "server_ready": self.server_ready,
            "server_capabilities": self.server_capabilities,
            "dry_run_mode": self.dry_run,
            "server_path": str(self.mcp_server_path)
        }


class MCPToolValidator:
    """Validates MCP tool calls for common security issues"""
    
    @staticmethod
    def validate_file_access(path: str, operation: str) -> Tuple[bool, Optional[str]]:
        """Validate file access operations"""
        try:
            resolved_path = Path(path).resolve()
            
            # Check for suspicious paths
            suspicious_paths = [
                '/etc/passwd', '/etc/shadow', '/etc/sudoers',
                '/root', '/proc/sys', '/sys', '/dev'
            ]
            
            for suspicious in suspicious_paths:
                if str(resolved_path).startswith(suspicious):
                    return False, f"Access to {suspicious} is restricted"
            
            # Check for operations on sensitive files
            if operation in ['write', 'delete', 'modify']:
                if resolved_path.suffix in ['.key', '.pem', '.p12', '.crt']:
                    return False, f"Modification of {resolved_path.suffix} files is restricted"
            
            return True, None
            
        except Exception as e:
            return False, f"Path validation error: {e}"
    
    @staticmethod
    def validate_command_parameters(command: str, args: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate command execution parameters"""
        # Check for command injection attempts
        dangerous_chars = [';', '|', '&', '$(', '`', '>', '<']
        full_command = f"{command} {' '.join(args)}"
        
        for char in dangerous_chars:
            if char in full_command:
                return False, f"Potentially dangerous character '{char}' in command"
        
        # Check for dangerous commands
        dangerous_commands = ['rm', 'rmdir', 'dd', 'mkfs', 'fdisk']
        if command in dangerous_commands:
            return False, f"Command '{command}' requires special approval"
        
        return True, None
    
    @staticmethod
    def validate_network_access(host: str, port: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """Validate network access requests"""
        # Block access to localhost services that might be sensitive
        if host in ['localhost', '127.0.0.1', '::1']:
            sensitive_ports = [22, 23, 25, 53, 80, 443, 993, 995, 3306, 5432, 6379, 27017]
            if port and port in sensitive_ports:
                return False, f"Access to localhost:{port} is restricted"
        
        # Block private network ranges for external tools
        import ipaddress
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private and not ip.is_loopback:
                return False, "Access to private network addresses is restricted"
        except ValueError:
            # Not an IP address, probably a hostname - allow for now
            pass
        
        return True, None



