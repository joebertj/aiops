# AIOps - AI-Powered Operations Toolkit

**Intelligent automation and management tools for modern infrastructure operations.**

This project showcases AI-first approaches to operations, featuring **awesh** - Awe-Inspired Workspace Environment Shell that serves as a "free cursor" for shell-native AI assistance, plus supporting MCP (Model Context Protocol) servers for various infrastructure platforms.

**💡 Core Vision:** AI assistance in the terminal without IDE bloat - the benefits of AI-powered development without editor overhead or opinionated tool constraints.

## 🚀 awesh - AI-Aware Interactive Shell

![awesh](awesh/awesh.png)

**awesh** is the centerpiece of this toolkit - an AI-aware interactive shell that provides intelligent assistance while preserving all the power and familiarity of traditional bash operations.

## ⚡ Quickstart - Get awesh Running Fast

### 🚀 One-Command Installation
```bash
# Clone and install awesh in one go
git clone https://github.com/joebertj/aiops.git
cd aiops
python3 deployment/deployment_mcp.py clean_install
```

### 🔑 Configure Your API Key
```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your_api_key_here
export OPENAI_MODEL=gpt-5

# Optional: Use OpenRouter instead
export AI_PROVIDER=openrouter
export OPENROUTER_API_KEY=your_openrouter_key_here
export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

### 🎯 Start Using awesh
```bash
# Launch awesh
awesh

# Try these examples:
> find all files that is recently edited
> show me the system status
> list all python processes
> what's taking up disk space?
```

### 🛠️ Development Workflow
```bash
# Fast development cycle with Deployment MCP
python3 deployment/deployment_mcp.py build_clean    # Build only
python3 deployment/deployment_mcp.py deploy_only    # Deploy only
python3 deployment/deployment_mcp.py clean_install  # Full cycle
```

### 🔧 Configuration
```bash
# Edit ~/.aweshrc for persistent settings
VERBOSE=1                    # 0=silent, 1=info, 2=debug
AI_PROVIDER=openai          # openai or openrouter
MODEL=gpt-5                 # AI model to use
```

### 🎮 Control Commands
```bash
# Inside awesh
aweh                        # Show help and all available commands
awes                        # Show verbose status (API provider, model, debug state)
awea                        # Show current AI provider and model
awea openai                 # Switch to OpenAI
awea openrouter             # Switch to OpenRouter
awem                        # Show current model
awem gpt-4                  # Set model to GPT-4
awem gpt-3.5-turbo          # Set model to GPT-3.5 Turbo
awem claude-3               # Set model to Claude 3
awev                        # Show verbose level
awev 0/1/2                  # Set verbose level
awev on/off                 # Enable/disable verbose
```

**That's it!** You now have AI-powered shell assistance with security middleware, intelligent command routing, and full bash compatibility.

## 📖 Related Reading

**[AIOps: Artificial Intelligence for IT Operations](https://www.amazon.com/dp/B0FNKKXFPQ)** - A comprehensive guide to the AI revolution in IT operations, documenting real-world transformations and practical implementation strategies. Written by the creator of this toolkit, it provides the theoretical foundation and strategic insights behind these tools.

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

**💎 Naming Inspiration:**
awesh draws its name from my eldest daughter, **Awit Perl** - where "Awit" means "Psalm" in Filipino, representing both "Awe" and "Wit," while "Perl" means "Pearl" (still more OG than the Python we have today). This shell embodies the same wonder and wisdom that inspired its creation.

The flagship component of AIOps - an intelligent shell that seamlessly blends natural language AI interaction with traditional command-line operations. **Built by Ops, for Ops** - designed for systems administrators, DevOps engineers, and infrastructure professionals who live in the terminal.

**💡 The "Free Cursor" Concept:**
awesh represents what we really want from AI-assisted development: the AI assistance without the IDE bloat. It's a "free cursor" that's purely shell-based - giving you AI-powered development in your terminal without the overhead of editors or opinionated tool prompts.

**🌍 Democratizing AI-Powered Development:**
awesh brings the **Cursor/Claude Code experience to every shell**, democratizing AI-assisted development by making it a **shell primitive**, not an editor feature:

- **🚀 Universal Access**: Any Linux/Unix system becomes AI-powered - no editor lock-in
- **⚡ Shell-Native AI**: Natural language commands get AI interpretation and auto-execution  
- **🔄 Intent Recognition**: "read md files" → AI understands → `ls *.md` → Shows results seamlessly
- **🛠️ Tool Integration**: Works with vi, nano, grep, git - your existing workflow enhanced
- **🔓 Open Ecosystem**: Not dependent on proprietary platforms or specific editors

Instead of being locked into AI editors, **every shell becomes an AI-powered operations environment**. This democratizes access to AI-assisted infrastructure management for anyone with a terminal.

**🔧 The Ops-First Philosophy:**
awesh embraces the **minimalistic yet powerful** approach that operations professionals know and love:

- **🖥️ Shell + vi Workflow**: Designed for those who live in terminals and edit with vi/vim
- **⚡ No IDE Bloat**: Pure shell experience - familiar, fast, and efficient
- **🛠️ Infrastructure-Focused**: Built for system administration, not application development  
- **📊 Ops Mindset**: Troubleshooting, monitoring, deployment - operations tasks first
- **🔍 Minimal Learning Curve**: If you know bash and vi, you know awesh

**For the shell/vi professional** who wants AI assistance without abandoning the minimalistic, powerful tools that make operations efficient.

**🎯 Ideal Test Users:**
A 23-year terminal veteran is the perfect test user for writing an AI-enhanced terminal - not developers who spent time in advanced IDEs pampered by so much GUI tooling. Experienced terminal users understand the real workflow, know what's actually needed, and can identify when AI assistance genuinely enhances rather than complicates the shell experience.

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
awesh> ls -la                              # → Sandbox validation → Direct execution
awesh> what files are here?                # → Sandbox validation → AI query via middleware
awesh> find . -name "*.py"                 # → Sandbox validation → Direct execution  
awesh> explain this error                  # → Sandbox validation → AI query via middleware
awesh> cat file.txt | grep error           # → Sandbox validation → Direct execution
awesh> summarize this directory structure  # → Sandbox validation → AI query via middleware
awesh> why did the build fail?             # → Sandbox validation → AI query via middleware
awesh> awem gpt-4                          # → Built-in command (set model)
awesh> awev 1                              # → Built-in command (enable verbose)
```

