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
└─────────────────┘    │ • Socket Client │    │ • File Agent    │    │ • Config File   │
                       │ • PTY Support   │    │ • Socket Server │    │ • RAG Analysis  │
                       └─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │                        │
                                │                        │                        │
                                ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Bash Sandbox    │    │  Unix Sockets   │    │   AI Provider   │    │  Config Files   │
│ (awesh_sandbox) │    │                 │    │                 │    │                 │
│                 │    │ • ~/.awesh.sock │    │ • OpenAI API    │    │ • ~/.aweshrc    │
│ • PTY Support   │    │ • ~/.awesh_sandbox.sock│ • OpenRouter    │    │ • ~/.awesh_config.ini│
│ • Command Test  │    │ • Status Sync   │    │ • GPT-4/5       │    │ • Verbose Control│
│ • Interactive   │    │ • Command Flow  │    │ • Streaming     │    │ • AI Settings   │
│   Detection     │    │ • Frontend Socket│   │ • Tool Calling  │    │ • Security Rules│
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Details

### 1. C Frontend (awesh.c)
```
┌─────────────────────────────────────────────────────────────────┐
│                        C Frontend (awesh.c)                    │
├─────────────────────────────────────────────────────────────────┤
│ • Interactive Shell with Readline Support                      │
│ • Smart Command Routing (Sandbox → AI → Direct)                │
│ • Built-in Commands: cd, pwd, exit, quit                       │
│ • Socket Communication with Backend & Sandbox                  │
│ • Security Agent Integration                                   │
│ • Dynamic Prompt Generation (0ms)                              │
│ • Process Health Monitoring & Auto-restart                     │
│ • PTY Support for Interactive Commands                         │
│ • Independent Operation (works as regular bash)                │
└─────────────────────────────────────────────────────────────────┘

Key Functions:
├── Command Routing Logic
│   ├── is_awesh_command() - Control commands (aweh, awes, awev, awea)
│   ├── is_builtin() - Built-in shell commands
│   ├── test_command_in_sandbox() - Sandbox command testing
│   ├── is_interactive_command() - Interactive command detection
│   └── execute_command_securely() - Main command execution
│
├── Communication
│   ├── send_to_backend() - Backend socket communication
│   ├── send_to_sandbox() - Sandbox socket communication
│   ├── send_to_security_agent() - Security agent communication
│   └── init_frontend_socket() - Frontend socket server
│
├── Process Management
│   ├── restart_backend() - Backend process restart
│   ├── restart_security_agent() - Security agent restart
│   ├── restart_sandbox() - Sandbox process restart
│   └── attempt_child_restart() - Auto-restart failed processes
│
└── Security Integration
    ├── get_security_agent_status() - Threat status
    ├── get_health_status_emojis() - Process health (🧠:🔒:🏖️)
    └── Config file reading (~/.aweshrc)
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
│ • Config File Reading (~/.aweshrc)                             │
│ • RAG Data Collection & Analysis                               │
│ • Isolated Operation (no socket server)                        │
└─────────────────────────────────────────────────────────────────┘

Security Features:
├── Process Scanning
│   ├── Backend API calls for process data
│   ├── RAG Data Collection (Every 5s)
│   └── AI Analysis (Every 5min)
│
├── Pattern Detection
│   ├── Dangerous Commands (rm -rf /, dd, mkfs, etc.)
│   ├── Sensitive Data (passwords, keys, tokens)
│   └── Regex-based Filtering
│
└── Communication
    ├── Backend Socket Connection (security analysis only)
    ├── Config File Reading (verbose control)
    └── Threat Alert Propagation
```

### 4. Bash Sandbox (awesh_sandbox)
```
┌─────────────────────────────────────────────────────────────────┐
│                    Bash Sandbox (awesh_sandbox)                │
├─────────────────────────────────────────────────────────────────┤
│ • PTY-based Bash Environment                                   │
│ • Command Testing & Execution                                  │
│ • Interactive Command Detection                                │
│ • Socket Communication with Frontend                           │
│ • Automatic Cleanup on Interactive Commands                    │
└─────────────────────────────────────────────────────────────────┘

Sandbox Features:
├── Command Execution
│   ├── PTY Support for proper TTY
│   ├── 2-second timeout for command testing
│   ├── Bash prompt detection
│   └── Interactive command cleanup (Ctrl+C)
│
├── Communication
│   ├── Unix Domain Socket (~/.awesh_sandbox.sock)
│   ├── Command/Response Protocol
│   └── INTERACTIVE_COMMAND detection
│
└── Process Management
    ├── Persistent bash process
    ├── Automatic cleanup on exit
    └── Error handling and recovery
```

## Data Flow

