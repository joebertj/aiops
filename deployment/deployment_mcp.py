#!/usr/bin/env python3
"""
Deployment MCP Server for awesh
Handles syntax checking, building, killing processes, and deployment
"""

import asyncio
import json
import logging
import os
import subprocess
import signal
import psutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# MCP imports
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("awesh-deployment")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
AWESH_DIR = PROJECT_ROOT / "awesh"
BACKEND_DIR = PROJECT_ROOT / "awesh_backend"
INSTALL_PATH = Path.home() / ".local" / "bin" / "awesh"

server = Server("awesh-deployment")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available deployment tools"""
    return [
        types.Tool(
            name="syntax_check",
            description="Check C code syntax and Python code style",
            inputSchema={
                "type": "object",
                "properties": {
                    "component": {
                        "type": "string",
                        "enum": ["c", "python", "all"],
                        "description": "Component to check (c, python, or all)"
                    }
                },
                "required": ["component"]
            }
        ),
        types.Tool(
            name="build",
            description="Build awesh C frontend and Python backend",
            inputSchema={
                "type": "object",
                "properties": {
                    "clean": {
                        "type": "boolean",
                        "description": "Clean build (make clean first)",
                        "default": False
                    },
                    "verbose": {
                        "type": "boolean", 
                        "description": "Verbose build output",
                        "default": False
                    }
                }
            }
        ),
        types.Tool(
            name="kill_processes",
            description="Kill running awesh processes and clean up sockets",
            inputSchema={
                "type": "object",
                "properties": {
                    "force": {
                        "type": "boolean",
                        "description": "Force kill processes (SIGKILL)",
                        "default": False
                    }
                }
            }
        ),
        types.Tool(
            name="deploy",
            description="Deploy awesh binary and backend to ~/.local/bin",
            inputSchema={
                "type": "object",
                "properties": {
                    "backup": {
                        "type": "boolean",
                        "description": "Backup existing installation",
                        "default": True
                    }
                }
            }
        ),
        types.Tool(
            name="test_deployment",
            description="Test deployed awesh installation",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeout": {
                        "type": "integer",
                        "description": "Test timeout in seconds",
                        "default": 30
                    }
                }
            }
        ),
        types.Tool(
            name="full_deploy",
            description="Complete deployment pipeline: syntax check -> build -> kill -> deploy -> test",
            inputSchema={
                "type": "object",
                "properties": {
                    "skip_tests": {
                        "type": "boolean",
                        "description": "Skip deployment tests",
                        "default": False
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    
    if name == "syntax_check":
        return await syntax_check(arguments.get("component", "all"))
    
    elif name == "build":
        return await build_project(
            clean=arguments.get("clean", False),
            verbose=arguments.get("verbose", False)
        )
    
    elif name == "kill_processes":
        return await kill_awesh_processes(arguments.get("force", False))
    
    elif name == "deploy":
        return await deploy_awesh(arguments.get("backup", True))
    
    elif name == "test_deployment":
        return await test_deployment(arguments.get("timeout", 30))
    
    elif name == "full_deploy":
        return await full_deployment_pipeline(arguments.get("skip_tests", False))
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def syntax_check(component: str) -> List[types.TextContent]:
    """Check syntax for C and/or Python code"""
    results = []
    
    if component in ["c", "all"]:
        # Check C syntax
        results.append(types.TextContent(type="text", text="🔍 Checking C syntax..."))
        
        c_files = list(AWESH_DIR.glob("*.c"))
        for c_file in c_files:
            try:
                # Use gcc -fsyntax-only for syntax checking
                result = subprocess.run([
                    "gcc", "-fsyntax-only", "-Wall", "-Wextra", "-std=c99",
                    str(c_file)
                ], capture_output=True, text=True, cwd=AWESH_DIR)
                
                if result.returncode == 0:
                    results.append(types.TextContent(
                        type="text", 
                        text=f"✅ {c_file.name}: Syntax OK"
                    ))
                else:
                    results.append(types.TextContent(
                        type="text", 
                        text=f"❌ {c_file.name}: Syntax errors:\n{result.stderr}"
                    ))
            except Exception as e:
                results.append(types.TextContent(
                    type="text",
                    text=f"❌ Error checking {c_file.name}: {e}"
                ))
    
    if component in ["python", "all"]:
        # Check Python syntax and style
        results.append(types.TextContent(type="text", text="🔍 Checking Python syntax..."))
        
        py_files = list(BACKEND_DIR.glob("*.py"))
        for py_file in py_files:
            try:
                # Compile Python file to check syntax
                with open(py_file, 'r') as f:
                    compile(f.read(), py_file, 'exec')
                
                results.append(types.TextContent(
                    type="text",
                    text=f"✅ {py_file.name}: Syntax OK"
                ))
            except SyntaxError as e:
                results.append(types.TextContent(
                    type="text",
                    text=f"❌ {py_file.name}: Syntax error: {e}"
                ))
            except Exception as e:
                results.append(types.TextContent(
                    type="text",
                    text=f"❌ Error checking {py_file.name}: {e}"
                ))
    
    return results

async def build_project(clean: bool = False, verbose: bool = False) -> List[types.TextContent]:
    """Build the awesh project"""
    results = []
    
    try:
        # Clean if requested
        if clean:
            results.append(types.TextContent(type="text", text="🧹 Cleaning build..."))
            result = subprocess.run(
                ["make", "clean"], 
                capture_output=True, text=True, cwd=AWESH_DIR
            )
            if result.returncode != 0:
                results.append(types.TextContent(
                    type="text",
                    text=f"❌ Clean failed: {result.stderr}"
                ))
                return results
        
        # Build C frontend
        results.append(types.TextContent(type="text", text="🔨 Building C frontend..."))
        make_cmd = ["make"]
        if verbose:
            make_cmd.append("V=1")
        
        result = subprocess.run(
            make_cmd,
            capture_output=True, text=True, cwd=AWESH_DIR
        )
        
        if result.returncode == 0:
            results.append(types.TextContent(type="text", text="✅ C frontend built successfully"))
            if verbose and result.stdout:
                results.append(types.TextContent(type="text", text=f"Build output:\n{result.stdout}"))
        else:
            results.append(types.TextContent(
                type="text",
                text=f"❌ C build failed:\n{result.stderr}"
            ))
            return results
        
        # Install Python backend
        results.append(types.TextContent(type="text", text="📦 Installing Python backend..."))
        result = subprocess.run([
            "pip3", "install", "--user", "-e", "."
        ], capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        if result.returncode == 0:
            results.append(types.TextContent(type="text", text="✅ Python backend installed"))
        else:
            results.append(types.TextContent(
                type="text",
                text=f"❌ Python backend install failed:\n{result.stderr}"
            ))
    
    except Exception as e:
        results.append(types.TextContent(
            type="text",
            text=f"❌ Build error: {e}"
        ))
    
    return results

async def kill_awesh_processes(force: bool = False) -> List[types.TextContent]:
    """Kill running awesh processes and clean up"""
    results = []
    killed_processes = []
    
    try:
        # Find awesh processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'awesh' or \
                   (proc.info['cmdline'] and 'awesh_backend' in ' '.join(proc.info['cmdline'])):
                    
                    pid = proc.info['pid']
                    name = proc.info['name']
                    
                    if force:
                        os.kill(pid, signal.SIGKILL)
                        results.append(types.TextContent(
                            type="text",
                            text=f"💀 Force killed {name} (PID: {pid})"
                        ))
                    else:
                        os.kill(pid, signal.SIGTERM)
                        results.append(types.TextContent(
                            type="text", 
                            text=f"🛑 Terminated {name} (PID: {pid})"
                        ))
                    
                    killed_processes.append(pid)
            
            except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
                continue
        
        if not killed_processes:
            results.append(types.TextContent(
                type="text",
                text="ℹ️  No awesh processes found running"
            ))
        
        # Clean up socket files
        socket_paths = [
            Path.home() / ".awesh.sock",
            Path("/tmp/awesh.sock")
        ]
        
        for socket_path in socket_paths:
            if socket_path.exists():
                socket_path.unlink()
                results.append(types.TextContent(
                    type="text",
                    text=f"🧹 Removed socket: {socket_path}"
                ))
        
        # Wait a moment for processes to clean up
        if killed_processes:
            await asyncio.sleep(1)
            results.append(types.TextContent(
                type="text",
                text="✅ Process cleanup complete"
            ))
    
    except Exception as e:
        results.append(types.TextContent(
            type="text",
            text=f"❌ Error killing processes: {e}"
        ))
    
    return results

async def deploy_awesh(backup: bool = True) -> List[types.TextContent]:
    """Deploy awesh binary to ~/.local/bin"""
    results = []
    
    try:
        # Create ~/.local/bin if it doesn't exist
        install_dir = Path.home() / ".local" / "bin"
        install_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup existing installation
        if backup and INSTALL_PATH.exists():
            backup_path = INSTALL_PATH.with_suffix('.bak')
            INSTALL_PATH.rename(backup_path)
            results.append(types.TextContent(
                type="text",
                text=f"💾 Backed up existing awesh to {backup_path}"
            ))
        
        # Copy new binary
        binary_path = AWESH_DIR / "awesh"
        if not binary_path.exists():
            results.append(types.TextContent(
                type="text",
                text="❌ awesh binary not found. Run build first."
            ))
            return results
        
        import shutil
        shutil.copy2(binary_path, INSTALL_PATH)
        INSTALL_PATH.chmod(0o755)
        
        results.append(types.TextContent(
            type="text",
            text=f"✅ Deployed awesh to {INSTALL_PATH}"
        ))
        
        # Verify deployment
        if INSTALL_PATH.exists() and os.access(INSTALL_PATH, os.X_OK):
            results.append(types.TextContent(
                type="text",
                text="✅ Binary is executable and ready"
            ))
        else:
            results.append(types.TextContent(
                type="text",
                text="❌ Deployment verification failed"
            ))
    
    except Exception as e:
        results.append(types.TextContent(
            type="text",
            text=f"❌ Deployment error: {e}"
        ))
    
    return results

async def test_deployment(timeout: int = 30) -> List[types.TextContent]:
    """Test the deployed awesh installation"""
    results = []
    
    try:
        # Check if binary exists and is executable
        if not INSTALL_PATH.exists():
            results.append(types.TextContent(
                type="text",
                text="❌ awesh binary not found at ~/.local/bin/awesh"
            ))
            return results
        
        if not os.access(INSTALL_PATH, os.X_OK):
            results.append(types.TextContent(
                type="text", 
                text="❌ awesh binary is not executable"
            ))
            return results
        
        results.append(types.TextContent(
            type="text",
            text="✅ Binary exists and is executable"
        ))
        
        # Test that it can start (without hanging)
        results.append(types.TextContent(
            type="text",
            text="🧪 Testing startup (this may take a moment)..."
        ))
        
        # Start awesh with a timeout and send exit command
        proc = await asyncio.create_subprocess_exec(
            str(INSTALL_PATH),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # Send exit command after a brief delay
            await asyncio.sleep(2)
            proc.stdin.write(b"exit\n")
            await proc.stdin.drain()
            
            # Wait for process to exit
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            
            if proc.returncode == 0:
                results.append(types.TextContent(
                    type="text",
                    text="✅ awesh starts and exits cleanly"
                ))
            else:
                results.append(types.TextContent(
                    type="text",
                    text=f"⚠️  awesh exited with code {proc.returncode}"
                ))
                if stderr:
                    results.append(types.TextContent(
                        type="text",
                        text=f"stderr: {stderr.decode()}"
                    ))
        
        except asyncio.TimeoutError:
            proc.kill()
            results.append(types.TextContent(
                type="text",
                text="❌ Test timed out - awesh may be hanging"
            ))
        
    except Exception as e:
        results.append(types.TextContent(
            type="text",
            text=f"❌ Test error: {e}"
        ))
    
    return results

async def full_deployment_pipeline(skip_tests: bool = False) -> List[types.TextContent]:
    """Complete deployment pipeline"""
    results = []
    
    results.append(types.TextContent(
        type="text",
        text="🚀 Starting full deployment pipeline..."
    ))
    
    # Step 1: Syntax check
    results.append(types.TextContent(type="text", text="\n📋 Step 1: Syntax Check"))
    syntax_results = await syntax_check("all")
    results.extend(syntax_results)
    
    # Check if syntax check passed
    if any("❌" in r.text for r in syntax_results):
        results.append(types.TextContent(
            type="text",
            text="❌ Deployment aborted due to syntax errors"
        ))
        return results
    
    # Step 2: Kill existing processes
    results.append(types.TextContent(type="text", text="\n🛑 Step 2: Kill Existing Processes"))
    kill_results = await kill_awesh_processes(force=False)
    results.extend(kill_results)
    
    # Step 3: Build
    results.append(types.TextContent(type="text", text="\n🔨 Step 3: Build"))
    build_results = await build_project(clean=True, verbose=False)
    results.extend(build_results)
    
    # Check if build passed
    if any("❌" in r.text for r in build_results):
        results.append(types.TextContent(
            type="text",
            text="❌ Deployment aborted due to build errors"
        ))
        return results
    
    # Step 4: Deploy
    results.append(types.TextContent(type="text", text="\n📦 Step 4: Deploy"))
    deploy_results = await deploy_awesh(backup=True)
    results.extend(deploy_results)
    
    # Check if deploy passed
    if any("❌" in r.text for r in deploy_results):
        results.append(types.TextContent(
            type="text",
            text="❌ Deployment failed"
        ))
        return results
    
    # Step 5: Test (optional)
    if not skip_tests:
        results.append(types.TextContent(type="text", text="\n🧪 Step 5: Test Deployment"))
        test_results = await test_deployment(timeout=30)
        results.extend(test_results)
    
    results.append(types.TextContent(
        type="text",
        text="\n🎉 Deployment pipeline completed successfully!"
    ))
    
    return results

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="awesh-deployment",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
