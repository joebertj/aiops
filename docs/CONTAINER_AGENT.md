# Container Agent Documentation

## Overview

The Container Agent provides Docker-compatible container management using `runc` and minimal dependencies. It handles container-related prompts and executes container operations using only `runc`, `bash`, and Python standard library modules - no Docker daemon required.

## Architecture

### Core Components

- **Runtime**: Uses `runc` (Open Container Initiative runtime)
- **Storage**: Local filesystem-based container and image storage
- **Interface**: Docker-compatible command syntax
- **Dependencies**: Only `runc`, `bash`, and Python standard library

### Storage Structure

```
~/.awesh/
├── containers/          # Container instances
│   └── <container_id>/
│       ├── config.json  # Container configuration
│       ├── logs.txt     # Container logs
│       └── bundle/      # OCI bundle for runc
│           ├── config.json
│           └── rootfs/
└── images/              # Container images
    └── <image_id>/
        ├── manifest.json
        └── layers/
```

## Supported Operations

### Container Management

| Command | Description | Status |
|---------|-------------|--------|
| `docker ps` | List running containers | ✅ Implemented |
| `docker run <image>` | Start new container | ✅ Implemented |
| `docker start <container>` | Start stopped container | ✅ Implemented |
| `docker stop <container>` | Stop running container | ✅ Implemented |
| `docker rm <container>` | Remove container | ✅ Implemented |
| `docker logs <container>` | View container logs | ✅ Implemented |
| `docker inspect <container>` | Inspect container details | ✅ Implemented |
| `docker exec <container> <cmd>` | Execute command in container | 🚧 Planned |

### Image Management

| Command | Description | Status |
|---------|-------------|--------|
| `docker images` | List available images | ✅ Implemented |
| `docker pull <image>` | Download image | 🚧 Planned |
| `docker build .` | Build image from Dockerfile | 🚧 Planned |
| `docker rmi <image>` | Remove image | 🚧 Planned |

## Usage Examples

### Basic Container Operations

```bash
# List containers
docker ps

# Run a new container
docker run ubuntu

# View container logs
docker logs <container_id>

# Stop a container
docker stop <container_id>

# Remove a container
docker rm <container_id>

# Inspect container details
docker inspect <container_id>
```

### Natural Language Queries

The Container Agent also responds to natural language prompts:

```bash
# List all containers
"show me all containers"
"what containers are running?"

# Container management
"start a new ubuntu container"
"stop the container with id abc123"
"show me the logs for container xyz789"

# Image operations
"list all available images"
"pull the latest nginx image"
```

## Agent Integration

### Processing Priority

The Container Agent runs at priority 30 in the agent processing chain:

1. **Security Agent** (priority 10) - Validates safety
2. **Kubernetes Agent** (priority 20) - Handles K8s operations  
3. **Container Agent** (priority 30) - Handles container operations
4. **Command Router Agent** (priority 100) - Routes to Bash/AI

### Prompt Detection

The agent automatically detects container-related prompts using keywords:

- **Container terms**: `container`, `docker`, `runc`, `podman`
- **Operations**: `run`, `start`, `stop`, `build`, `pull`, `push`
- **Management**: `ps`, `logs`, `exec`, `inspect`, `rm`, `rmi`
- **Infrastructure**: `image`, `volume`, `network`, `compose`

## Technical Implementation

### OCI Bundle Creation

The agent creates OCI-compliant bundles for `runc`:

```json
{
  "ociVersion": "1.0.0",
  "process": {
    "terminal": true,
    "user": {"uid": 0, "gid": 0},
    "args": ["/bin/sh"],
    "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
    "cwd": "/"
  },
  "root": {
    "path": "rootfs",
    "readonly": false
  },
  "hostname": "container_<id>",
  "mounts": [
    {
      "destination": "/proc",
      "type": "proc",
      "source": "proc"
    },
    {
      "destination": "/dev",
      "type": "tmpfs",
      "source": "tmpfs",
      "options": ["nosuid", "strictatime", "mode=755", "size=65536k"]
    }
  ],
  "linux": {
    "namespaces": [
      {"type": "pid"},
      {"type": "ipc"},
      {"type": "uts"},
      {"type": "mount"}
    ]
  }
}
```

### Container Lifecycle

1. **Creation**: Parse image name, create container directory
2. **Configuration**: Generate OCI bundle with proper namespaces
3. **Execution**: Use `runc run` to start container
4. **Management**: Track status, collect logs, handle signals
5. **Cleanup**: Remove container resources on deletion

## Security Considerations

### Namespace Isolation

Containers run with the following Linux namespaces:
- **PID**: Process ID isolation
- **IPC**: Inter-process communication isolation  
- **UTS**: Hostname isolation
- **Mount**: Filesystem isolation

### Resource Limits

- **Memory**: Configurable memory limits
- **CPU**: CPU usage restrictions
- **Storage**: Isolated root filesystem
- **Network**: Network namespace isolation (planned)

### Access Control

- **User mapping**: Containers run as specified user
- **Capability dropping**: Remove unnecessary capabilities
- **Read-only rootfs**: Optional read-only filesystem
- **Seccomp**: System call filtering (planned)

## Limitations

### Current Limitations

1. **Image Management**: No registry integration yet
2. **Network**: Basic network isolation only
3. **Volumes**: No persistent volume support
4. **Multi-stage builds**: Dockerfile parsing not implemented
5. **Compose**: No docker-compose support

### Planned Features

1. **Registry Integration**: Pull/push from container registries
2. **Volume Management**: Persistent volume support
3. **Network Management**: Custom network configurations
4. **Build System**: Dockerfile parsing and multi-stage builds
5. **Compose Support**: docker-compose file processing

## Troubleshooting

### Common Issues

#### runc Not Available
```
❌ Container Agent: runc is not available on this system.
```
**Solution**: Install runc:
```bash
# Ubuntu/Debian
sudo apt install runc

# CentOS/RHEL  
sudo yum install runc

# Build from source
git clone https://github.com/opencontainers/runc
cd runc && make && sudo make install
```

#### Container Won't Start
```
❌ Failed to start container <id>.
```
**Solutions**:
1. Check if image exists: `docker images`
2. Verify runc installation: `runc --version`
3. Check container logs: `docker logs <id>`
4. Inspect container config: `docker inspect <id>`

#### Permission Denied
```
❌ Error: permission denied
```
**Solutions**:
1. Ensure user has access to runc
2. Check container directory permissions
3. Verify namespace capabilities

### Debug Mode

Enable verbose logging:
```bash
awev 2  # Enable debug mode
```

This will show detailed container operations and error messages.

## Development

### Adding New Operations

To add new container operations:

1. **Add keyword detection** in `should_handle()`
2. **Implement operation method** (e.g., `_new_operation()`)
3. **Add to process()** method routing
4. **Update documentation** and help text

### Testing

Test container operations:
```bash
# Test basic operations
docker ps
docker run ubuntu
docker logs <container_id>

# Test error handling
docker run nonexistent-image
docker logs invalid-id
```

### Contributing

When contributing to the Container Agent:

1. Follow the existing code structure
2. Add comprehensive error handling
3. Update documentation for new features
4. Test with various container images
5. Ensure security best practices

## References

- [Open Container Initiative (OCI)](https://opencontainers.org/)
- [runc Documentation](https://github.com/opencontainers/runc)
- [Docker CLI Reference](https://docs.docker.com/engine/reference/commandline/cli/)
- [Linux Namespaces](https://man7.org/linux/man-pages/man7/namespaces.7.html)















