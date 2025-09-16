# awesh Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                awesh System Architecture                        │
│                          "AI by default, Bash when I mean Bash"                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │    │  C Frontend     │    │ Python Backend  │    │ Security Agent  │
│                 │    │   (awesh.c)     │    │ (awesh_backend) │    │ (awesh_sec)     │
│ • Natural Lang  │───▶│                 │───▶│                 │───▶│                 │
│ • Shell Commands│    │ • Readline UI   │    │ • AI Processing │    │ • Process Scan  │
│ • Mixed Input   │    │ • Command Route │    │ • MCP Tools     │    │ • Threat Detect │
└─────────────────┘    │ • Socket Client │    │ • File Agent    │    │ • Shared Memory │
                       └─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │                        │
                                │                        │                        │
                                ▼                        ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                       │  Unix Sockets   │    │   AI Provider   │    │  Shared Memory  │
                       │                 │    │                 │    │                 │
                       │ • ~/.awesh.sock │    │ • OpenAI API    │    │ • Status Updates│
                       │ • Status Sync   │    │ • OpenRouter    │    │ • Threat Alerts │
                       │ • Command Flow  │    │ • GPT-4/5       │    │ • Process Data  │
                       └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Details

### 1. C Frontend (awesh.c)
```
┌─────────────────────────────────────────────────────────────────┐
│                        C Frontend (awesh.c)                    │
├─────────────────────────────────────────────────────────────────┤
│ • Interactive Shell with Readline Support                      │
│ • Smart Command Routing (AI vs Bash Detection)                 │
│ • Built-in Commands: cd, pwd, exit                             │
│ • Socket Communication with Backend                            │
│ • Security Agent Integration                                   │
│ • Dynamic Prompt Generation                                    │
│ • Process Health Monitoring                                    │
└─────────────────────────────────────────────────────────────────┘

Key Functions:
├── Command Routing Logic
│   ├── is_awesh_command() - Control commands (aweh, awes, awev, awea)
│   ├── is_builtin() - Built-in shell commands
│   ├── is_interactive_bash_command() - Interactive commands
│   └── parse_ai_mode() - AI mode detection
│
├── Communication
│   ├── send_to_backend() - Socket communication
│   ├── check_ai_status() - AI readiness check
│   └── handle_ai_mode_detection() - AI processing
│
└── Security Integration
    ├── get_security_agent_status() - Threat status
    ├── get_health_status_emojis() - Process health
    └── Shared memory access for security data
```

### 2. Python Backend (awesh_backend)
```
┌─────────────────────────────────────────────────────────────────┐
│                    Python Backend (awesh_backend)              │
├─────────────────────────────────────────────────────────────────┤
│ • Socket Server (Unix Domain Sockets)                          │
│ • AI Client Integration (OpenAI/OpenRouter)                    │
│ • MCP (Model Context Protocol) Tool Execution                  │
│ • File Agent for File Operations                               │
│ • RAG (Retrieval Augmented Generation) System                  │
│ • Security Integration                                         │
└─────────────────────────────────────────────────────────────────┘

Components:
├── AweshSocketBackend (server.py)
│   ├── Socket Server (~/.awesh.sock)
│   ├── Command Processing
│   ├── AI Client Management
│   └── File Agent Integration
│
├── AweshAIClient (ai_client.py)
│   ├── OpenAI/OpenRouter Integration
│   ├── Streaming Responses
│   ├── System Prompt Management
│   └── Tool Function Calling
│
└── FileAgent (file_agent.py)
    ├── File Reading Operations
    ├── Content Filtering
    └── AI-Enhanced File Analysis
```

### 3. Security Agent (awesh_sec)
```
┌─────────────────────────────────────────────────────────────────┐
│                    Security Agent (awesh_sec)                  │
├─────────────────────────────────────────────────────────────────┤
│ • Process Monitoring (Every 5 seconds)                         │
│ • AI-Powered Threat Detection (Every 5 minutes)                │
│ • Pattern-Based Security Filtering                             │
│ • Shared Memory Status Communication                            │
│ • RAG Data Collection                                          │
└─────────────────────────────────────────────────────────────────┘

Security Features:
├── Process Scanning
│   ├── ps -eo pid,ppid,user,comm,args
│   ├── RAG Data Collection (Every 5s)
│   └── AI Analysis (Every 5min)
│
├── Pattern Detection
│   ├── Dangerous Commands (rm -rf /, dd, mkfs, etc.)
│   ├── Sensitive Data (passwords, keys, tokens)
│   └── Regex-based Filtering
│
└── Communication
    ├── Backend Socket Connection
    ├── Shared Memory Status Updates
    └── Threat Alert Propagation
```

