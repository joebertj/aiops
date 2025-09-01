# Smart Kubernetes MCP Server

A Model Context Protocol (MCP) server that converts natural language prompts directly to Kubernetes API calls, bypassing kubectl entirely.

## 🚀 Features

- **Natural Language Processing**: Convert plain English to Kubernetes operations
- **Direct API Calls**: Uses Kubernetes Python client for direct cluster communication
- **Smart Intent Recognition**: Automatically detects what you want to do
- **Rich Output**: Human-readable summaries with raw data
- **Local Cluster Support**: Works with your local k3d/k3s cluster

## 📁 Files

- `smart_k8s_mcp.py` - Main MCP server with natural language processing
- `interactive_client.py` - Interactive client for testing prompts

## 🛠️ Installation

1. **Install dependencies**:
   ```bash
   pip3 install kubernetes
   ```

2. **Ensure kubectl is configured**:
   ```bash
   kubectl cluster-info
   ```

## 🎯 Usage

### Interactive Mode (Recommended)

Run the interactive client to test natural language prompts:

```bash
python3 interactive_client.py
```

**Example prompts you can try**:
- "Show me the cluster health"
- "What nodes do I have?"
- "Get pods in default namespace"
- "Show me the services"
- "Check cluster status"
- "Get pods from kube-system namespace"
- "Describe pod traefik-5d45fc8cc9-h7vj8"
- "Show me the logs for pod coredns-ccb96694c-wxnc2"
- "Show me all deployments"
- "Get deployment status in kube-system"
- "Check deployment health"

### Direct MCP Server

Run the MCP server directly:

```bash
python3 smart_k8s_mcp.py
```

### Standard Tools Mode

Use the basic MCP server for traditional tool calls:

```bash
python3 kubernetes_mcp_server.py
```

## 🔍 How It Works

1. **Natural Language Input**: You type a prompt like "Show me the cluster health"
2. **Intent Recognition**: The server parses your prompt and identifies the intent
3. **Parameter Extraction**: Automatically extracts namespaces, pod names, etc.
4. **API Call**: Makes direct Kubernetes API calls using the Python client
5. **Smart Output**: Provides human-readable summaries with raw data

## 🧠 Supported Operations

### Cluster Operations
- ✅ Get cluster overview and health
- ✅ List all nodes with status
- ✅ List all namespaces
- ✅ Component status monitoring

### Pod Operations
- ✅ List pods by namespace
- ✅ Get pod details and status
- ✅ Retrieve pod logs
- ✅ Pod health monitoring
- ✅ Pod creation and management
- ✅ Pod binding and eviction

### Service Operations
- ✅ List services by namespace
- ✅ Service configuration details
- ✅ Port and endpoint information
- ✅ Service creation and management
- ✅ Service proxy operations

### Deployment Operations
- ✅ List deployments by namespace
- ✅ Deployment status and replicas
- ✅ Rolling update information
- ✅ Deployment scaling and updates
- ✅ Deployment history and rollbacks
- ✅ Deployment creation and management

### Advanced Operations
- ✅ **ConfigMaps & Secrets**: Management and listing
- ✅ **Persistent Volumes**: Storage management
- ✅ **RBAC**: Role and role binding management
- ✅ **Networking**: Ingress, Network Policies
- ✅ **Storage**: Storage classes, CSI drivers
- ✅ **Batch Jobs**: CronJobs and Jobs
- ✅ **Autoscaling**: HPA management
- ✅ **Policy**: Pod disruption budgets

## 🔧 Configuration

The server automatically detects your Kubernetes configuration:

1. **kubeconfig file** (default: `~/.kube/config`)
2. **In-cluster service account** (if running inside cluster)
3. **Environment variables** (KUBECONFIG, etc.)

## 📊 Example Output

```
🤖 Processing: Show me the cluster health
--------------------------------------------------
🏥 **Cluster Health Overview**

🖥️  **Nodes**: 2 nodes are running
   • 2/2 nodes are ready

📁 **Namespaces**: 5 namespaces
   • 5/5 namespaces are active

📦 **Pods**: 8 pods across all namespaces
   • 7/8 pods are running

📊 Raw Data:
{
  "nodes": [...],
  "namespaces": [...],
  "pods": [...]
}
```

## 🚨 Troubleshooting

### Common Issues

1. **"No module named 'kubernetes'"**
   ```bash
   pip3 install kubernetes
   ```

2. **"Could not load kubeconfig"**
   - Ensure kubectl is configured: `kubectl cluster-info`
   - Check your kubeconfig file: `kubectl config view`

3. **"Failed to connect to cluster"**
   - Verify your cluster is running: `kubectl get nodes`
   - Check cluster status: `kubectl cluster-info`

### Debug Mode

Enable debug logging by modifying the logging level in the server files:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Comprehensive API Capabilities

Your Kubernetes MCP server has access to the full Kubernetes API surface:

### **Core API Groups Available**
- **🔧 Core V1**: Pods, Services, Nodes, Namespaces, ConfigMaps, Secrets
- **🚀 Apps V1**: Deployments, StatefulSets, DaemonSets, ReplicaSets
- **🌐 Networking V1**: Ingress, Network Policies, Service CIDRs
- **🔐 RBAC V1**: Roles, RoleBindings, ClusterRoles, ClusterRoleBindings
- **💾 Storage V1**: Storage Classes, CSI Drivers, Volume Attachments
- **⚡ Batch V1**: Jobs, CronJobs
- **📈 Autoscaling V1**: Horizontal Pod Autoscalers
- **🛡️ Policy V1**: Pod Disruption Budgets

### **Available Operations**
- **Create**: Deployments, Pods, Services, ConfigMaps, Secrets
- **List**: All resources across namespaces
- **Get**: Detailed resource information
- **Update**: Resource modifications and scaling
- **Delete**: Resource cleanup
- **Watch**: Real-time resource monitoring

### **Example Prompts**
- "Show me all deployments"
- "Get deployment status in kube-system"
- "Scale deployment traefik to 3 replicas"
- "Check deployment health"
- "Show deployment history"
- "Create a new nginx deployment"
- "List all storage classes"
- "Show RBAC roles in kube-system"

## 🔮 Future Enhancements

- [ ] Resource creation and management
- [ ] Advanced filtering and search
- [ ] Metrics and monitoring integration
- [ ] Multi-cluster support
- [ ] Custom resource definitions
- [ ] RBAC and security analysis
- [ ] Advanced deployment strategies (Blue/Green, Canary)
- [ ] Deployment automation and CI/CD integration

## 📚 MCP Protocol

This server implements the Model Context Protocol (MCP) specification:

- **JSON-RPC 2.0** communication
- **Standard MCP methods**: `initialize`, `tools/list`, `tools/call`
- **Custom prompt handling**: `prompts/list`, `prompts/call`
- **Structured content responses**

## 🤝 Contributing

Feel free to extend the natural language processing capabilities or add new Kubernetes operations!

## 📄 License

This project is open source and available under the Apache License 2.0.
