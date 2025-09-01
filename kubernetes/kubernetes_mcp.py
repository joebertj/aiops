#!/usr/bin/env python3
"""
Kubernetes MCP Server
Provides Kubernetes cluster operations through Model Context Protocol
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from mcp import Server
from mcp.server import StdioServerParameters
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KubernetesMCPServer:
    def __init__(self):
        self.server = Server("kubernetes-mcp")
        self.setup_handlers()
        self.setup_kubernetes_client()
    
    def setup_kubernetes_client(self):
        """Initialize Kubernetes client with local cluster config"""
        try:
            # Try to load from kubeconfig file (default location)
            config.load_kube_config()
            logger.info("Loaded Kubernetes config from kubeconfig file")
        except Exception as e:
            try:
                # Try to load from service account (in-cluster)
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
        
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools(request: ListToolsRequest) -> ListToolsResult:
            """List available Kubernetes tools"""
            tools = [
                Tool(
                    name="get_pods",
                    description="Get pods from a namespace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "namespace": {
                                "type": "string",
                                "description": "Namespace to get pods from (default: default)"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_services",
                    description="Get services from a namespace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "namespace": {
                                "type": "string",
                                "description": "Namespace to get services from (default: default)"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_deployments",
                    description="Get deployments from a namespace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "namespace": {
                                "type": "string",
                                "description": "Namespace to get deployments from (default: default)"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_nodes",
                    description="Get cluster nodes",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_namespaces",
                    description="Get all namespaces",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="describe_pod",
                    description="Get detailed information about a specific pod",
                    inputSchema={
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
                ),
                Tool(
                    name="get_pod_logs",
                    description="Get logs from a specific pod",
                    inputSchema={
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
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls for Kubernetes operations"""
            try:
                if request.name == "get_pods":
                    result = await self.get_pods(request.arguments)
                elif request.name == "get_services":
                    result = await self.get_services(request.arguments)
                elif request.name == "get_deployments":
                    result = await self.get_deployments(request.arguments)
                elif request.name == "get_nodes":
                    result = await self.get_nodes(request.arguments)
                elif request.name == "get_namespaces":
                    result = await self.get_namespaces(request.arguments)
                elif request.name == "describe_pod":
                    result = await self.describe_pod(request.arguments)
                elif request.name == "get_pod_logs":
                    result = await self.get_pod_logs(request.arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {request.name}")]
                    )
                
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, indent=2))]
                )
                
            except Exception as e:
                logger.error(f"Error in tool call: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")]
                )
    
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
                        "ready": any(cond.type == "Ready" and cond.status == "True" for cond in node.status.conditions)
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
        async with stdio_server(StdioServerParameters()) as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="kubernetes-mcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={}
                    )
                )
            )

async def main():
    """Main entry point"""
    server = KubernetesMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