### 1. Command Processing Flow (4-Component Architecture)
```
User Input → C Frontend → Command Routing Decision
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            Built-in Commands   Sandbox Test    AI Processing
                    │               │               │
                    │               ▼               │
                    │        Interactive?           │
                    │               │               │
                    │        ┌──────┼──────┐       │
                    │        │      │      │       │
                    │        ▼      ▼      ▼       │
                    │   Direct PTY  AI    Backend  │
                    │   Execution   Route  Route   │
                    │        │      │      │       │
                    │        │      │      ▼       │
                    │        │      │   Security   │
                    │        │      │  Middleware  │
                    │        │      │      │       │
                    │        │      │      ▼       │
                    │        │      │  Command     │
                    │        │      │ Execution    │
                    │        │      │      │       │
                    │        │      │      ▼       │
                    │        │      │  Results     │
                    │        │      │ Display      │
                    │        │      │      │       │
                    └────────┼──────┼──────┼───────┘
                             │      │      │
                             ▼      ▼      ▼
                        User Output
```

### 2. AI Response Modes (vi-inspired)
```
AI Response → Mode Detection
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
  Normal Mode   Command Mode   Display Mode
  (default)     awesh: cmd    (text only)
        │           │           │
        │           ▼           │
        │    Security Check     │
        │           │           │
        │           ▼           │
        │    Command Execute    │
        │           │           │
        └───────────┼───────────┘
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
├── AI_PROVIDER:<provider> - Provider switch
└── GET_PROCESS_DATA - Process data for security agent

Responses:
├── AI_READY / AI_LOADING - Status response
├── OK - Acknowledgment
└── <AI Response> - Streaming AI output
```

### 2. Frontend ↔ Sandbox (Unix Sockets)
```
Protocol: ~/.awesh_sandbox.sock (Unix Domain Socket)

Commands:
├── <command> - Any shell command to test/execute

Responses:
├── EXIT_CODE:<code>\nSTDOUT:<output>\nSTDERR:<error> - Normal command
└── EXIT_CODE:-2\nSTDOUT:INTERACTIVE_COMMAND\nSTDERR:\n - Interactive command
```

### 3. Backend ↔ Security Agent
```
Protocol: ~/.awesh.sock (Same socket, different messages)

Security Messages:
├── GET_PROCESS_DATA - Request process data from backend
├── RAG_ADD_PROCESS:<data> - Process data for RAG
├── PROCESS_ANALYSIS:ANALYZE_RAG_5MIN - AI analysis request
└── RAG_CLEAR_PROCESS_DATA - Clear RAG data after analysis

Responses:
├── <process_data> - Process information from ps command
├── <AI Analysis Result> - Threat analysis
└── OK - Acknowledgment
```

### 4. Security Agent ↔ Frontend
```
Protocol: Config File (~/.aweshrc)

Status Updates:
├── VERBOSE=<level> - Verbose level control
├── AI_PROVIDER=<provider> - AI provider setting
└── Other configuration settings

Note: Security agent reads config file directly, no socket communication
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
- **Sandbox Testing**: All commands tested in sandbox first
- **Interactive Detection**: Commands that don't return prompt → PTY execution
- **AI Triggers**: Natural language, questions, analysis requests
- **Built-in Commands**: cd, pwd, exit, quit (handled by frontend)
- **Fallback**: Direct bash execution when no children ready

### 2. Security Integration
- **Real-time Monitoring**: Process scanning every 5 seconds
- **AI Threat Detection**: Analysis every 5 minutes
- **Pattern Filtering**: Dangerous commands and sensitive data
- **Visual Indicators**: Emoji-based status in prompt (🧠:🔒:🏖️)
- **Isolated Security**: Security agent reads config, no socket server

### 3. Performance Optimizations
- **Instant Prompt**: 0ms prompt generation (no blocking calls)
- **Non-blocking**: All children start in background
- **Streaming**: Real-time AI responses
- **Health Monitoring**: Automatic process restart
- **Independent Operation**: Works as regular bash when needed

### 4. PTY Support
- **Interactive Commands**: vi, top, ssh, python, etc. work properly
- **TTY Detection**: Sandbox detects interactive commands automatically
- **Clean State**: Sandbox cleaned up after interactive detection
- **Direct Execution**: Interactive commands run in frontend with proper TTY

### 5. MCP Integration
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
🧠:🔒:🏖️:joebert@maximaal:~:☸️default:🌿main
> ls -la                              # → Sandbox → Bash execution
> vi file.txt                         # → Sandbox → Interactive → PTY execution
> what files are here?                # → AI analysis
> find . -name "*.py"                 # → Sandbox → Bash execution  
> top                                 # → Sandbox → Interactive → PTY execution
> explain this error                  # → AI interpretation
> cat file.txt | grep error           # → Sandbox → Bash (pipe detected)
> summarize this directory structure  # → AI analysis
> awev off                            # → Built-in command (verbose off)
> exit                                # → Built-in command (clean exit)
```

### Status Emojis
- **🧠** = Backend ready (AI available)
- **⏳** = Backend loading/not ready
- **💀** = Backend failed
- **🔒** = Security agent ready
- **⏳** = Security agent not ready
- **🏖️** = Sandbox ready
- **⏳** = Sandbox not ready

This architecture provides a robust, secure, and intelligent shell environment that seamlessly blends traditional command-line operations with AI assistance while maintaining the performance and security requirements of operations professionals.
