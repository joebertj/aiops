# awesh Architecture Contract

## 🏗️ **CORE ARCHITECTURAL PRINCIPLES**

### 1. **Bash-First, AI-Enhanced**
- **awesh is a bash wrapper, NOT a bash replacement**
- All bash functionality must be preserved: tab completion, history, line editing, pipes, redirection
- AI and agents enhance bash capabilities, they do not replace them
- Users keep their bash muscle memory and existing workflows

### 2. **C Frontend / Python Backend Separation**
- **C Frontend**: Fast, offline operations (prompt generation, basic parsing, file ops)
- **Python Backend**: Heavy operations (AI calls, agent processing, API operations)
- Frontend handles instant responsiveness, backend handles intelligence
- No AI processing in C frontend - all AI operations delegated to Python

### 3. **Agent System Architecture**
- **Processing Order**: Security Agent → Kubernetes Agent → Container Agent → Command Router Agent
- **Fail-Fast Behavior**: If any agent fails, processing stops immediately
- **Command Routing**: Direct commands go to bash, natural language goes to agents
- **Agent Priority**: Security Agent (10) → Kubernetes Agent (20) → Container Agent (30) → Command Router (100)

## 🔄 **COMMAND PROCESSING FLOW**

```
User Input → bash (tab completion, history, editing) → awesh C frontend → Python backend → Agent System → AI/Bash
```

### Detailed Flow:
1. **User types command** with full bash support (tab completion, history, line editing)
2. **C frontend** generates emoji-enhanced prompt and captures input
3. **Python backend** processes through agent system
4. **Agent System** determines routing:
   - **Direct commands** → Bash Executor (preserves existing functionality)
   - **Natural language** → Specialized agents (Container, Kubernetes, etc.)
   - **Unhandled** → AI processing
5. **Result displayed** back to user

## 🎯 **COMMAND ROUTING RULES**

### Direct Commands (Bash Executor)
```bash
docker ps                    # → Bash Executor → Actual Docker
docker run ubuntu            # → Bash Executor → Actual Docker  
docker build .               # → Bash Executor → Actual Docker
kubectl get pods             # → Bash Executor → Actual kubectl
ls -la | grep docker         # → Bash Executor → Bash pipes work
```

### Natural Language (Agent System)
```bash
"show my docker containers"  # → Container Agent → runc implementation
"run a new ubuntu container" # → Container Agent → runc implementation
"list all my containers"     # → Container Agent → runc implementation
"show me kubernetes pods"    # → Kubernetes Agent → Direct API calls
"deploy my app"              # → Appropriate agent based on context
```

### AI Processing (Fallback)
```bash
"explain what this does"     # → AI processing
"help me debug this issue"   # → AI processing
```

## 🚀 **PERFORMANCE REQUIREMENTS**

### Frontend (C) - Must be Instant
- **Prompt generation**: <50ms (with caching)
- **Input capture**: <10ms
- **Basic parsing**: <5ms
- **File operations**: <100ms

### Backend (Python) - Can be Slower
- **Agent processing**: <500ms
- **AI calls**: <5 seconds
- **API operations**: <10 seconds
- **Complex analysis**: <30 seconds

### Caching Strategy
- **Prompt data**: 5-second TTL (git branch, k8s context)
- **Agent results**: Context-dependent TTL
- **AI responses**: No caching (always fresh)

## 🎨 **PROMPT DESIGN CONTRACT**

### Format
```
<AI_STATUS>:<USER>@<HOST>:<CWD>:<CONTEXT>
> 
```

### AI Status Emojis
- **🤖**: AI Loading (offline, initializing)
- **🧠**: AI Ready (online, fully functional)
- **💀**: AI Failed (error state)

### Context Emojis
- **☸️**: Kubernetes context/namespace
- **🌿**: Git branch
- **🔧**: System/configuration context
- **📊**: Monitoring/metrics context

### Example
```
🧠:joebert@maximaal:~/AI/aiops:☸️<rancher-desktop>:🌿<main>
> 
```

## 🔒 **SECURITY ARCHITECTURE**

### Security Agent (Priority 10)
- **Guardrail Function**: Prevents dangerous commands using existing awesh security modules
- **Sensitive Info Gatekeeper**: Filters sensitive data using existing awesh filters
- **Prompt Integrity**: Detects tampering with hardcoded prompts
- **Fail-Fast**: Stops processing immediately on security violations

