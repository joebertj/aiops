# awesh Installation Guide

**awesh** is an AI-aware interactive shell that combines the speed of native C with the intelligence of Python AI libraries.

## Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/joebertj/aiops/main/install.sh | bash
```

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

2. **Run the installer:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Restart your terminal** or run:
   ```bash
   source ~/.bashrc
   ```

## Configuration

### OpenAI API Key (Required)

Add your OpenAI API key to `~/.aweshrc`:

```bash
echo 'OPENAI_API_KEY=your_api_key_here' >> ~/.aweshrc
```

### Optional Settings

```bash
# ~/.aweshrc
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4                    # Default model
SHOW_AI_STATUS=true                   # Show AI status in prompt
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
- Check if Python dependencies are installed: `pip3 list | grep awesh`
- Verify OpenAI API key in `~/.aweshrc`

### Compilation errors
- Install readline headers: `sudo apt install libreadline-dev`
- Install build tools: `sudo apt install build-essential`

## Uninstall

```bash
rm ~/.local/bin/awesh
pip3 uninstall awesh-backend
rm ~/.aweshrc ~/.awesh.sock
```

## Support

- **Documentation**: [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/joebertj/aiops/issues)
- **Discussions**: [GitHub Discussions](https://github.com/joebertj/aiops/discussions)