**"AI by default, Bash when I mean Bash."**

**🔧 Installation:**
```bash
# Use deployment MCP for clean installation with virtual environment
cd deployment/
python3 deployment_mcp.py clean_install

# Configure your OpenAI API key
export OPENAI_API_KEY=your_api_key_here
awesh
```

**🐍 Virtual Environment Enforcement:**
AIOps automatically uses a Python virtual environment for all operations, ensuring:
- **Dependency isolation** from system Python packages
- **Consistent environments** across different systems  
- **Clean deployments** with reproducible setups
- **No conflicts** with system-installed packages

The deployment script automatically creates and manages the virtual environment, installing all dependencies in isolation. See [VENV_SETUP.md](VENV_SETUP.md) for detailed information.

**🔧 Configuration:**
Set these environment variables in your shell:

```bash
# AI Provider Configuration
export AI_PROVIDER=openai                    # openai or openrouter
export OPENAI_MODEL=gpt-5                   # Model to use
export OPENAI_API_KEY=sk-proj-abc123...xyz  # Your OpenAI API key (truncated)

# OpenRouter Configuration (if using openrouter)
export OPENROUTER_API_KEY=sk-or-v1-abc...xyz # Your OpenRouter API key (truncated)
export OPENROUTER_MODEL=anthropic/claude-3-sonnet

# Display Options  
export VERBOSE=1              # 0=silent, 1=info, 2=debug (default: 1)

# File Agent Options
export FILE_AGENT_ENABLED=1           # 1=enabled, 0=disabled (default: 1)
# Note: AI prompt enhancement is always enabled for built-in agents
export FILE_AGENT_MAX_FILE_SIZE=50000 # Max size per file in bytes (default: 50000)
export FILE_AGENT_MAX_TOTAL_CONTENT=10000 # Max total content to inject (default: 10000)
export FILE_AGENT_MAX_FILES=5         # Max number of files to include (default: 5)
```

**Example configuration:**
```bash
export AI_PROVIDER=openai
export OPENAI_MODEL=gpt-5
export OPENAI_API_KEY=sk-proj-JrUoBu9D4iCb...T3BlbkFJMEjXf8l0w9SPKE-Rw
export VERBOSE=1
```

**⚠️ Testing Status:**
> **Currently optimized for OpenAI GPT-5**: awesh is actively tested and developed using OpenAI's GPT-5 model. While OpenRouter and other AI providers are supported, they may exhibit unexpected behavior or suboptimal performance. We recommend using OpenAI with GPT-5 for the most reliable experience while we continue testing and improving compatibility with other providers.

**🎛️ Control Commands:**
```bash
# Help & Status
aweh            # Show all available awesh control commands
awes            # Show verbose status (API provider, model, debug state)
awea            # Show current AI provider and model

# Model Management
awem            # Show current model
awem gpt-4      # Set model to GPT-4
awem gpt-3.5-turbo # Set model to GPT-3.5 Turbo
awem claude-3   # Set model to Claude 3

# Verbose Debug Control
awev            # Show verbose level status
awev 0          # Set verbose level 0 (silent)
awev 1          # Set verbose level 1 (info)
awev 2          # Set verbose level 2 (debug)
awev on         # Enable verbose logging (level 1)
awev off        # Disable verbose logging (level 0)

# AI Provider Switching
awea openai     # Switch to OpenAI (GPT models)
awea openrouter # Switch to OpenRouter (multiple providers)
```

*Control commands use the `awe` prefix to avoid conflicts with bash builtins and create a clean namespace for awesh operations.*

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

### Install awesh

```bash
# Use deployment MCP for clean installation with virtual environment
cd deployment/
python3 deployment_mcp.py clean_install
```

