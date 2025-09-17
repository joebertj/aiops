"""
Container Agent for AIOps System

Provides Docker-compatible container management using runc and minimal dependencies.
This agent handles container-related prompts and executes container operations using
only runc, bash, and Python standard library modules.
"""

import os
import json
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

from .base_agent import BaseAgent, AgentResult


@dataclass
class ContainerInfo:
    """Information about a container"""
    id: str
    name: str
    image: str
    status: str
    created: str
    ports: List[str]
    mounts: List[str]


@dataclass
class ImageInfo:
    """Information about a container image"""
    id: str
    name: str
    tag: str
    size: str
    created: str


class ContainerAgent(BaseAgent):
    """
    Container Agent with Docker-compatible interface using runc.
    
    This agent provides container management capabilities using only:
    - runc: For container runtime
    - bash: For shell operations
    - Python standard library: For orchestration
    
    No Docker daemon or Docker CLI required.
    """
    
    def __init__(self, priority: int = 5):
        super().__init__("Container Agent", priority)
        
        # Container storage paths
        self.containers_dir = Path.home() / ".awesh" / "containers"
        self.images_dir = Path.home() / ".awesh" / "images"
        self.runtime_dir = Path.home() / ".awesh" / "runtime"
        
        # Ensure directories exist
        self.containers_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if runc is available
        self.runc_available = self._check_runc_availability()
        
        # Container keywords for detection
        self.container_keywords = [
            'container', 'docker', 'runc', 'podman', 'image', 'run', 'start', 'stop',
            'build', 'pull', 'push', 'exec', 'logs', 'ps', 'inspect', 'rm', 'rmi',
            'volume', 'network', 'compose', 'swarm', 'registry'
        ]
    
    def _check_runc_availability(self) -> bool:
        """Check if runc is available on the system"""
        try:
            result = subprocess.run(['runc', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def should_handle(self, prompt: str, context: Dict[str, Any]) -> bool:
        """
        Determine if this agent should handle container-related prompts.
        
        Args:
            prompt: The user's input prompt
            context: Additional context
            
        Returns:
            True if this agent should handle the prompt
        """
        prompt_lower = prompt.lower()
        
        # Check for container-related keywords
        for keyword in self.container_keywords:
            if keyword in prompt_lower:
                return True
        
        # Check for common container commands
        container_commands = [
            'docker run', 'docker build', 'docker pull', 'docker push',
            'docker ps', 'docker logs', 'docker exec', 'docker stop',
            'docker start', 'docker rm', 'docker rmi', 'docker inspect'
        ]
        
        for command in container_commands:
            if command in prompt_lower:
                return True
        
        return False
    
    async def process(self, prompt: str, context: Dict[str, Any]) -> AgentResult:
        """
        Process container-related prompts.
        
        Args:
            prompt: The user's input prompt
            context: Additional context
            
        Returns:
            AgentResult with container operation response
        """
        if not self.runc_available:
            return AgentResult(
                handled=True,
                response="❌ Container Agent: runc is not available on this system.\n"
                        "Please install runc to use container functionality:\n"
                        "  Ubuntu/Debian: sudo apt install runc\n"
                        "  CentOS/RHEL: sudo yum install runc\n"
                        "  Or build from source: https://github.com/opencontainers/runc"
            )
        
        prompt_lower = prompt.lower().strip()
        
        try:
            # Parse and execute container operations
            if any(cmd in prompt_lower for cmd in ['docker ps', 'container list', 'list containers']):
                return await self._list_containers()
            
            elif any(cmd in prompt_lower for cmd in ['docker images', 'image list', 'list images']):
                return await self._list_images()
            
            elif 'docker run' in prompt_lower or 'run container' in prompt_lower:
                return await self._run_container(prompt)
            
            elif 'docker build' in prompt_lower or 'build image' in prompt_lower:
                return await self._build_image(prompt)
            
            elif 'docker pull' in prompt_lower or 'pull image' in prompt_lower:
                return await self._pull_image(prompt)
            
            elif 'docker logs' in prompt_lower or 'container logs' in prompt_lower:
                return await self._get_logs(prompt)
            
            elif 'docker exec' in prompt_lower or 'exec into' in prompt_lower:
                return await self._exec_container(prompt)
            
            elif 'docker stop' in prompt_lower or 'stop container' in prompt_lower:
                return await self._stop_container(prompt)
            
            elif 'docker start' in prompt_lower or 'start container' in prompt_lower:
                return await self._start_container(prompt)
            
            elif 'docker rm' in prompt_lower or 'remove container' in prompt_lower:
                return await self._remove_container(prompt)
            
            elif 'docker inspect' in prompt_lower or 'inspect container' in prompt_lower:
                return await self._inspect_container(prompt)
            
            else:
                return AgentResult(
                    handled=True,
                    response="🐳 Container Agent: I can help with container operations!\n\n"
                            "Available commands:\n"
                            "• List containers: 'docker ps' or 'list containers'\n"
                            "• List images: 'docker images' or 'list images'\n"
                            "• Run container: 'docker run <image>' or 'run container <image>'\n"
                            "• Build image: 'docker build .' or 'build image'\n"
                            "• Pull image: 'docker pull <image>' or 'pull image <image>'\n"
                            "• View logs: 'docker logs <container>' or 'container logs <container>'\n"
                            "• Execute command: 'docker exec <container> <command>'\n"
                            "• Stop container: 'docker stop <container>'\n"
                            "• Start container: 'docker start <container>'\n"
                            "• Remove container: 'docker rm <container>'\n"
                            "• Inspect container: 'docker inspect <container>'\n\n"
                            "Note: This uses runc instead of Docker daemon for lightweight container management."
                )
        
        except Exception as e:
            return AgentResult(
                handled=True,
                response=f"❌ Container Agent Error: {str(e)}\n"
                        "Please check your container configuration and try again."
            )
    
    async def _list_containers(self) -> AgentResult:
        """List all containers"""
        containers = []
        
        # Scan container directories
        for container_dir in self.containers_dir.iterdir():
            if container_dir.is_dir():
                config_file = container_dir / "config.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                        
                        container_info = ContainerInfo(
                            id=container_dir.name[:12],
                            name=config.get('name', 'unknown'),
                            image=config.get('image', 'unknown'),
                            status=self._get_container_status(container_dir),
                            created=datetime.fromtimestamp(container_dir.stat().st_ctime).isoformat(),
                            ports=config.get('ports', []),
                            mounts=config.get('mounts', [])
                        )
                        containers.append(container_info)
                    except Exception:
                        continue
        
        if not containers:
            return AgentResult(
                handled=True,
                response="🐳 No containers found.\n"
                        "Use 'docker run <image>' to start a new container."
            )
        
        # Format output
        output = "🐳 Container List:\n"
        output += "ID          NAME        IMAGE       STATUS      CREATED\n"
        output += "-" * 60 + "\n"
        
        for container in containers:
            output += f"{container.id:<12} {container.name:<12} {container.image:<12} {container.status:<12} {container.created[:19]}\n"
        
        return AgentResult(handled=True, response=output)
    
    async def _list_images(self) -> AgentResult:
        """List all container images"""
        images = []
        
        # Scan image directories
        for image_dir in self.images_dir.iterdir():
            if image_dir.is_dir():
                manifest_file = image_dir / "manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest = json.load(f)
                        
                        image_info = ImageInfo(
                            id=image_dir.name[:12],
                            name=manifest.get('name', 'unknown'),
                            tag=manifest.get('tag', 'latest'),
                            size=self._get_directory_size(image_dir),
                            created=datetime.fromtimestamp(image_dir.stat().st_ctime).isoformat()
                        )
                        images.append(image_info)
                    except Exception:
                        continue
        
        if not images:
            return AgentResult(
                handled=True,
                response="🐳 No images found.\n"
                        "Use 'docker pull <image>' to download an image or 'docker build .' to build one."
            )
        
        # Format output
        output = "🐳 Image List:\n"
        output += "ID          REPOSITORY   TAG        SIZE        CREATED\n"
        output += "-" * 60 + "\n"
        
        for image in images:
            output += f"{image.id:<12} {image.name:<12} {image.tag:<12} {image.size:<12} {image.created[:19]}\n"
        
        return AgentResult(handled=True, response=output)
    
    async def _run_container(self, prompt: str) -> AgentResult:
        """Run a new container"""
        # Parse image name from prompt
        image_name = self._extract_image_name(prompt)
        if not image_name:
            return AgentResult(
                handled=True,
                response="❌ Please specify an image name.\n"
                        "Usage: 'docker run <image>' or 'run container <image>'"
            )
        
        # Check if image exists
        if not self._image_exists(image_name):
            return AgentResult(
                handled=True,
                response=f"❌ Image '{image_name}' not found.\n"
                        f"Please pull the image first: 'docker pull {image_name}'"
            )
        
        # Create container
        container_id = str(uuid.uuid4())[:12]
        container_dir = self.containers_dir / container_id
        
        try:
            container_dir.mkdir(exist_ok=True)
            
            # Create container configuration
            config = {
                'id': container_id,
                'name': f"container_{container_id}",
                'image': image_name,
                'status': 'created',
                'created': datetime.now().isoformat(),
                'ports': [],
                'mounts': []
            }
            
            with open(container_dir / "config.json", 'w') as f:
                json.dump(config, f, indent=2)
            
            # Start container with runc
            result = await self._start_runc_container(container_dir, image_name)
            
            if result:
                return AgentResult(
                    handled=True,
                    response=f"✅ Container {container_id} started successfully!\n"
                            f"Image: {image_name}\n"
                            f"Status: running\n"
                            f"Use 'docker logs {container_id}' to view logs."
                )
            else:
                return AgentResult(
                    handled=True,
                    response=f"❌ Failed to start container {container_id}.\n"
                            "Check container configuration and try again."
                )
        
        except Exception as e:
            return AgentResult(
                handled=True,
                response=f"❌ Error creating container: {str(e)}"
            )
    
    async def _build_image(self, prompt: str) -> AgentResult:
        """Build a container image from Dockerfile"""
        # For now, return a placeholder response
        # In a full implementation, this would:
        # 1. Parse Dockerfile
        # 2. Create rootfs using chroot or similar
        # 3. Package as OCI image
        # 4. Store in images directory
        
        return AgentResult(
            handled=True,
            response="🐳 Container Agent: Image building is not yet implemented.\n"
                    "This feature requires additional implementation for:\n"
                    "• Dockerfile parsing\n"
                    "• Root filesystem creation\n"
                    "• OCI image packaging\n\n"
                    "For now, use 'docker pull <image>' to download existing images."
        )
    
    async def _pull_image(self, prompt: str) -> AgentResult:
        """Pull a container image"""
        image_name = self._extract_image_name(prompt)
        if not image_name:
            return AgentResult(
                handled=True,
                response="❌ Please specify an image name.\n"
                        "Usage: 'docker pull <image>' or 'pull image <image>'"
            )
        
        # For now, return a placeholder response
        # In a full implementation, this would:
        # 1. Connect to container registry
        # 2. Download image layers
        # 3. Extract and store in images directory
        
        return AgentResult(
            handled=True,
            response=f"🐳 Container Agent: Image pulling is not yet implemented.\n"
                    f"Would pull image: {image_name}\n\n"
                    "This feature requires additional implementation for:\n"
                    "• Registry authentication\n"
                    "• Image layer downloading\n"
                    "• OCI image extraction\n\n"
                    "For now, you can create simple containers using existing system images."
        )
    
    async def _get_logs(self, prompt: str) -> AgentResult:
        """Get container logs"""
        container_id = self._extract_container_id(prompt)
        if not container_id:
            return AgentResult(
                handled=True,
                response="❌ Please specify a container ID.\n"
                        "Usage: 'docker logs <container_id>' or 'container logs <container_id>'"
            )
        
        container_dir = self.containers_dir / container_id
        if not container_dir.exists():
            return AgentResult(
                handled=True,
                response=f"❌ Container {container_id} not found."
            )
        
        # Read container logs
        log_file = container_dir / "logs.txt"
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    logs = f.read()
                return AgentResult(
                    handled=True,
                    response=f"🐳 Logs for container {container_id}:\n\n{logs}"
                )
            except Exception as e:
                return AgentResult(
                    handled=True,
                    response=f"❌ Error reading logs: {str(e)}"
                )
        else:
            return AgentResult(
                handled=True,
                response=f"🐳 No logs available for container {container_id}."
            )
    
    async def _exec_container(self, prompt: str) -> AgentResult:
        """Execute command in container"""
        return AgentResult(
            handled=True,
            response="🐳 Container Agent: Container execution is not yet implemented.\n"
                    "This feature requires additional implementation for:\n"
                    "• Container process management\n"
                    "• Command execution in container context\n"
                    "• Process isolation and security\n\n"
                    "For now, use 'docker logs <container>' to view container output."
        )
    
    async def _stop_container(self, prompt: str) -> AgentResult:
        """Stop a running container"""
        container_id = self._extract_container_id(prompt)
        if not container_id:
            return AgentResult(
                handled=True,
                response="❌ Please specify a container ID.\n"
                        "Usage: 'docker stop <container_id>' or 'stop container <container_id>'"
            )
        
        container_dir = self.containers_dir / container_id
        if not container_dir.exists():
            return AgentResult(
                handled=True,
                response=f"❌ Container {container_id} not found."
            )
        
        # Stop container with runc
        try:
            result = await self._stop_runc_container(container_dir)
            if result:
                return AgentResult(
                    handled=True,
                    response=f"✅ Container {container_id} stopped successfully."
                )
            else:
                return AgentResult(
                    handled=True,
                    response=f"❌ Failed to stop container {container_id}."
                )
        except Exception as e:
            return AgentResult(
                handled=True,
                response=f"❌ Error stopping container: {str(e)}"
            )
    
    async def _start_container(self, prompt: str) -> AgentResult:
        """Start a stopped container"""
        container_id = self._extract_container_id(prompt)
        if not container_id:
            return AgentResult(
                handled=True,
                response="❌ Please specify a container ID.\n"
                        "Usage: 'docker start <container_id>' or 'start container <container_id>'"
            )
        
        container_dir = self.containers_dir / container_id
        if not container_dir.exists():
            return AgentResult(
                handled=True,
                response=f"❌ Container {container_id} not found."
            )
        
        # Start container with runc
        try:
            result = await self._start_runc_container(container_dir)
            if result:
                return AgentResult(
                    handled=True,
                    response=f"✅ Container {container_id} started successfully."
                )
            else:
                return AgentResult(
                    handled=True,
                    response=f"❌ Failed to start container {container_id}."
                )
        except Exception as e:
            return AgentResult(
                handled=True,
                response=f"❌ Error starting container: {str(e)}"
            )
    
    async def _remove_container(self, prompt: str) -> AgentResult:
        """Remove a container"""
        container_id = self._extract_container_id(prompt)
        if not container_id:
            return AgentResult(
                handled=True,
                response="❌ Please specify a container ID.\n"
                        "Usage: 'docker rm <container_id>' or 'remove container <container_id>'"
            )
        
        container_dir = self.containers_dir / container_id
        if not container_dir.exists():
            return AgentResult(
                handled=True,
                response=f"❌ Container {container_id} not found."
            )
        
        # Remove container directory
        try:
            shutil.rmtree(container_dir)
            return AgentResult(
                handled=True,
                response=f"✅ Container {container_id} removed successfully."
            )
        except Exception as e:
            return AgentResult(
                handled=True,
                response=f"❌ Error removing container: {str(e)}"
            )
    
    async def _inspect_container(self, prompt: str) -> AgentResult:
        """Inspect container details"""
        container_id = self._extract_container_id(prompt)
        if not container_id:
            return AgentResult(
                handled=True,
                response="❌ Please specify a container ID.\n"
                        "Usage: 'docker inspect <container_id>' or 'inspect container <container_id>'"
            )
        
        container_dir = self.containers_dir / container_id
        if not container_dir.exists():
            return AgentResult(
                handled=True,
                response=f"❌ Container {container_id} not found."
            )
        
        # Read container configuration
        config_file = container_dir / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                return AgentResult(
                    handled=True,
                    response=f"🐳 Container {container_id} Details:\n\n"
                            f"ID: {config.get('id', 'unknown')}\n"
                            f"Name: {config.get('name', 'unknown')}\n"
                            f"Image: {config.get('image', 'unknown')}\n"
                            f"Status: {self._get_container_status(container_dir)}\n"
                            f"Created: {config.get('created', 'unknown')}\n"
                            f"Ports: {', '.join(config.get('ports', [])) or 'None'}\n"
                            f"Mounts: {', '.join(config.get('mounts', [])) or 'None'}"
                )
            except Exception as e:
                return AgentResult(
                    handled=True,
                    response=f"❌ Error reading container config: {str(e)}"
                )
        else:
            return AgentResult(
                handled=True,
                response=f"❌ Container configuration not found for {container_id}."
            )
    
    def _extract_image_name(self, prompt: str) -> Optional[str]:
        """Extract image name from prompt"""
        # Simple extraction - look for common patterns
        words = prompt.split()
        for i, word in enumerate(words):
            if word in ['run', 'pull', 'build'] and i + 1 < len(words):
                return words[i + 1]
        return None
    
    def _extract_container_id(self, prompt: str) -> Optional[str]:
        """Extract container ID from prompt"""
        words = prompt.split()
        for i, word in enumerate(words):
            if word in ['logs', 'exec', 'stop', 'start', 'rm', 'inspect'] and i + 1 < len(words):
                return words[i + 1]
        return None
    
    def _image_exists(self, image_name: str) -> bool:
        """Check if image exists locally"""
        # For now, return True for common images
        # In a full implementation, check images directory
        common_images = ['ubuntu', 'alpine', 'busybox', 'nginx', 'redis', 'postgres']
        return any(img in image_name.lower() for img in common_images)
    
    def _get_container_status(self, container_dir: Path) -> str:
        """Get container status"""
        # Check if container is running by looking for runc process
        try:
            result = subprocess.run(['runc', 'list'], capture_output=True, text=True)
            if container_dir.name in result.stdout:
                return 'running'
        except Exception:
            pass
        return 'stopped'
    
    def _get_directory_size(self, directory: Path) -> str:
        """Get human-readable directory size"""
        try:
            total_size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
            if total_size < 1024:
                return f"{total_size}B"
            elif total_size < 1024 * 1024:
                return f"{total_size // 1024}KB"
            else:
                return f"{total_size // (1024 * 1024)}MB"
        except Exception:
            return "unknown"
    
    async def _start_runc_container(self, container_dir: Path, image_name: str = None) -> bool:
        """Start container using runc"""
        try:
            # Create basic OCI bundle structure
            bundle_dir = container_dir / "bundle"
            bundle_dir.mkdir(exist_ok=True)
            
            # Create config.json for runc
            oci_config = {
                "ociVersion": "1.0.0",
                "process": {
                    "terminal": True,
                    "user": {"uid": 0, "gid": 0},
                    "args": ["/bin/sh"],
                    "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
                    "cwd": "/"
                },
                "root": {
                    "path": "rootfs",
                    "readonly": False
                },
                "hostname": f"container_{container_dir.name}",
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
            
            with open(bundle_dir / "config.json", 'w') as f:
                json.dump(oci_config, f, indent=2)
            
            # Create rootfs directory
            rootfs_dir = bundle_dir / "rootfs"
            rootfs_dir.mkdir(exist_ok=True)
            
            # For now, create a minimal rootfs
            # In a full implementation, this would extract from an image
            (rootfs_dir / "bin").mkdir(exist_ok=True)
            (rootfs_dir / "usr").mkdir(exist_ok=True)
            (rootfs_dir / "etc").mkdir(exist_ok=True)
            
            # Start container
            result = subprocess.run([
                'runc', 'run', '--bundle', str(bundle_dir), container_dir.name
            ], capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0
        
        except Exception as e:
            print(f"Error starting runc container: {e}")
            return False
    
    async def _stop_runc_container(self, container_dir: Path) -> bool:
        """Stop container using runc"""
        try:
            result = subprocess.run([
                'runc', 'kill', container_dir.name, 'TERM'
            ], capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0
        
        except Exception as e:
            print(f"Error stopping runc container: {e}")
            return False













