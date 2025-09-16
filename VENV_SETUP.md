# Virtual Environment Setup and Enforcement

This document describes how AIOps enforces the use of a Python virtual environment for all Python operations, ensuring consistent dependency management and isolation.

## Overview

AIOps uses a Python virtual environment (`venv`) to:
- **Isolate dependencies** from system Python packages
- **Ensure consistent versions** across different environments
- **Prevent conflicts** with system-installed packages
- **Enable clean deployments** with reproducible environments

## Virtual Environment Structure

```
aiops/
├── venv/                    # Virtual environment directory
│   ├── bin/                 # Unix/Linux executables
│   │   ├── python3         # Virtual environment Python
│   │   ├── pip             # Virtual environment pip
│   │   └── activate        # Activation script
│   └── lib/                 # Python packages
└── awesh/                   # Main application
    └── requirements.txt     # Python dependencies
```

## Automatic Virtual Environment Management

### Deployment Script Enforcement

The `deployment/deployment_mcp.py` script automatically:

1. **Creates virtual environment** if it doesn't exist
2. **Upgrades pip** in the virtual environment
3. **Installs dependencies** from `requirements.txt`
4. **Uses venv Python** for all Python operations
5. **Enforces venv usage** throughout the deployment process

### Key Functions

#### `setup_venv()`
- Creates virtual environment if missing
- Upgrades pip to latest version
- Ensures proper permissions and structure

#### `get_venv_python()`
- Returns path to virtual environment Python executable
- Cross-platform support (Windows/Unix)
- Fallback to system Python if venv unavailable

#### `get_venv_pip()`
- Returns path to virtual environment pip executable
- Used for all package installations
- Ensures dependencies are installed in isolation

## Virtual Environment Usage in awesh

### Backend Process

The awesh shell automatically uses the virtual environment Python for its backend process:

```python
# In awesh/shell.py
venv_python = Path(__file__).parent.parent / "venv" / "bin" / "python3"
python_executable = str(venv_python) if venv_python.exists() else sys.executable

self.backend_process = subprocess.Popen([
    python_executable, str(backend_script)
], ...)
```

### Dependency Management

All Python dependencies are managed through the virtual environment:

```bash
# Dependencies are installed in venv, not system Python
./venv/bin/pip install -r awesh/requirements.txt
./venv/bin/pip install -e .
```

## Requirements and Dependencies

### Core Dependencies (`awesh/requirements.txt`)

```txt
# Core dependencies for awesh
asyncio-mqtt>=0.16.0
aiofiles>=23.0.0
openai>=1.0.0
anthropic>=0.7.0
pydantic>=2.0.0
pyyaml>=6.0.0
rich>=13.0.0
prompt-toolkit>=3.0.0
psutil>=5.9.0

# Optional dependencies for enhanced functionality
httpx>=0.24.0
websockets>=11.0.0
jsonschema>=4.17.0

# Vector database and RAG system dependencies
sentence-transformers>=2.2.0
chromadb>=0.4.0
numpy>=1.24.0
```

### Virtual Environment Benefits

1. **Isolation**: Dependencies don't conflict with system packages
2. **Reproducibility**: Same environment across different systems
3. **Clean Uninstall**: Remove entire `venv/` directory to clean up
4. **Version Control**: `requirements.txt` tracks exact versions
5. **Development Safety**: No risk of breaking system Python

## Deployment Commands

### Clean Install (Recommended)
```bash
cd deployment/
python3 deployment_mcp.py clean_install
```

This command:
1. Sets up virtual environment
2. Installs all dependencies
3. Builds and deploys awesh
4. Uses venv Python for backend

### Install Dependencies Only
```bash
cd deployment/
python3 deployment_mcp.py install_deps
```

### Setup Virtual Environment Only
```bash
cd deployment/
python3 deployment_mcp.py setup_venv
```

## Manual Virtual Environment Operations

### Activate Virtual Environment
```bash
cd aiops/
source venv/bin/activate
```

### Install Dependencies Manually
```bash
# Using venv pip
./venv/bin/pip install -r awesh/requirements.txt
./venv/bin/pip install -e .
```

### Run Python Scripts with venv
```bash
# Use venv Python explicitly
./venv/bin/python3 awesh/backend.py
./venv/bin/python3 deployment/deployment_mcp.py clean_install
```

### Check Virtual Environment Status
```bash
# Verify venv Python is being used
which python3                    # Should show system Python
./venv/bin/python3 --version     # Should show venv Python version

# Check installed packages
./venv/bin/pip list
```

## Troubleshooting

### Virtual Environment Not Found
```bash
# Error: Virtual environment Python not found
# Solution: Run setup_venv
cd deployment/
python3 deployment_mcp.py setup_venv
```

### Dependencies Not Available
```bash
# Error: ModuleNotFoundError
# Solution: Install dependencies in venv
cd deployment/
python3 deployment_mcp.py install_deps
```

### Wrong Python Executable
```bash
# Check which Python awesh is using
ps aux | grep awesh
# Should show venv/bin/python3, not /usr/bin/python3
```

### Virtual Environment Corruption
```bash
# Remove and recreate venv
rm -rf venv/
cd deployment/
python3 deployment_mcp.py setup_venv
python3 deployment_mcp.py install_deps
```

## Best Practices

### Development Workflow
1. **Always use deployment script** for installations
2. **Don't install packages globally** - use venv
3. **Update requirements.txt** when adding dependencies
4. **Test with clean install** before committing changes

### Production Deployment
1. **Use clean_install** for production deployments
2. **Verify venv usage** in production environment
3. **Monitor dependency versions** for security updates
4. **Keep requirements.txt updated** with exact versions

### Version Control
- **Include `venv/` in `.gitignore`** (already configured)
- **Commit `requirements.txt`** with exact versions
- **Document dependency changes** in commit messages
- **Test on clean systems** before releasing

## Integration with CI/CD

The virtual environment enforcement works seamlessly with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Setup Virtual Environment
  run: |
    cd deployment/
    python3 deployment_mcp.py setup_venv
    python3 deployment_mcp.py install_deps

- name: Build and Test
  run: |
    cd deployment/
    python3 deployment_mcp.py clean_install
    python3 deployment_mcp.py test
```

## Security Considerations

### Dependency Isolation
- Virtual environment prevents dependency conflicts
- Isolated from system Python packages
- No risk of breaking system tools

### Package Verification
- All packages installed from PyPI
- Version pinning in requirements.txt
- No custom package sources

### Access Control
- Virtual environment owned by user
- No root privileges required
- Clean uninstall by removing venv directory

## Monitoring and Maintenance

### Regular Maintenance
```bash
# Update pip in venv
./venv/bin/pip install --upgrade pip

# Check for outdated packages
./venv/bin/pip list --outdated

# Update specific packages
./venv/bin/pip install --upgrade package_name
```

### Health Checks
```bash
# Verify venv integrity
./venv/bin/python3 -c "import sys; print(sys.executable)"
# Should show path to venv/bin/python3

# Test critical imports
./venv/bin/python3 -c "import openai, anthropic, psutil; print('All imports successful')"
```

This virtual environment enforcement ensures that AIOps runs in a clean, isolated, and reproducible environment across all deployment scenarios.









