#!/usr/bin/env python3
"""
Simple test script to get nodes from Kubernetes cluster
"""

from kubernetes import client, config

def main():
    """Get and display cluster nodes"""
    print("🚀 Testing Kubernetes MCP Server - Nodes Functionality")
    print("=" * 60)
    
    try:
        # Load Kubernetes config
        config.load_kube_config()
        print("✅ Loaded Kubernetes config")
        
        # Initialize API client
        core_v1 = client.CoreV1Api()
        print("✅ Connected to Kubernetes cluster")
        
        # Get nodes
        print("\n🔍 Fetching cluster nodes...")
        nodes = core_v1.list_node()
        
        if not nodes.items:
            print("❌ No nodes found in the cluster")
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
        
        print("\n✨ This is what the MCP server would return for 'show me all the nodes'")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
