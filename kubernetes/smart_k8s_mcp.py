#!/usr/bin/env python3
"""
Smart Kubernetes MCP Server
Converts natural language prompts directly to Kubernetes API calls
"""

import asyncio
import json
import logging
import sys
import re
from typing import Any, Dict, List, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartKubernetesMCPServer:
    """Smart Kubernetes MCP Server with natural language processing"""
    
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
    
    def parse_natural_language(self, prompt: str) -> Dict[str, Any]:
        """Parse natural language prompt and extract intent and parameters"""
        prompt_lower = prompt.lower()
        
        # Node-related queries
        if any(word in prompt_lower for word in ["node", "nodes", "cluster", "servers"]):
            if "status" in prompt_lower or "health" in prompt_lower:
                return {"action": "get_nodes", "args": {}, "description": "Getting cluster node status and health"}
            elif "capacity" in prompt_lower or "resources" in prompt_lower:
                return {"action": "get_nodes", "args": {}, "description": "Getting cluster node capacity and resources"}
            else:
                return {"action": "get_nodes", "args": {}, "description": "Getting cluster nodes information"}
        
        # Pod-related queries
        elif any(word in prompt_lower for word in ["pod", "pods", "containers"]):
            namespace = self.extract_namespace(prompt)
            if "logs" in prompt_lower:
                pod_name = self.extract_pod_name(prompt)
                if pod_name:
                    return {
                        "action": "get_pod_logs", 
                        "args": {"name": pod_name, "namespace": namespace},
                        "description": f"Getting logs for pod {pod_name}"
                    }
                else:
                    return {"action": "get_all_pods", "args": {}, "description": "Getting all pods across all namespaces"}
            elif "describe" in prompt_lower or "details" in prompt_lower or "info" in prompt_lower:
                pod_name = self.extract_pod_name(prompt)
                if pod_name:
                    return {
                        "action": "describe_pod", 
                        "args": {"name": pod_name, "namespace": namespace},
                        "description": f"Getting detailed information for pod {pod_name}"
                    }
                else:
                    return {"action": "get_all_pods", "args": {}, "description": "Getting all pods across all namespaces"}
            else:
                # If no specific namespace mentioned, get all pods
                if "namespace" not in prompt_lower or "default" in prompt_lower:
                    return {"action": "get_all_pods", "args": {}, "description": "Getting all pods across all namespaces"}
                else:
                    return {"action": "get_pods", "args": {"namespace": namespace}, "description": f"Getting pods in {namespace} namespace"}
        
        # Service-related queries
        elif any(word in prompt_lower for word in ["service", "services", "svc"]):
            namespace = self.extract_namespace(prompt)
            return {"action": "get_services", "args": {"namespace": namespace}, "description": "Getting services information"}
        
        # Deployment-related queries
        elif any(word in prompt_lower for word in ["deployment", "deployments", "deploy"]):
            namespace = self.extract_namespace(prompt)
            if "create" in prompt_lower or "deploy" in prompt_lower:
                # Extract app name from prompt
                app_name = self.extract_app_name(prompt)
                if app_name:
                    return {"action": "create_deployment", "args": {"name": app_name, "namespace": namespace}, "description": f"Creating {app_name} deployment"}
                else:
                    return {"action": "get_deployments", "args": {"namespace": namespace}, "description": "Getting deployments information"}
            else:
                return {"action": "get_deployments", "args": {"namespace": namespace}, "description": "Getting deployments information"}
        
        # Namespace-related queries
        elif any(word in prompt_lower for word in ["namespace", "namespaces", "ns"]):
            return {"action": "get_namespaces", "args": {}, "description": "Getting all namespaces"}
        
        # Health/status queries
        elif any(word in prompt_lower for word in ["health", "status", "overview", "summary"]):
            return {"action": "get_cluster_overview", "args": {}, "description": "Getting cluster health and status overview"}
        
        # Default to cluster overview
        else:
            return {"action": "get_cluster_overview", "args": {}, "description": "Getting general cluster information"}
    
    def extract_namespace(self, prompt: str) -> str:
        """Extract namespace from prompt"""
        # Look for namespace patterns
        patterns = [
            r"in (\w+) namespace",
            r"namespace (\w+)",
            r"from (\w+)",
            r"(\w+) namespace"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "default"
    
    def extract_pod_name(self, prompt: str) -> Optional[str]:
        """Extract pod name from prompt"""
        # Look for pod name patterns
        patterns = [
            r"pod (\w+)",
            r"(\w+) pod",
            r"container (\w+)",
            r"(\w+) container"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_app_name(self, prompt: str) -> Optional[str]:
        """Extract application name from deployment prompt"""
        # Look for app name patterns
        patterns = [
            r"deploy (\w+)",
            r"deploy an? (\w+)",
            r"create (\w+)",
            r"create an? (\w+)",
            r"(\w+) deployment",
            r"deploy (\w+) app"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def handle_prompt(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle natural language prompt and convert to Kubernetes operations"""
        try:
            prompt = message["params"]["arguments"]["prompt"]
            print(f"🤖 Processing prompt: {prompt}", file=sys.stderr)
            
            # Parse the natural language
            parsed = self.parse_natural_language(prompt)
            print(f"🔍 Interpreted as: {parsed['description']}", file=sys.stderr)
            
            # Execute the action
            if parsed["action"] == "get_cluster_overview":
                result = await self.get_cluster_overview(parsed["args"])
            elif parsed["action"] == "get_pods":
                result = await self.get_pods(parsed["args"])
            elif parsed["action"] == "get_all_pods":
                result = await self.get_all_pods(parsed["args"])
            elif parsed["action"] == "get_services":
                result = await self.get_services(parsed["args"])
            elif parsed["action"] == "get_deployments":
                result = await self.get_deployments(parsed["args"])
            elif parsed["action"] == "create_deployment":
                result = await self.create_deployment(parsed["args"])
            elif parsed["action"] == "get_nodes":
                result = await self.get_nodes(parsed["args"])
            elif parsed["action"] == "get_namespaces":
                result = await self.get_namespaces(parsed["args"])
            elif parsed["action"] == "describe_pod":
                result = await self.describe_pod(parsed["args"])
            elif parsed["action"] == "get_pod_logs":
                result = await self.get_pod_logs(parsed["args"])
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Unknown action: {parsed['action']}"
                    }
                }
            
            # Format the response with natural language summary
            summary = self.generate_summary(parsed["action"], result, prompt)
            
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": summary
                        },
                        {
                            "type": "text",
                            "text": f"\n📊 Raw Data:\n{json.dumps(result, indent=2)}"
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing prompt: {e}")
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Error processing prompt: {str(e)}"
                }
            }
    
    def generate_summary(self, action: str, result: Dict[str, Any], original_prompt: str) -> str:
        """Generate natural language summary of the result"""
        if action == "get_cluster_overview":
            nodes = result.get("nodes", [])
            namespaces = result.get("namespaces", [])
            pods = result.get("pods", [])
            
            summary = f"🏥 **Cluster Health Overview**\n\n"
            summary += f"🖥️  **Nodes**: {len(nodes)} nodes are running\n"
            ready_nodes = sum(1 for node in nodes if node.get("ready", False))
            summary += f"   • {ready_nodes}/{len(nodes)} nodes are ready\n\n"
            
            summary += f"📁 **Namespaces**: {len(namespaces)} namespaces\n"
            active_ns = sum(1 for ns in namespaces if ns.get("status") == "Active")
            summary += f"   • {active_ns}/{len(namespaces)} namespaces are active\n\n"
            
            summary += f"📦 **Pods**: {len(pods)} pods across all namespaces\n"
            running_pods = sum(1 for pod in pods if pod.get("status") == "Running")
            summary += f"   • {running_pods}/{len(pods)} pods are running\n"
            
            return summary
            
        elif action == "get_nodes":
            nodes = result.get("nodes", [])
            summary = f"🖥️  **Cluster Nodes** ({len(nodes)} total)\n\n"
            
            for node in nodes:
                status_icon = "🟢" if node.get("ready", False) else "🔴"
                summary += f"{status_icon} **{node['name']}**\n"
                summary += f"   • Status: {'Ready' if node.get('ready') else 'Not Ready'}\n"
                summary += f"   • CPU: {node.get('cpu', 'Unknown')}\n"
                summary += f"   • Memory: {node.get('memory', 'Unknown')}\n"
                summary += f"   • Architecture: {node.get('architecture', 'Unknown')}\n\n"
            
            return summary
            
        elif action == "get_pods":
            pods = result.get("pods", [])
            namespace = result.get("namespace", "default")
            summary = f"📦 **Pods in {namespace} namespace** ({len(pods)} total)\n\n"
            
            for pod in pods:
                status_icon = "🟢" if pod.get("status") == "Running" else "🟡"
                summary += f"{status_icon} **{pod['name']}**\n"
                summary += f"   • Status: {pod.get('status', 'Unknown')}\n"
                summary += f"   • Ready: {pod.get('ready', 'Unknown')}\n"
                summary += f"   • Restarts: {pod.get('restarts', 0)}\n\n"
            
            return summary
            
        elif action == "get_all_pods":
            total_pods = result.get("total_pods", 0)
            namespaces = result.get("namespaces", {})
            summary = f"📦 **All Pods Across All Namespaces** ({total_pods} total)\n\n"
            
            for namespace, pods in namespaces.items():
                summary += f"📁 **{namespace}** ({len(pods)} pods):\n"
                for pod in pods:
                    status_icon = "🟢" if pod.get("status") == "Running" else "🟡"
                    summary += f"  {status_icon} {pod['name']:<30} {pod.get('status', 'Unknown')}\n"
                summary += "\n"
            
            return summary
            
        elif action == "create_deployment":
            deployment = result.get("deployment", {})
            summary = f"🚀 **Deployment Created Successfully!**\n\n"
            summary += f"📋 **Details:**\n"
            summary += f"  • Name: {deployment.get('name', 'Unknown')}\n"
            summary += f"  • Namespace: {deployment.get('namespace', 'Unknown')}\n"
            summary += f"  • Replicas: {deployment.get('replicas', 0)}\n"
            summary += f"  • Available: {deployment.get('available', 0)}\n"
            summary += f"  • Ready: {deployment.get('ready', 0)}\n\n"
            summary += f"✅ {result.get('message', 'Deployment created')}\n"
            
            return summary
            
        elif action == "get_services":
            services = result.get("services", [])
            namespace = result.get("namespace", "default")
            summary = f"🔌 **Services in {namespace} namespace** ({len(services)} total)\n\n"
            
            for svc in services:
                summary += f"🔌 **{svc['name']}**\n"
                summary += f"   • Type: {svc.get('type', 'Unknown')}\n"
                summary += f"   • Cluster IP: {svc.get('cluster_ip', 'None')}\n"
                if svc.get('ports'):
                    summary += f"   • Ports: {', '.join(svc['ports'])}\n"
                summary += "\n"
            
            return summary
            
        else:
            return f"📊 **Result for {action}**\n\n{json.dumps(result, indent=2)}"
    
    async def get_cluster_overview(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive cluster overview"""
        try:
            # Get nodes
            nodes = self.core_v1.list_node()
            nodes_data = [
                {
                    "name": node.metadata.name,
                    "ready": any(cond.type == "Ready" and cond.status == "True" for cond in node.status.conditions),
                    "cpu": node.status.capacity.get("cpu", "Unknown"),
                    "memory": node.status.capacity.get("memory", "Unknown"),
                    "architecture": node.status.node_info.architecture if node.status.node_info else "Unknown"
                }
                for node in nodes.items
            ]
            
            # Get namespaces
            namespaces = self.core_v1.list_namespace()
            namespaces_data = [
                {
                    "name": ns.metadata.name,
                    "status": ns.status.phase
                }
                for ns in namespaces.items
            ]
            
            # Get pods across all namespaces
            pods = self.core_v1.list_pod_for_all_namespaces()
            pods_data = [
                {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase
                }
                for pod in pods.items
            ]
            
            return {
                "nodes": nodes_data,
                "namespaces": namespaces_data,
                "pods": pods_data
            }
            
        except ApiException as e:
            raise Exception(f"Failed to get cluster overview: {e}")
    
    async def get_all_pods(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get pods from all namespaces"""
        try:
            pods = self.core_v1.list_pod_for_all_namespaces()
            
            # Group by namespace
            namespace_pods = {}
            for pod in pods.items:
                namespace = pod.metadata.namespace
                if namespace not in namespace_pods:
                    namespace_pods[namespace] = []
                
                # Handle the ready status properly
                ready_status = 0
                if pod.status.container_statuses:
                    ready_status = sum(1 for cs in pod.status.container_statuses if cs.ready)
                
                namespace_pods[namespace].append({
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ready": ready_status,
                    "restarts": pod.status.container_statuses[0].restart_count if pod.status.container_statuses else 0,
                    "age": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                })
            
            return {
                "all_namespaces": True,
                "total_pods": len(pods.items),
                "namespaces": namespace_pods
            }
        except ApiException as e:
            raise Exception(f"Failed to get all pods: {e}")
    
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
    
    async def create_deployment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new deployment"""
        name = args["name"]
        namespace = args.get("namespace", "default")
        
        try:
            # Create deployment object
            deployment = client.V1Deployment(
                metadata=client.V1ObjectMeta(name=name, namespace=namespace),
                spec=client.V1DeploymentSpec(
                    replicas=1,
                    selector=client.V1LabelSelector(
                        match_labels={"app": name}
                    ),
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(
                            labels={"app": name}
                        ),
                        spec=client.V1PodSpec(
                            containers=[
                                client.V1Container(
                                    name=name,
                                    image=f"{name}:latest" if name != "nginx" else "nginx:latest",
                                    ports=[client.V1ContainerPort(container_port=80)]
                                )
                            ]
                        )
                    )
                )
            )
            
            # Create the deployment
            result = self.apps_v1.create_namespaced_deployment(
                namespace=namespace,
                body=deployment
            )
            
            return {
                "action": "deployment_created",
                "name": name,
                "namespace": namespace,
                "status": "Created",
                "message": f"Successfully created {name} deployment in {namespace} namespace",
                "deployment": {
                    "name": result.metadata.name,
                    "namespace": result.metadata.namespace,
                    "replicas": result.spec.replicas,
                    "available": result.status.available_replicas if result.status.available_replicas else 0,
                    "ready": result.status.ready_replicas if result.status.ready_replicas else 0
                }
            }
            
        except ApiException as e:
            raise Exception(f"Failed to create deployment {name}: {e}")
    
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
        # Write startup messages to stderr so they don't interfere with JSON responses
        print("🚀 Starting Smart Kubernetes MCP Server...", file=sys.stderr)
        print("💡 This server converts natural language prompts to Kubernetes API calls!", file=sys.stderr)
        
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
                    print(f"Invalid JSON: {line}", file=sys.stderr)
                    continue
                
                # Handle different message types
                method = message.get("method")
                if method == "initialize":
                    response = await self.handle_initialization(message)
                elif method == "tools/list":
                    response = await self.handle_list_tools(message)
                elif method == "tools/call":
                    response = await self.handle_call_tool(message)
                elif method == "prompts/list":
                    response = await self.handle_list_prompts(message)
                elif method == "prompts/call":
                    response = await self.handle_prompt(message)
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                
                # Send response to stdout (this is what the client reads)
                response_line = json.dumps(response) + "\n"
                sys.stdout.write(response_line)
                sys.stdout.flush()
                
            except Exception as e:
                print(f"Error processing message: {e}", file=sys.stderr)
                error_response = {
                    "jsonrpc": "2.0",
                    "id": message.get("id") if 'message' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                error_line = json.dumps(error_response) + "\n"
                sys.stdout.write(error_line)
                sys.stdout.flush()
    
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
                    "name": "smart-kubernetes-mcp",
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
                "name": "get_nodes",
                "description": "Get cluster nodes",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
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
    
    async def handle_list_prompts(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list prompts request"""
        prompts = [
            {
                "name": "cluster_health",
                "description": "Check cluster health and status",
                "arguments": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Natural language prompt about cluster health"
                        }
                    },
                    "required": ["prompt"]
                }
            },
            {
                "name": "pod_management",
                "description": "Manage and inspect pods",
                "arguments": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Natural language prompt about pod operations"
                        }
                    },
                    "required": ["prompt"]
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "prompts": prompts
            }
        }
    
    async def handle_call_tool(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request"""
        try:
            tool_name = message["params"]["name"]
            arguments = message["params"].get("arguments", {})
            
            if tool_name == "get_pods":
                result = await self.get_pods(arguments)
            elif tool_name == "get_nodes":
                result = await self.get_nodes(arguments)
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

async def main():
    """Main entry point"""
    server = SmartKubernetesMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
