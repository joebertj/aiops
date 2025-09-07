# AIOps - AI-Powered Operations Toolkit

**Intelligent automation and management tools for modern infrastructure operations.**

This project showcases AI-first approaches to operations, featuring **awesh** - Awe-Inspired Workspace Environment Shell that serves as a "free cursor" for shell-native AI assistance, plus supporting MCP (Model Context Protocol) servers for various infrastructure platforms.

**💡 Core Vision:** AI assistance in the terminal without IDE bloat - the benefits of AI-powered development without editor overhead or opinionated tool constraints.

## 🧠 Breaking the AI Stigma in Open Source

**AI is Baseline + Human Creativity = Breakthrough Tools**

This project uses AI as the baseline, then pushes further with human creativity to achieve breakthroughs beyond what AI training alone provides. We believe:

- **AI is Baseline**: AI provides the superior baseline capabilities we build upon
- **Human Creativity Pushes Further**: We use human creativity to go beyond AI's training limitations
- **Beyond Training Data**: Human creativity enforces new concepts that weren't in AI's training
- **AI is Starting Point, Not End**: AI serves as our baseline; human creativity is what creates innovation
- **Push Past Boundaries**: Human creativity pushes past what AI learned from training data

**🎯 Our Approach:**
- Use AI as the superior baseline
- Push further with human creativity beyond training patterns
- Implement creative approaches that go beyond what AI learned
- Create novel behaviors that training data couldn't anticipate

**🌟 The Result:** Tools like awesh that represent breakthrough innovation - using AI as the base layer, then implementing non-traditional techniques that contradict conventional training to create AI-aware shells with behaviors no training data could have anticipated.

Open source thrives on experimentation and innovation. AI provides the base infrastructure; non-traditional, training-contradicting techniques are what create genuine breakthroughs.

## 🌟 Featured Components

### 🐚 **awesh** - AIWES (Awe-Inspired Workspace Environment Shell)
*"AI by default, Bash when I mean Bash"*

The flagship component of AIOps - an intelligent shell that seamlessly blends natural language AI interaction with traditional command-line operations. Built for operations teams who want the power of conversational AI without losing the precision of shell commands.

**💡 The "Free Cursor" Concept:**
awesh represents what we really want from AI-assisted development: the AI assistance without the IDE bloat. It's a "free cursor" that's purely shell-based - giving you AI-powered development in your terminal without the overhead of editors or opinionated tool prompts.

**🌟 Core Philosophy:**
- **Zero-Friction AI**: No special syntax - just type naturally
- **Intelligent Routing**: Automatically detects AI vs Bash intent
- **Context-Aware**: Remembers your environment and command history
- **Safety First**: AI suggestions with human control
- **Gradual Adoption**: Works alongside your existing workflow

**🚀 Key Features:**
- **Smart Command Routing**: Detects shell syntax, commands, and natural language automatically
- **OpenAI Integration**: Powered by GPT-4/GPT-5 with configurable models
- **System Prompt Support**: Customizable AI behavior for your operations context  
- **Streaming Responses**: Real-time AI output with conversation continuity
- **Environment Variable Support**: Easy configuration via `~/.aweshrc`
- **MCP Integration**: Secure tool execution through Model Context Protocol
- **Full Bash Compatibility**: All your existing commands work exactly as before

**💡 Example Usage:**
```bash
awesh> ls -la                    # → Bash execution
awesh> what files are here?      # → AI analysis
awesh> find . -name "*.py"       # → Bash execution  
awesh> explain this error        # → AI interpretation
awesh> cd /var/log && analyze the latest errors  # → Mixed AI + Bash
```

**🔧 Installation:**
```bash
cd awesh/
./install.sh
# Configure your OpenAI API key in ~/.aweshrc
awesh
```

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

### Install awesh - AIWES (Awe-Inspired Workspace Environment Shell)

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

**AI Base Layer + Experimental Innovation:** We leverage AI as our base infrastructure layer, then experiment with non-traditional, training-contradicting techniques to create breakthrough solutions. AI provides the foundational capabilities; experimental techniques that contradict training patterns are what create genuine innovation.

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

## 📚 Model Context Protocol (MCP) Servers

AIOps leverages the Model Context Protocol to provide secure, standardized AI tool execution across multiple infrastructure platforms. Each MCP server specializes in a specific domain while maintaining consistent interfaces and security policies.

### 🎯 Available MCP Servers

#### ☸️ **Kubernetes MCP Server**
*Natural language to Kubernetes API - Direct cluster communication*

Our flagship MCP server that converts plain English into direct Kubernetes API calls, bypassing kubectl entirely for more efficient and AI-friendly cluster management.

**🚀 Key Features:**
- **Direct API Access**: Uses Kubernetes Python client for native cluster communication
- **Natural Language Processing**: "Show me unhealthy pods" → API calls + human-readable output
- **Smart Intent Recognition**: Automatically detects operations from conversational input
- **Rich Contextual Output**: Human summaries with raw data for AI consumption
- **Multi-Namespace Support**: Seamlessly works across cluster namespaces
- **Real-time Monitoring**: Live cluster state analysis and reporting

**📋 Supported Operations:**
- **Cluster Health**: Overall cluster status, node health, component monitoring
- **Pod Management**: List, describe, logs, create, delete, scale operations
- **Service Discovery**: Service listing, endpoint analysis, port mapping
- **Deployment Control**: Rollouts, scaling, history, rollback operations
- **Resource Management**: ConfigMaps, Secrets, PVs, Storage Classes
- **RBAC & Security**: Role analysis, permission checking, policy management
- **Batch Operations**: Jobs, CronJobs, scheduled task management