**🐍 Virtual Environment Benefits:**
- **Automatic setup**: Creates isolated Python environment
- **Dependency management**: Installs all packages in venv
- **Clean deployment**: No system Python conflicts
- **Reproducible builds**: Same environment everywhere

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

## 🚀 Deployment MCP

The Deployment MCP provides comprehensive CI/CD automation for awesh with two main modes: **CI Build** (development) and **Production Install** (deployment). It handles complete pipelines with syntax checking, process management, git operations, and sanity testing.

### Features

- **🏗️ CI/CD Pipelines**: Separate build (CI) and install (deploy) workflows
- **🔍 Syntax Checking**: Validates C code and Python code before deployment
- **🔨 Build Management**: Clean builds, compilation with proper flags
- **🛑 Process Management**: Kill running awesh processes and clean up sockets  
- **📦 Deployment**: Install binaries to `~/.local/bin` with backup
- **🧪 Sanity Testing**: Test socket communication and backend functionality
- **📝 Git Integration**: Automated git pull, commit, and push operations

### Usage

The Deployment MCP is a standalone Python script that doesn't require external MCP libraries:

```bash
cd deployment/
python3 deployment_mcp.py [command]
```

### Available Commands

#### CI/CD Pipelines
```bash
# CI Build Pipeline (Development)
# Checks → Bins → Git push
python3 deployment_mcp.py build

# Production Install Pipeline (Deployment)  
# Git pull → Skip build → Kill procs → Copies
python3 deployment_mcp.py install

# Clean Install Pipeline (Development)
# Checks → Kill procs → Build → Deploy → Git push (no git pull)
python3 deployment_mcp.py clean_install
```

#### Individual Operations
```bash
# Check syntax for C and Python code
python3 deployment_mcp.py syntax_check

# Build awesh (incremental)
python3 deployment_mcp.py build_only

# Build awesh (clean build)
python3 deployment_mcp.py build_clean

# Kill running awesh processes
python3 deployment_mcp.py kill

# Force kill processes (SIGKILL)
python3 deployment_mcp.py kill_force

# Deploy binary to ~/.local/bin
python3 deployment_mcp.py deploy_only

# Test deployment and backend communication
python3 deployment_mcp.py test

# Git operations
python3 deployment_mcp.py git_pull   # Pull latest changes
python3 deployment_mcp.py git_push   # Commit and push changes
```

### Pipeline Workflows

#### CI Build Pipeline (`build`)
*For development - checks, bins, git push*

1. **📋 Checks**: Validates all C and Python code syntax
2. **🔨 Bins**: Clean build of C frontend + Python backend installation  
3. **📝 Git Push**: Commit changes and push to repository

#### Production Install Pipeline (`install`)
*For deployment - git pull, skip build, kills procs, copies*

1. **📥 Git Pull**: Pull latest changes from repository
2. **🛑 Kill Procs**: Terminates existing awesh processes
3. **📦 Copies**: Install binary to `~/.local/bin` with backup

#### Clean Install Pipeline (`clean_install`)
*For development - build and deploy without git pull*

1. **📋 Checks**: Validates all C and Python code syntax
2. **🛑 Kill Procs**: Terminates existing awesh processes
3. **🔨 Build**: Clean build of C frontend + Python backend installation
4. **📦 Deploy**: Install binary to `~/.local/bin` with backup
5. **📝 Git Push**: Commit changes and push to repository

### Example Output

```bash
$ python3 deployment_mcp.py full_deploy
🚀 Starting full deployment pipeline...

📋 Step 1: Syntax Check
🔍 Checking C syntax...
✅ awesh.c: Syntax OK
🔍 Checking Python syntax...  
✅ server.py: Syntax OK
✅ ai_client.py: Syntax OK

🛑 Step 2: Kill Existing Processes
🛑 Terminated awesh (PID: 12345)
🧹 Removed socket: /home/user/.awesh.sock

🔨 Step 3: Build
🧹 Cleaning build...
🔨 Building C frontend...
✅ C frontend built successfully
📦 Installing Python backend...
✅ Python backend installed

📦 Step 4: Deploy
💾 Backed up existing awesh to /home/user/.local/bin/awesh.bak
✅ Deployed awesh to /home/user/.local/bin/awesh
✅ Binary is executable and ready

🧪 Step 5: Test Deployment
✅ Binary exists and is executable
🧪 Testing backend socket communication...
✅ Socket connection successful
✅ STATUS command works: AI_LOADING
✅ Command execution works
✅ Backend sanity test passed
✅ Deployment test passed

📝 Step 6: Git Commit & Push
📝 Git: Adding changes...
📝 Git: Committing changes...
📝 Git: Pushing to remote...
✅ Changes committed and pushed successfully

🎉 Deployment pipeline completed successfully!
```

### Development Workflow

For awesh development, use the Deployment MCP to ensure consistent builds and deployments:

```bash
# During development - quick test
python3 deployment_mcp.py build && python3 deployment_mcp.py deploy

# Before committing - full validation  
python3 deployment_mcp.py full_deploy

# Debugging backend issues
python3 deployment_mcp.py kill_force && python3 deployment_mcp.py test
```

The Deployment MCP ensures reliable, repeatable deployments and catches issues early in the development cycle.

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