### Security Modules Used
- `CommandSafetyFilter`: Command validation
- `SensitiveDataFilter`: Data protection
- `AweshPolicyEngine`: Policy enforcement

## 🐳 **CONTAINER AGENT ARCHITECTURE**

### Docker Compatibility
- **Direct commands**: Use actual Docker (preserve existing workflows)
- **Natural language**: Use runc implementation (AI-enhanced)
- **No Docker daemon dependency**: runc works without Docker

### Implementation
- **Runtime**: runc (Open Container Initiative)
- **Storage**: Local filesystem-based
- **Interface**: Docker-compatible command syntax
- **Dependencies**: Only runc, bash, Python standard library

## ☸️ **KUBERNETES AGENT ARCHITECTURE**

### Direct API Approach
- **No kubectl dependency**: Direct Kubernetes API calls
- **AI-powered**: Natural language to API call translation
- **Performance**: 5-20x faster than kubectl chaining
- **Intelligence**: Context-aware responses

### Implementation
- **API Client**: Kubernetes Python client
- **MCP Integration**: Uses existing Kubernetes MCP
- **Context Awareness**: Understands cluster state
- **Natural Language**: Translates intent to API calls

## 🐛 **DEBUG-DRIVEN DEVELOPMENT (D³)**

### Performance Monitoring
- **VERBOSE=0**: Silent (production)
- **VERBOSE=1**: Info level (default)
- **VERBOSE=2**: Debug level with emoji output

### Debug Output Format
```
🐛 DEBUG: <operation> took <time>ms
```

### D³ Workflow
1. **Identify Problem**: Use performance monitoring
2. **Analyze Context**: Measure each operation
3. **Design Solution**: Optimize bottlenecks
4. **Implement Fix**: Apply optimizations
5. **Verify Solution**: Measure improvements

## 🚫 **ARCHITECTURAL VIOLATIONS**

### ❌ **NEVER DO THESE**
- Replace bash functionality with custom implementations
- Put AI processing in C frontend
- Remove tab completion or command history
- Break existing bash workflows
- Make direct commands slower than bash
- Remove agent fail-fast behavior
- Cache AI responses (always fresh)
- Use Docker daemon in Container Agent implementation

### ✅ **ALWAYS DO THESE**
- Preserve all bash functionality
- Use C for fast operations, Python for heavy operations
- Process agents in priority order with fail-fast
- Route direct commands to bash, natural language to agents
- Use emojis for visual context in prompts
- Monitor performance with D³ methodology
- Cache prompt data for performance
- Use existing awesh security modules

## 📋 **ARCHITECTURAL DECISIONS**

### Why Bash-First?
- **User Experience**: No learning curve, preserves muscle memory
- **Compatibility**: All existing scripts and workflows work
- **Performance**: Bash is fast for direct operations
- **Ecosystem**: Leverages 40+ years of shell tooling

### Why C Frontend / Python Backend?
- **Performance**: C handles instant operations, Python handles intelligence
- **Separation of Concerns**: Fast vs smart operations
- **Maintainability**: Clear boundaries between components
- **Scalability**: Each component can be optimized independently

### Why Agent System?
- **Specialization**: Each agent handles specific domains
- **Performance**: Direct API calls vs CLI chaining
- **Intelligence**: AI-powered natural language processing
- **Extensibility**: Easy to add new agents

### Why Emoji Prompts?
- **Visual Context**: Instant understanding of system state
- **Space Efficient**: More information in less space
- **User Friendly**: Intuitive visual indicators
- **Professional**: Clean, modern interface

## 🔄 **EVOLUTION PATH**

### Phase 1: Foundation (Current)
- ✅ Bash wrapper with AI enhancement
- ✅ C frontend / Python backend separation
- ✅ Basic agent system
- ✅ Emoji-enhanced prompts
- ✅ Performance monitoring

### Phase 2: Agent Expansion
- 🔄 Container Agent with runc
- 🔄 Kubernetes Agent with direct API
- 🔄 AWS Agent with direct API
- 🔄 Terraform Agent with direct API

### Phase 3: Intelligence
- 🔄 Advanced AI integration
- 🔄 Predictive operations
- 🔄 Autonomous problem solving
- 🔄 Context-aware assistance

## 📝 **ARCHITECTURAL COMPLIANCE**

This document serves as the **architectural contract** for awesh. Any changes that violate these principles must be flagged and discussed before implementation.

**Last Updated**: September 10, 2024
**Version**: 1.0
**Status**: Active Contract