**🔧 Usage:**
```bash
cd kubernetes/
python3 interactive_client.py

# Try these natural language prompts:
"Show me the cluster health"
"What pods are failing in kube-system?"
"Scale the traefik deployment to 3 replicas"
"Show me all services and their endpoints"
```

[📖 Full Kubernetes MCP Documentation →](./kubernetes/)

---

#### 🚀 **Deployment MCP Server** *(Coming Soon)*
*AI-powered deployment automation and pipeline management*

Advanced deployment orchestration with natural language controls for CI/CD pipelines, release management, and deployment strategies.

**🎯 Planned Features:**
- **Pipeline Orchestration**: "Deploy version 2.1.3 to staging"
- **Release Management**: Automated rollback, canary deployments, blue-green strategies
- **Multi-Environment Control**: Development, staging, production deployment flows
- **Integration Hub**: GitHub Actions, GitLab CI, Jenkins, ArgoCD connectivity
- **Deployment Analytics**: Success rates, performance metrics, failure analysis

*Will be copied from `~/AI/kubernetes_web` deployment automation components*

---

#### 🧪 **Test Suite MCP Server** *(Development Paused)*
*Intelligent test execution and quality assurance automation*

Comprehensive testing automation with AI-driven test selection, execution, and result analysis for continuous quality assurance.

**🎯 Planned Features:**
- **Smart Test Selection**: "Run tests affected by the API changes"
- **Quality Gate Management**: Automated pass/fail criteria with AI analysis
- **Test Environment Provisioning**: Dynamic test infrastructure creation
- **Result Intelligence**: AI-powered failure analysis and debugging suggestions
- **Coverage Analysis**: Gap identification and test recommendation

**⚠️ Development Status:**
Development of this MCP server has been paused due to Cursor's AI tool limitations. The tool's opinionated prompts interfere with the strict rule adherence required for safety-critical testing scenarios. Moving to vi + terminal for clean development without tool interference.

*Will be implemented in vi-based development environment and copied from `~/AI/kubernetes_web` test automation framework once completed.*

---

### 🔒 MCP Security & Standards

All MCP servers in AIOps follow strict security and operational standards:

- **🛡️ Policy Enforcement**: Configurable allow-lists for commands and resources
- **📊 Audit Logging**: Complete operation trails with redacted sensitive data  
- **⏱️ Resource Limits**: CPU, memory, and timeout controls for all operations
- **🔐 Authentication**: Integration with existing cluster RBAC and credentials
- **🚨 Safety Controls**: Dry-run modes and confirmation workflows for destructive operations
- **📈 Monitoring**: Built-in metrics and health checks for MCP server performance

### 🔧 MCP Development Framework

The AIOps MCP framework provides:

- **🏗️ Server Templates**: Rapid development of new infrastructure MCP servers
- **🧪 Testing Utilities**: Comprehensive test suites for MCP server validation
- **📚 Documentation Tools**: Auto-generated API docs and usage examples
- **🔄 Hot Reloading**: Development-friendly server restart and configuration updates
- **📊 Performance Profiling**: Built-in metrics and performance analysis tools

## ⚠️ Development Constraints & Limitations

### Cursor IDE Tool Limitations

During development of the Test Suite MCP, we encountered limitations with Cursor's AI tools that prevented proper implementation:

**🚫 Opinionated Tool Prompts**
- Cursor's AI tools introduce their own prompts and rules without user control
- These tool-level prompts conflict with our custom test suite logic and safety rules
- The AI assistant violates the specific rules and constraints we set for our MCP servers
- This makes it impossible to implement domain-specific AI behavior that contradicts the tool's opinions

**📋 Specific Issue:**
- Our Test Suite MCP requires strict rule adherence for safety-critical testing scenarios
- Cursor's tool prompts override our custom behavioral constraints
- The AI ignores project-specific rules in favor of the tool's generic guidelines

**💡 Development Philosophy:**
As vi users, we prefer simple, direct tools that don't impose their own opinions. IDEs are often overkill - vi is sufficient for most development tasks. Even modern alternatives like neovim introduce unnecessary complexity. The best tools get out of your way and let you work.

**🤔 The "Free Cursor" Vision:**
We use Cursor but don't really leverage any of the VSCode features - we just want the AI assistance without the IDE overhead. What we need is a "free cursor" that's purely shell-based: AI assistance in the terminal without the bloated editor interface or opinionated tool prompts.

This is essentially what **awesh** represents - a shell-native AI assistant that provides the benefits of AI-powered development without the constraints of IDE-based tools.

**🔧 Solution:**
- Test Suite MCP development moved to vi + terminal environment  
- Clean development without IDE tool interference
- Direct control over AI behavior and constraints
- **awesh** as the prototype for shell-native AI assistance

This experience reinforces why simple, unopinionated tools are superior for specialized development work.

---

## 🤝 Contributing

We welcome contributions that advance AI-powered operations and break new ground:

- **New MCP Servers**: Add support for additional platforms
- **Enhanced NLP**: Improve natural language understanding  
- **Safety Features**: Better guardrails and validation
- **Documentation**: Help others adopt AIOps practices
- **Novel AI Applications**: Push beyond conventional AI use cases
- **Human-AI Collaboration**: Show how creativity enhances AI capabilities

**🧠 AI-Foundation Development Welcome:**
We encourage and celebrate using AI's superiority as your foundation. Start with AI's superior capabilities, then apply your creativity to transcend training data boundaries. The best contributions use AI as the base and add human concepts that go beyond what AI learned.

**Note:** When contributing MCP servers with custom AI behavior, consider using simple tools like vi + terminal that don't impose their own AI opinions on your specialized use cases.

## 📄 License

This project is open source and available under the Apache License 2.0.

---

*AIOps: Where artificial intelligence meets infrastructure operations. Making the complex simple, the manual automatic, and the reactive proactive.*
