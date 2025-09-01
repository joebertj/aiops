#!/usr/bin/env python3
"""
Kubernetes MCP Server
A complete Model Context Protocol server implementation for Kubernetes operations
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KubernetesMCPServer:
    """Kubernetes MCP Server implementation"""
    
    def __init__(self):
        self.setup_kubernetes_client()
        self.request_id = 0
        
    def setup_kubernetes_client(self):
        """Initialize Kubernetes client with local cluster config"""
        try:
            config.load_kube_config()
            logger.info("Loaded Kubernetes config from kubeconfig file")
        except Exception as e:
            try:
                config.load_incluster_config()
                logger.info("Loaded Kubernetes config from in-cluster service account")
            except Exception as e2:
                logger.warning(f"Could not load kubeconfig: {e}")
                logger.warning(f"Could not load in-cluster config: {e2}")
                logger.info("Using default config - ensure kubectl is configured")
        
        # Initialize API clients
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        self.rbac_v1 = client.RbacAuthorizationV1Api()
    
    def get_next_request_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    async def handle_initialization(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialization request"""
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "kubernetes-mcp",
                    "version": "1.0.0"
                }
            }
        }
    
    async def handle_list_tools(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list tools request"""
        tools = [
            {
                "name": "get_pods",
                "description": "Get pods from a namespace",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "Namespace to get pods from (default: default)"
                        }
                    }
                }
            },
            {
                "name": "get_services",
                "description": "Get services from a namespace",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "Namespace to get services from (default: default)"
                        }
                    }
                }
            },
            {
                "name": "get_deployments",
                "description": "Get deployments from a namespace",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "Namespace to get deployments from (default: default)"
                        }
                    }
                }
            },
            {
                "name": "get_nodes",
                "description": "Get cluster nodes",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_namespaces",
                "description": "Get all namespaces",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "describe_pod",
                "description": "Get detailed information about a specific pod",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the pod"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Namespace of the pod (default: default)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "get_pod_logs",
                "description": "Get logs from a specific pod",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the pod"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Namespace of the pod (default: default)"
                        },
                        "container": {
                            "type": "string",
                            "description": "Container name (optional)"
                        },
                        "tail_lines": {
                            "type": "integer",
                            "description": "Number of lines to return (default: 100)"
                        }
                    },
                    "required": ["name"]
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "tools": tools
            }
        }
    
    async def handle_call_tool(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request"""
        try:
            tool_name = message["params"]["name"]
            arguments = message["params"].get("arguments", {})
            
            if tool_name == "get_pods":
                result = await self.get_pods(arguments)
            elif tool_name == "get_services":
                result = await self.get_services(arguments)
            elif tool_name == "get_deployments":
                result = await self.get_deployments(arguments)
            elif tool_name == "get_nodes":
                result = await self.get_nodes(arguments)
            elif tool_name == "get_namespaces":
                result = await self.get_namespaces(arguments)
            elif tool_name == "describe_pod":
                result = await self.describe_pod(arguments)
            elif tool_name == "get_pod_logs":
                result = await self.get_pod_logs(arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {tool_name}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in tool call: {e}")
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def get_pods(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get pods from a namespace"""
        namespace = args.get("namespace", "default")
        try:
            pods = self.core_v1.list_namespaced_pod(namespace=namespace)
            return {
                "namespace": namespace,
                "pods": [
                    {
                        "name": pod.metadata.name,
                        "status": pod.status.phase,
                        "ready": pod.status.ready,
                        "restarts": pod.status.container_statuses[0].restart_count if pod.status.container_statuses else 0,
                        "age": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                    }
                    for pod in pods.items
                ]
            }
        except ApiException as e:
            raise Exception(f"Failed to get pods: {e}")
    
    async def get_services(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get services from a namespace"""
        namespace = args.get("namespace", "default")
        try:
            services = self.core_v1.list_namespaced_service(namespace=namespace)
            return {
                "namespace": namespace,
                "services": [
                    {
                        "name": svc.metadata.name,
                        "type": svc.spec.type,
                        "cluster_ip": svc.spec.cluster_ip,
                        "ports": [f"{port.port}:{port.target_port}" for port in svc.spec.ports] if svc.spec.ports else []
                    }
                    for svc in services.items
                ]
            }
        except ApiException as e:
            raise Exception(f"Failed to get services: {e}")
    
    async def get_deployments(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get deployments from a namespace"""
        namespace = args.get("namespace", "default")
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
            return {
                "namespace": namespace,
                "deployments": [
                    {
                        "name": dep.metadata.name,
                        "replicas": dep.spec.replicas,
                        "available": dep.status.available_replicas,
                        "ready": dep.status.ready_replicas,
                        "updated": dep.status.updated_replicas
                    }
                    for dep in deployments.items
                ]
            }
        except ApiException as e:
            raise Exception(f"Failed to get deployments: {e}")
    
    async def get_nodes(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get cluster nodes"""
        try:
            nodes = self.core_v1.list_node()
            return {
                "nodes": [
                    {
                        "name": node.metadata.name,
                        "status": node.status.conditions[-1].type if node.status.conditions else "Unknown",
                        "cpu": node.status.capacity.get("cpu", "Unknown"),
                        "memory": node.status.capacity.get("memory", "Unknown"),
                        "ready": any(cond.type == "Ready" and cond.status == "True" for cond in node.status.conditions),
                        "architecture": node.status.node_info.architecture if node.status.node_info else "Unknown",
                        "kubelet_version": node.status.node_info.kubelet_version if node.status.node_info else "Unknown"
                    }
                    for node in nodes.items
                ]
            }
        except ApiException as e:
            raise Exception(f"Failed to get nodes: {e}")
    
    async def get_namespaces(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get all namespaces"""
        try:
            namespaces = self.core_v1.list_namespace()
            return {
                "namespaces": [
                    {
                        "name": ns.metadata.name,
                        "status": ns.status.phase,
                        "age": ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else None
                    }
                    for ns in namespaces.items
                ]
            }
        except ApiException as e:
            raise Exception(f"Failed to get namespaces: {e}")
    
    async def describe_pod(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a specific pod"""
        name = args["name"]
        namespace = args.get("namespace", "default")
        try:
            pod = self.core_v1.read_namespaced_pod(name=name, namespace=namespace)
            return {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "containers": [
                    {
                        "name": container.name,
                        "image": container.image,
                        "ready": any(cs.ready for cs in pod.status.container_statuses if cs.name == container.name) if pod.status.container_statuses else False
                    }
                    for container in pod.spec.containers
                ],
                "labels": pod.metadata.labels,
                "annotations": pod.metadata.annotations,
                "creation_timestamp": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
            }
        except ApiException as e:
            raise Exception(f"Failed to get pod {name}: {e}")
    
    async def get_pod_logs(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get logs from a specific pod"""
        name = args["name"]
        namespace = args.get("namespace", "default")
        container = args.get("container")
        tail_lines = args.get("tail_lines", 100)
        
        try:
            logs = self.core_v1.read_namespaced_pod_log(
                name=name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines
            )
            return {
                "pod": name,
                "namespace": namespace,
                "container": container,
                "tail_lines": tail_lines,
                "logs": logs
            }
        except ApiException as e:
            raise Exception(f"Failed to get logs for pod {name}: {e}")
    
    async def run(self):
        """Run the MCP server"""
        logger.info("🚀 Starting Kubernetes MCP Server...")
        
        while True:
            try:
                # Read input line
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {line}")
                    continue
                
                # Handle different message types
                method = message.get("method")
                if method == "initialize":
                    response = await self.handle_initialization(message)
                elif method == "tools/list":
                    response = await self.handle_list_tools(message)
                elif method == "tools/call":
                    response = await self.handle_call_tool(message)
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                
                # Send response
                response_line = json.dumps(response) + "\n"
                await asyncio.get_event_loop().run_in_executor(None, sys.stdout.write, response_line)
                await asyncio.get_event_loop().run_in_executor(None, sys.stdout.flush)
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": message.get("id") if 'message' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                error_line = json.dumps(error_response) + "\n"
                await asyncio.get_event_loop().run_in_executor(None, sys.stdout.write, error_line)
                await asyncio.get_event_loop().run_in_executor(None, sys.stdout.flush)

async def main():
    """Main entry point"""
    server = KubernetesMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
