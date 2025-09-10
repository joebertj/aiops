# awesh Installation Guide

**awesh** is an AI-aware interactive shell that combines the speed of native C with the intelligence of Python AI libraries.

## Quick Install

```bash
cd aiops/deployment/
python3 deployment_mcp.py clean_install
```

**🐍 Virtual Environment:** The installation automatically creates and uses a Python virtual environment, ensuring clean dependency isolation and reproducible deployments.

## Manual Installation

### Prerequisites

- **Linux** (Ubuntu, Debian, CentOS, RHEL, etc.)
- **gcc** compiler
- **python3** (3.8+)
- **pip3**
- **readline development headers**

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install build-essential python3 python3-pip libreadline-dev
```

#### CentOS/RHEL/Fedora
```bash
sudo yum groupinstall 'Development Tools'
sudo yum install python3 python3-pip readline-devel
```

### Build and Install

1. **Clone the repository:**
   ```bash
   git clone https://github.com/joebertj/aiops.git
   cd aiops
   ```

2. **Run the deployment MCP (with virtual environment):**
   ```bash
   cd deployment/
   python3 deployment_mcp.py clean_install
   ```
   
   This automatically:
   - Creates a Python virtual environment
   - Installs all dependencies in isolation
   - Builds and deploys awesh using venv Python

3. **Restart your terminal** or run:
   ```bash
   source ~/.bashrc
   ```

## Configuration

### OpenAI API Key (Required)

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY=your_api_key_here
# Add to ~/.bashrc or ~/.profile to persist across sessions
echo 'export OPENAI_API_KEY=your_api_key_here' >> ~/.bashrc
```

### Optional Settings

Set additional environment variables as needed:

```bash
export OPENAI_MODEL=gpt-4                    # Default model
export VERBOSE=1                             # 0=silent, 1=show AI status+debug, 2+=more verbose
```

## Usage

Start awesh:
```bash
awesh
```

You'll see:
```
awesh v0.1.0 - Awe-Inspired Workspace Environment Shell
Model: gpt-4

AI loading: awesh> 
```

Once AI loads:
```
AI ready: awesh> ls
```

### Features

- **Instant startup** - C frontend starts immediately
- **AI intelligence** - Failed commands get AI suggestions
- **Traditional shell** - Works like bash for successful commands
- **Interactive programs** - vi, nano, htop work perfectly
- **Smart routing** - Bash first, AI for complex cases

### Examples

```bash
# Regular commands work normally
AI ready: awesh> ls -la
total 48
drwxr-xr-x  8 user user 4096 Jan 15 10:30 .
...

# Failed commands get AI help
AI ready: awesh> list files
🤖 I see you want to list files. Try: `ls`
Would you like me to run this? (y/n)

# Natural language queries
AI ready: awesh> how do I find large files?
🤖 To find large files, you can use:
`find . -type f -size +100M -ls`
```

## Troubleshooting

### Command not found: awesh
- Make sure `~/.local/bin` is in your PATH
- Restart your terminal or run `source ~/.bashrc`

### Backend connection failed
- Check if Python dependencies are installed: `./venv/bin/pip list | grep awesh`
- Verify OpenAI API key in `~/.aweshrc`
- Ensure virtual environment is being used: `ps aux | grep awesh` should show `venv/bin/python3`

### Compilation errors
- Install readline headers: `sudo apt install libreadline-dev`
- Install build tools: `sudo apt install build-essential`

### Virtual environment issues
- **Virtual environment not found**: Run `python3 deployment/deployment_mcp.py setup_venv`
- **Dependencies missing**: Run `python3 deployment/deployment_mcp.py install_deps`
- **Wrong Python executable**: Check `ps aux | grep awesh` shows `venv/bin/python3`
- **Permission errors**: Ensure `venv/` directory is owned by your user

## Uninstall

```bash
cd deployment/
python3 deployment_mcp.py kill_force
rm ~/.local/bin/awesh
./venv/bin/pip uninstall awesh-backend  # Use venv pip
rm ~/.aweshrc ~/.awesh.sock
rm -rf venv/  # Remove virtual environment
```

## Support

- **Documentation**: [README.md](README.md)
- **Virtual Environment**: [VENV_SETUP.md](VENV_SETUP.md) - Detailed venv setup and troubleshooting
- **Issues**: [GitHub Issues](https://github.com/joebertj/aiops/issues)
- **Discussions**: [GitHub Discussions](https://github.com/joebertj/aiops/discussions)
