#!/usr/bin/env python3
"""
Simple Kubernetes Client
Connects to local cluster and shows basic information
"""

import json
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def setup_kubernetes_client():
    """Initialize Kubernetes client with local cluster config"""
    try:
        # Try to load from kubeconfig file (default location)
        config.load_kube_config()
        print("✓ Loaded Kubernetes config from kubeconfig file")
    except Exception as e:
        try:
            # Try to load from service account (in-cluster)
            config.load_incluster_config()
            print("✓ Loaded Kubernetes config from in-cluster service account")
        except Exception as e2:
            print(f"⚠ Could not load kubeconfig: {e}")
            print(f"⚠ Could not load in-cluster config: {e2}")
            print("ℹ Using default config - ensure kubectl is configured")
    
    # Initialize API clients
    core_v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    return core_v1, apps_v1

def get_nodes(core_v1):
    """Get cluster nodes"""
    try:
        print("\n🔍 Fetching cluster nodes...")
        nodes = core_v1.list_node()
        
        if not nodes.items:
            print("No nodes found in the cluster")
            return
        
        print(f"\n📊 Found {len(nodes.items)} node(s):")
        print("=" * 80)
        
        for i, node in enumerate(nodes.items, 1):
            print(f"\nNode {i}: {node.metadata.name}")
            print("-" * 40)
            
            # Status
            ready_status = "🟢 Ready" if any(cond.type == "Ready" and cond.status == "True" for cond in node.status.conditions) else "🔴 Not Ready"
            print(f"Status: {ready_status}")
            
            # Conditions
            if node.status.conditions:
                print("Conditions:")
                for cond in node.status.conditions:
                    status_icon = "✅" if cond.status == "True" else "❌"
                    print(f"  {status_icon} {cond.type}: {cond.status}")
            
            # Capacity
            if node.status.capacity:
                print("Capacity:")
                for resource, value in node.status.capacity.items():
                    print(f"  {resource}: {value}")
            
            # Labels
            if node.metadata.labels:
                print("Labels:")
                for key, value in node.metadata.labels.items():
                    print(f"  {key}: {value}")
            
            # Creation time
            if node.metadata.creation_timestamp:
                print(f"Created: {node.metadata.creation_timestamp}")
                
    except ApiException as e:
        print(f"❌ Failed to get nodes: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def get_namespaces(core_v1):
    """Get all namespaces"""
    try:
        print("\n🔍 Fetching namespaces...")
        namespaces = core_v1.list_namespace()
        
        if not namespaces.items:
            print("No namespaces found")
            return
        
        print(f"\n📁 Found {len(namespaces.items)} namespace(s):")
        print("=" * 50)
        
        for ns in namespaces.items:
            status_icon = "🟢" if ns.status.phase == "Active" else "🔴"
            print(f"{status_icon} {ns.metadata.name:<20} {ns.status.phase}")
            
    except ApiException as e:
        print(f"❌ Failed to get namespaces: {e}")

def get_pods_summary(core_v1):
    """Get a summary of pods across all namespaces"""
    try:
        print("\n🔍 Fetching pods summary...")
        pods = core_v1.list_pod_for_all_namespaces()
        
        if not pods.items:
            print("No pods found")
            return
        
        # Group by namespace
        namespace_pods = {}
        for pod in pods.items:
            namespace = pod.metadata.namespace
            if namespace not in namespace_pods:
                namespace_pods[namespace] = []
            namespace_pods[namespace].append(pod)
        
        print(f"\n📦 Found {len(pods.items)} pod(s) across {len(namespace_pods)} namespace(s):")
        print("=" * 60)
        
        for namespace, pods_list in namespace_pods.items():
            print(f"\n📁 {namespace} ({len(pods_list)} pods):")
            for pod in pods_list:
                status_icon = "🟢" if pod.status.phase == "Running" else "🟡"
                print(f"  {status_icon} {pod.metadata.name:<30} {pod.status.phase}")
                
    except ApiException as e:
        print(f"❌ Failed to get pods: {e}")

def main():
    """Main function"""
    print("🚀 Kubernetes Cluster Inspector")
    print("=" * 40)
    
    try:
        # Setup client
        core_v1, apps_v1 = setup_kubernetes_client()
        
        # Test connection
        try:
            # Try to get API version to test connection
            api_resources = core_v1.get_api_resources()
            print("✓ Successfully connected to Kubernetes cluster!")
        except Exception as e:
            print(f"❌ Failed to connect to cluster: {e}")
            print("💡 Make sure your kubectl is configured and cluster is running")
            return
        
        # Get cluster information
        get_namespaces(core_v1)
        get_nodes(core_v1)
        get_pods_summary(core_v1)
        
        print("\n✨ Cluster inspection complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
