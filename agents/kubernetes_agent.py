"""
Kubernetes Agent for AIOps System

This agent intercepts Kubernetes-related prompts and uses direct Kubernetes API calls
instead of kubectl. It leverages the existing Kubernetes MCP server for natural language
processing and direct API communication.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import re

from .base_agent import BaseAgent, AgentResult


class KubernetesAgent(BaseAgent):
    """
    Kubernetes Agent that handles Kubernetes-related prompts using direct API calls.
    
    This agent:
    1. Detects Kubernetes-related prompts
    2. Uses the Kubernetes MCP server for natural language processing
    3. Executes direct Kubernetes API calls (no kubectl)
    4. Returns human-readable results
    """
    
    def __init__(self, kubernetes_mcp_path: Optional[str] = None):
        super().__init__("Kubernetes Agent", priority=20)  # Process after security agent
        
        # Path to the Kubernetes MCP server
        self.kubernetes_mcp_path = kubernetes_mcp_path or str(
            Path(__file__).parent.parent / "kubernetes" / "smart_k8s_mcp.py"
        )
        
        # Kubernetes-related keywords and patterns
        self.kubernetes_keywords = {
            'kubernetes', 'k8s', 'kube', 'cluster', 'node', 'nodes', 'pod', 'pods',
            'deployment', 'deployments', 'service', 'services', 'namespace', 'namespaces',
            'configmap', 'configmaps', 'secret', 'secrets', 'ingress', 'ingresses',
            'daemonset', 'daemonsets', 'statefulset', 'statefulsets', 'job', 'jobs',
            'cronjob', 'cronjobs', 'persistentvolume', 'persistentvolumes', 'pvc',
            'replicaset', 'replicasets', 'endpoint', 'endpoints', 'event', 'events',
            'rbac', 'role', 'roles', 'rolebinding', 'rolebindings', 'serviceaccount',
            'serviceaccounts', 'networkpolicy', 'networkpolicies', 'storageclass',
            'storageclasses', 'volume', 'volumes', 'container', 'containers',
            'image', 'images', 'registry', 'helm', 'chart', 'charts'
        }
        
        # Shell command patterns that should NOT be intercepted
        self.shell_patterns = [
            r'^kubectl\s+',  # Direct kubectl commands
            r'^k\s+',        # kubectl alias
            r'^helm\s+',     # Helm commands
            r'^docker\s+',   # Docker commands
            r'^k3d\s+',      # k3d commands
            r'^minikube\s+', # minikube commands
        ]
        
        self.mcp_process = None
        self.mcp_ready = False
    
    def should_handle(self, prompt: str, context: Dict[str, Any]) -> bool:
        """
        Determine if this is a Kubernetes-related prompt that should be handled.
        
        Returns False for direct shell commands (kubectl, helm, etc.)
        """
        prompt_lower = prompt.lower()
        
        # Don't handle direct shell commands
        for pattern in self.shell_patterns:
            if re.match(pattern, prompt_lower):
                return False
        
        # Check for Kubernetes keywords
        words = set(re.findall(r'\b\w+\b', prompt_lower))
        kubernetes_words = words.intersection(self.kubernetes_keywords)
        
        # Handle if we found Kubernetes-related terms
        return len(kubernetes_words) > 0
    
    async def process(self, prompt: str, context: Dict[str, Any]) -> AgentResult:
        """
        Process the Kubernetes prompt using the MCP server.
        """
        try:
            # Start MCP server if not running
            if not self.mcp_ready:
                await self._start_mcp_server()
            
            if not self.mcp_ready:
                return AgentResult(
                    handled=False,
                    response="❌ Failed to start Kubernetes MCP server. Please check your Kubernetes configuration."
                )
            
            # Send prompt to MCP server
            response = await self._send_to_mcp(prompt)
            
            if response:
                return AgentResult(
                    handled=True,
                    response=response,
                    metadata={"agent": "kubernetes", "method": "mcp_api"}
                )
            else:
                return AgentResult(
                    handled=False,
                    response="❌ Failed to get response from Kubernetes MCP server."
                )
                
        except Exception as e:
            return AgentResult(
                handled=False,
                response=f"❌ Kubernetes agent error: {str(e)}"
            )
    
    async def _start_mcp_server(self):
        """Start the Kubernetes MCP server subprocess"""
        try:
            if not Path(self.kubernetes_mcp_path).exists():
                raise FileNotFoundError(f"Kubernetes MCP server not found at {self.kubernetes_mcp_path}")
            
            # Start the MCP server
            self.mcp_process = await asyncio.create_subprocess_exec(
                sys.executable, self.kubernetes_mcp_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                bufsize=0
            )
            
            # Wait a moment for server to start
            await asyncio.sleep(1)
            
            # Initialize the server
            init_success = await self._initialize_mcp()
            self.mcp_ready = init_success
            
        except Exception as e:
            print(f"Failed to start Kubernetes MCP server: {e}", file=sys.stderr)
            self.mcp_ready = False
    
    async def _initialize_mcp(self) -> bool:
        """Initialize the MCP server"""
        try:
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "kubernetes-agent",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self._send_mcp_message(init_message)
            return "result" in response and "serverInfo" in response.get("result", {})
            
        except Exception as e:
            print(f"Failed to initialize MCP server: {e}", file=sys.stderr)
            return False
    
    async def _send_to_mcp(self, prompt: str) -> Optional[str]:
        """Send a prompt to the MCP server and get response"""
        try:
            # Send prompt using the cluster_health prompt
            prompt_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "prompts/call",
                "params": {
                    "name": "cluster_health",
                    "arguments": {
                        "prompt": prompt
                    }
                }
            }
            
            response = await self._send_mcp_message(prompt_message)
            
            if "result" in response and "content" in response["result"]:
                # Extract text content from response
                content_parts = []
                for item in response["result"]["content"]:
                    if item.get("type") == "text":
                        content_parts.append(item["text"])
                
                return "\n".join(content_parts) if content_parts else None
            
            return None
            
        except Exception as e:
            print(f"Error sending prompt to MCP: {e}", file=sys.stderr)
            return None
    
    async def _send_mcp_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC message to the MCP server"""
        if not self.mcp_process or not self.mcp_process.stdin:
            raise Exception("MCP server not running")
        
        try:
            # Send message
            message_line = json.dumps(message) + "\n"
            self.mcp_process.stdin.write(message_line.encode())
            await self.mcp_process.stdin.drain()
            
            # Wait for response
            await asyncio.sleep(0.2)
            
            # Read response
            if self.mcp_process.stdout.at_eof():
                raise Exception("MCP server closed stdout")
            
            response_line = await self.mcp_process.stdout.readline()
            if response_line:
                response_text = response_line.decode().strip()
                if response_text:
                    return json.loads(response_text)
            
            raise Exception("No response from MCP server")
            
        except Exception as e:
            print(f"Error communicating with MCP server: {e}", file=sys.stderr)
            raise
    
    def get_help(self) -> str:
        """Get help text for the Kubernetes agent"""
        return """
Kubernetes Agent - Handles Kubernetes operations using direct API calls

This agent intercepts Kubernetes-related prompts and uses the Kubernetes MCP server
to convert natural language to direct Kubernetes API calls, bypassing kubectl entirely.

Supported operations:
• Cluster health and status monitoring
• Pod management (list, describe, logs, create)
• Service discovery and management  
• Deployment operations (scale, update, rollback)
• Namespace and resource management
• Node and cluster information
• ConfigMaps, Secrets, and other resources

Examples:
• "Show me the cluster health"
• "What pods are running in default namespace?"
• "Get logs for pod my-app-123"
• "Scale deployment webapp to 3 replicas"
• "List all services in kube-system"

Note: Direct kubectl/helm commands are passed through to shell execution.
"""
    
    async def cleanup(self):
        """Clean up MCP server process"""
        if self.mcp_process:
            self.mcp_process.terminate()
            await self.mcp_process.wait()
            self.mcp_process = None
            self.mcp_ready = False