## Data Flow

### 1. Command Processing Flow
```
User Input → C Frontend → Command Routing Decision
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            Built-in Commands   Bash Commands   AI Processing
                    │               │               │
                    │               │               ▼
                    │               │        Security Check
                    │               │               │
                    │               │               ▼
                    │               │        Python Backend
                    │               │               │
                    │               │               ▼
                    │               │        AI Provider
                    │               │               │
                    │               │               ▼
                    │               │        MCP Tools
                    │               │               │
                    │               │               ▼
                    │               │        Response
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                                    ▼
                            User Output
```

### 2. Security Monitoring Flow
```
Security Agent → Process Scanning (5s) → RAG Data Collection
                                        │
                                        ▼
                               Backend RAG Storage
                                        │
                                        ▼
                               AI Analysis (5min) → Threat Detection
                                        │
                                        ▼
                               Shared Memory Update
                                        │
                                        ▼
                               Frontend Status Display
```

## Communication Protocols

### 1. Frontend ↔ Backend (Unix Sockets)
```
Protocol: ~/.awesh.sock (Unix Domain Socket)

Commands:
├── STATUS - AI readiness check
├── CWD:<path> - Working directory sync
├── QUERY:<prompt> - AI query
├── BASH_FAILED:<code>:<cmd>:<file> - Bash failure context
├── VERBOSE:<level> - Verbose level update
└── AI_PROVIDER:<provider> - Provider switch

Responses:
├── AI_READY / AI_LOADING - Status response
├── OK - Acknowledgment
└── <AI Response> - Streaming AI output
```

### 2. Backend ↔ Security Agent
```
Protocol: ~/.awesh.sock (Same socket, different messages)

Security Messages:
├── SECURITY_CHECK:<prompt> - Security validation
├── RAG_ADD_PROCESS:<data> - Process data for RAG
├── PROCESS_ANALYSIS:ANALYZE_RAG_5MIN - AI analysis request
└── THREAT_DETECTED:<info> - Threat detection result

Responses:
├── SECURITY_OK:<filtered_prompt> - Safe prompt
├── SECURITY_BLOCKED:<reason> - Blocked prompt
└── <AI Analysis Result> - Threat analysis
```

### 3. Security Agent ↔ Frontend
```
Protocol: Shared Memory (awesh_security_status_<user>)

Status Updates:
├── ✅ No threats detected
├── 🔴 HIGH: <threat_info>
├── 🟡 MEDIUM: <threat_info>
└── 🟢 LOW: <threat_info>
```

## Configuration

### 1. Frontend Configuration (~/.aweshrc)
```
VERBOSE=0                    # 0=silent, 1=info, 2=debug
AI_PROVIDER=openai          # openai or openrouter
MODEL=gpt-5                 # AI model to use
OPENAI_API_KEY=sk-...       # API key
OPENROUTER_API_KEY=sk-...   # OpenRouter key
```

### 2. System Prompts
```
~/.awesh_system.txt         # Custom AI behavior
Default: Operations-focused prompt for infrastructure management
```

## Key Features

### 1. Smart Command Routing
- **Bash Triggers**: Known commands, shell syntax, pipes, redirects
- **AI Triggers**: Natural language, questions, analysis requests
- **Built-in Commands**: cd, pwd, exit (handled by frontend)

### 2. Security Integration
- **Real-time Monitoring**: Process scanning every 5 seconds
- **AI Threat Detection**: Analysis every 5 minutes
- **Pattern Filtering**: Dangerous commands and sensitive data
- **Visual Indicators**: Emoji-based status in prompt

### 3. Performance Optimizations
- **Caching**: Prompt data cached for 5 seconds
- **Non-blocking**: Backend starts in background
- **Streaming**: Real-time AI responses
- **Health Monitoring**: Automatic process restart

### 4. MCP Integration
- **Tool Execution**: Secure tool calling through MCP
- **File Operations**: FileAgent for file reading/analysis
- **Safety**: No direct shell execution from AI
- **Audit**: Configurable logging and monitoring

## Installation & Usage

### Quick Start
```bash
cd awesh/
./install.sh
export OPENAI_API_KEY=your_key
awesh
```

### Example Session
```bash
awesh> ls -la                              # → Bash execution
awesh> what files are here?                # → AI analysis
awesh> find . -name "*.py"                 # → Bash execution  
awesh> explain this error                  # → AI interpretation
awesh> cat file.txt | grep error           # → Bash (pipe detected)
awesh> summarize this directory structure  # → AI analysis
```

This architecture provides a robust, secure, and intelligent shell environment that seamlessly blends traditional command-line operations with AI assistance while maintaining the performance and security requirements of operations professionals.
