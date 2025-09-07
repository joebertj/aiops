# AIOps - AI-Powered Operations Toolkit

**Intelligent automation and management tools for modern infrastructure operations.**

This project showcases AI-first approaches to operations, featuring **awesh** - an AI-aware interactive shell, and supporting MCP (Model Context Protocol) servers for various infrastructure platforms.

## 🌟 Featured Components

### 🐚 **awesh** - AI-Aware Interactive Shell
*"AI by default, Bash when I mean Bash"*

An intelligent shell that automatically routes commands between AI processing and Bash execution based on smart content detection. Perfect for operations teams who want natural language infrastructure management with the reliability of traditional shell commands.

**Key Features:**
- **Smart Routing**: Automatically detects whether input should go to AI or Bash
- **Natural Language Operations**: Ask questions, get summaries, analyze systems
- **Traditional Shell**: Full Bash compatibility for exact commands
- **MCP Integration**: Secure tool execution through Model Context Protocol
- **Streaming Responses**: Real-time AI output with full conversation context

[📖 Learn more about awesh →](./awesh/)

### ⚙️ **Kubernetes MCP Server** 
*Direct natural language to Kubernetes API*

A Model Context Protocol server that converts natural language prompts directly to Kubernetes API calls, bypassing kubectl entirely. Ideal for infrastructure automation and monitoring.

**Key Features:**
- **Natural Language Processing**: Convert plain English to Kubernetes operations  
- **Direct API Calls**: Uses Kubernetes Python client for direct cluster communication
- **Smart Intent Recognition**: Automatically detects what you want to do
- **Rich Output**: Human-readable summaries with raw data
- **Local Cluster Support**: Works with your local k3d/k3s cluster

## 🏗️ Project Structure

```
aiops/
├── awesh/                  # AI-aware interactive shell (showcase)
│   ├── main.py            # Shell entry point
│   ├── router.py          # Command routing logic
│   ├── config.py          # Configuration management
│   └── specs.md           # Detailed specifications
├── kubernetes/            # Kubernetes MCP server
│   ├── smart_k8s_mcp.py  # Natural language K8s server
│   └── interactive_client.py
├── credential_store/      # Secure credential management
├── executor/             # Command execution framework
├── interaction/          # User interaction components  
├── nlp/                  # Natural language processing
├── planner/              # Task planning and orchestration
└── state_store/          # State management
```

## 🚀 Quick Start

### Install awesh (AI-aware Shell)

```bash
cd awesh/
./install.sh
```

Or install manually:
```bash
cd awesh/
pip install -e .
awesh
```

### Try Kubernetes MCP Server

1. **Install dependencies**:
   ```bash
   pip3 install kubernetes
   ```

2. **Ensure kubectl is configured**:
   ```bash
   kubectl cluster-info
   ```

3. **Run interactive mode**:
   ```bash
   cd kubernetes/
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

## 🔮 AIOps Vision & Roadmap

### Core Philosophy
AIOps represents a paradigm shift from traditional infrastructure management to AI-first operations. The goal is to make infrastructure as conversational and intuitive as possible while maintaining the precision and reliability that operations teams require.

### Planned Components
- **🐚 awesh**: AI-aware shell (current showcase)
- **☸️ Kubernetes MCP**: Natural language Kubernetes management (available)
- **🔒 Security MCP**: AI-powered security analysis and remediation
- **📊 Monitoring MCP**: Intelligent alerting and incident response
- **🚀 CI/CD MCP**: Natural language deployment pipelines
- **☁️ Cloud Provider MCPs**: AWS, GCP, Azure natural language management
- **📈 Analytics Engine**: Cross-platform operational intelligence

### Technical Roadmap
- [ ] **awesh v1.0**: Complete AI-aware shell with full MCP integration
- [ ] **Multi-MCP Support**: Connect multiple MCP servers simultaneously  
- [ ] **Advanced NLP**: Context-aware command interpretation
- [ ] **Workflow Automation**: AI-generated operational runbooks
- [ ] **Predictive Operations**: Proactive issue detection and resolution
- [ ] **Team Collaboration**: Shared AI context and knowledge bases

## 🧠 AI-First Operations

This project demonstrates several key principles:

1. **Natural Language Interface**: Operations should be as easy as having a conversation
2. **Context Awareness**: AI should understand your infrastructure and history
3. **Safety by Design**: AI suggestions with human approval workflows
4. **Gradual Adoption**: Works alongside existing tools and processes
5. **Knowledge Sharing**: AI learns from team practices and tribal knowledge

## 📚 Model Context Protocol (MCP)

All AI integrations use the Model Context Protocol for secure, standardized tool execution:

- **🔒 Security**: Strict policy enforcement and audit trails
- **🔧 Extensibility**: Plugin architecture for new infrastructure platforms
- **📊 Observability**: Full logging and monitoring of AI actions
- **🤝 Interoperability**: Works with any MCP-compatible AI system

## 🤝 Contributing

We welcome contributions that advance AI-powered operations:

- **New MCP Servers**: Add support for additional platforms
- **Enhanced NLP**: Improve natural language understanding
- **Safety Features**: Better guardrails and validation
- **Documentation**: Help others adopt AIOps practices

## 📄 License

This project is open source and available under the Apache License 2.0.

---

*AIOps: Where artificial intelligence meets infrastructure operations. Making the complex simple, the manual automatic, and the reactive proactive.*
