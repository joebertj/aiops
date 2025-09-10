#!/usr/bin/env python3
"""
Awesh Test Suite MCP
Comprehensive testing framework for awesh functionality
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import socket
import signal
import psutil

class AweshTestSuite:
    """Comprehensive test suite for awesh functionality"""
    
    def __init__(self):
        self.test_results = []
        self.awesh_process = None
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
        self.awesh_binary = Path.home() / ".local" / "bin" / "awesh"
        self.verbose = os.getenv('VERBOSE', '1')
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamps"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        self.log(f"{status_emoji} {test_name}: {status}")
        if details:
            self.log(f"    Details: {details}")
    
    async def setup_test_environment(self) -> bool:
        """Setup test environment and verify awesh is available"""
        self.log("Setting up test environment...")
        
        # Check if awesh binary exists
        if not self.awesh_binary.exists():
            self.log_test("awesh_binary_exists", "FAIL", f"Binary not found at {self.awesh_binary}")
            return False
        else:
            self.log_test("awesh_binary_exists", "PASS", f"Found at {self.awesh_binary}")
        
        # Check if awesh is executable
        if not os.access(self.awesh_binary, os.X_OK):
            self.log_test("awesh_binary_executable", "FAIL", "Binary not executable")
            return False
        else:
            self.log_test("awesh_binary_executable", "PASS")
        
        # Check configuration file
        config_file = Path.home() / ".aweshrc"
        if config_file.exists():
            self.log_test("config_file_exists", "PASS", f"Found at {config_file}")
            # Read and validate config
            try:
                with open(config_file, 'r') as f:
                    config_content = f.read()
                    if "AI_PROVIDER" in config_content and "MODEL" in config_content:
                        self.log_test("config_file_valid", "PASS", "Contains required settings")
                    else:
                        self.log_test("config_file_valid", "FAIL", "Missing required settings")
            except Exception as e:
                self.log_test("config_file_readable", "FAIL", str(e))
        else:
            self.log_test("config_file_exists", "FAIL", "Configuration file not found")
        
        return True
    
    async def test_bash_commands(self) -> None:
        """Test common bash commands"""
        self.log("Testing common bash commands...")
        
        bash_tests = [
            ("ls", "list directory contents"),
            ("pwd", "print working directory"),
            ("echo 'hello world'", "echo command"),
            ("date", "get current date"),
            ("whoami", "get current user"),
            ("uname -a", "system information"),
            ("ps aux | head -5", "process list"),
            ("df -h | head -3", "disk usage"),
            ("free -h", "memory usage"),
        ]
        
        for command, description in bash_tests:
            try:
                result = await self.run_awesh_command(command)
                if result["exit_code"] == 0:
                    self.log_test(f"bash_{command.replace(' ', '_').replace('|', '_')}", "PASS", description)
                else:
                    self.log_test(f"bash_{command.replace(' ', '_').replace('|', '_')}", "FAIL", 
                                f"Exit code: {result['exit_code']}, Error: {result.get('stderr', '')}")
            except Exception as e:
                self.log_test(f"bash_{command.replace(' ', '_').replace('|', '_')}", "FAIL", str(e))
    
    async def test_natural_queries(self) -> None:
        """Test natural language queries for Docker and Kubernetes"""
        self.log("Testing natural language queries...")
        
        natural_queries = [
            ("show my docker containers", "Docker container list"),
            ("list all kubernetes pods", "Kubernetes pod listing"),
            ("what's my current directory", "Directory information"),
            ("show system resources", "System resource information"),
            ("list running processes", "Process listing"),
            ("check disk space", "Disk space check"),
            ("show network connections", "Network information"),
        ]
        
        for query, description in natural_queries:
            try:
                result = await self.run_awesh_command(query)
                # Natural queries should return AI responses, not bash commands
                if "awesh_cmd:" in result.get("stdout", "") or "awesh_edit:" in result.get("stdout", ""):
                    self.log_test(f"natural_{query.replace(' ', '_')}", "PASS", description)
                else:
                    self.log_test(f"natural_{query.replace(' ', '_')}", "FAIL", 
                                "No AI response format detected")
            except Exception as e:
                self.log_test(f"natural_{query.replace(' ', '_')}", "FAIL", str(e))
    
    async def test_prompt_correctness(self) -> None:
        """Test prompt format and dynamic context"""
        self.log("Testing prompt correctness...")
        
        # Test prompt format
        try:
            # Start awesh and capture initial prompt
            result = await self.run_awesh_command("pwd", capture_prompt=True)
            
            if "🤖:" in result.get("prompt", ""):
                self.log_test("prompt_ai_emoji", "PASS", "AI emoji present")
            else:
                self.log_test("prompt_ai_emoji", "FAIL", "AI emoji missing")
            
            if "🔒:" in result.get("prompt", ""):
                self.log_test("prompt_security_emoji", "PASS", "Security emoji present")
            else:
                self.log_test("prompt_security_emoji", "FAIL", "Security emoji missing")
            
            if "☸️" in result.get("prompt", ""):
                self.log_test("prompt_k8s_emoji", "PASS", "Kubernetes emoji present")
            else:
                self.log_test("prompt_k8s_emoji", "FAIL", "Kubernetes emoji missing")
            
            if "🌿" in result.get("prompt", ""):
                self.log_test("prompt_git_emoji", "PASS", "Git emoji present")
            else:
                self.log_test("prompt_git_emoji", "FAIL", "Git emoji missing")
                
        except Exception as e:
            self.log_test("prompt_format", "FAIL", str(e))
    
    async def test_awex_commands(self) -> None:
        """Test all aweX control commands"""
        self.log("Testing aweX control commands...")
        
        awex_commands = [
            ("awea", "Show AI status"),
            ("awes", "Show verbose status"),
            ("awev", "Show verbose level"),
            ("awev 0", "Set verbose to 0"),
            ("awev 1", "Set verbose to 1"),
            ("awev 2", "Set verbose to 2"),
            ("aweh", "Show help"),
        ]
        
        for command, description in awex_commands:
            try:
                result = await self.run_awesh_command(command)
                if result["exit_code"] == 0:
                    self.log_test(f"awex_{command.replace(' ', '_')}", "PASS", description)
                else:
                    self.log_test(f"awex_{command.replace(' ', '_')}", "FAIL", 
                                f"Exit code: {result['exit_code']}")
            except Exception as e:
                self.log_test(f"awex_{command.replace(' ', '_')}", "FAIL", str(e))
    
    async def test_ai_functionality(self) -> None:
        """Test AI integration and response handling"""
        self.log("Testing AI functionality...")
        
        ai_tests = [
            ("what is 2+2?", "Simple math question"),
            ("explain what a shell is", "Conceptual question"),
            ("list the files in this directory", "Directory listing request"),
            ("what's the weather like?", "General knowledge question"),
        ]
        
        for query, description in ai_tests:
            try:
                result = await self.run_awesh_command(query)
                stdout = result.get("stdout", "")
                
                if "awesh_cmd:" in stdout or "awesh_edit:" in stdout:
                    self.log_test(f"ai_{query.replace(' ', '_').replace('?', '')}", "PASS", description)
                else:
                    self.log_test(f"ai_{query.replace(' ', '_').replace('?', '')}", "FAIL", 
                                "No AI response format detected")
            except Exception as e:
                self.log_test(f"ai_{query.replace(' ', '_').replace('?', '')}", "FAIL", str(e))
    
    async def test_security_agent(self) -> None:
        """Test security agent and rogue process detection"""
        self.log("Testing security agent functionality...")
        
        # Test 1: Check if security agent is running
        try:
            result = await self.run_awesh_command("ps aux | grep awesh_sec | grep -v grep")
            if "awesh_sec" in result.get("stdout", ""):
                self.log_test("security_agent_running", "PASS", "Security agent process found")
            else:
                self.log_test("security_agent_running", "FAIL", "Security agent not running")
        except Exception as e:
            self.log_test("security_agent_running", "FAIL", str(e))
        
        # Test 2: Check shared memory
        try:
            import mmap
            import tempfile
            
            # Try to read shared memory
            shm_name = f"/awesh_security_status_{os.getenv('USER', 'unknown')}"
            try:
                with open(shm_name, 'r') as f:
                    content = f.read()
                    if content:
                        self.log_test("security_shared_memory", "PASS", f"Content: {content[:50]}...")
                    else:
                        self.log_test("security_shared_memory", "FAIL", "Empty shared memory")
            except FileNotFoundError:
                self.log_test("security_shared_memory", "FAIL", "Shared memory not found")
        except Exception as e:
            self.log_test("security_shared_memory", "FAIL", str(e))
        
        # Test 3: Create a test rogue process
        try:
            # Create a simple test script
            test_script = self.test_dir / "test_rogue.sh"
            with open(test_script, 'w') as f:
                f.write("#!/bin/bash\nwhile true; do echo 'test rogue process'; sleep 5; done\n")
            test_script.chmod(0o755)
            
            # Start the rogue process
            rogue_proc = subprocess.Popen([str(test_script)], 
                                        stdout=subprocess.DEVNULL, 
                                        stderr=subprocess.DEVNULL)
            
            # Wait a bit for security agent to detect it
            await asyncio.sleep(10)
            
            # Check if it's detected in the prompt
            result = await self.run_awesh_command("pwd", capture_prompt=True)
            prompt = result.get("prompt", "")
            
            if "👹" in prompt or "rogue" in prompt.lower():
                self.log_test("rogue_process_detection", "PASS", "Rogue process detected")
            else:
                self.log_test("rogue_process_detection", "FAIL", "Rogue process not detected")
            
            # Clean up
            rogue_proc.terminate()
            test_script.unlink()
            
        except Exception as e:
            self.log_test("rogue_process_detection", "FAIL", str(e))
    
    async def test_documentation_checks(self) -> None:
        """Test functionality documented in README and ARCHITECTURE"""
        self.log("Testing documented functionality...")
        
        # Test 1: Check if all documented features are present
        documented_features = [
            "vi-style modal system",
            "dynamic prompt with context",
            "security agent integration",
            "AI-powered command processing",
            "Kubernetes integration",
            "Docker integration",
        ]
        
        for feature in documented_features:
            # This is a placeholder - would need specific tests for each feature
            self.log_test(f"doc_feature_{feature.replace(' ', '_')}", "PENDING", 
                         f"Feature: {feature}")
        
        # Test 2: Check architecture compliance
        try:
            # Check if 3-process architecture is running
            result = await self.run_awesh_command("ps aux | grep -E '(awesh|python.*backend)' | grep -v grep")
            processes = result.get("stdout", "")
            
            if "awesh" in processes and "python" in processes:
                self.log_test("architecture_3_process", "PASS", "3-process architecture detected")
            else:
                self.log_test("architecture_3_process", "FAIL", "3-process architecture not detected")
        except Exception as e:
            self.log_test("architecture_3_process", "FAIL", str(e))
    
    async def run_awesh_command(self, command: str, capture_prompt: bool = False) -> Dict[str, Any]:
        """Run a command through awesh and return the result"""
        try:
            # Create a temporary file for output
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
                temp_file = f.name
            
            # Run awesh with the command
            env = os.environ.copy()
            env['VERBOSE'] = self.verbose
            
            process = await asyncio.create_subprocess_exec(
                str(self.awesh_binary),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            # Send command and wait for response
            stdout, stderr = await process.communicate(input=f"{command}\nexit\n".encode())
            
            result = {
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "exit_code": process.returncode
            }
            
            # Extract prompt if requested
            if capture_prompt:
                lines = result["stdout"].split('\n')
                for line in lines:
                    if "🤖:" in line and ">" in line:
                        result["prompt"] = line
                        break
            
            return result
            
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        self.log("Starting comprehensive awesh test suite...")
        start_time = time.time()
        
        # Setup
        if not await self.setup_test_environment():
            self.log("Test environment setup failed. Aborting tests.", "ERROR")
            return {"success": False, "error": "Setup failed"}
        
        # Run all test categories
        test_categories = [
            ("Bash Commands", self.test_bash_commands),
            ("Natural Queries", self.test_natural_queries),
            ("Prompt Correctness", self.test_prompt_correctness),
            ("AweX Commands", self.test_awex_commands),
            ("AI Functionality", self.test_ai_functionality),
            ("Security Agent", self.test_security_agent),
            ("Documentation Checks", self.test_documentation_checks),
        ]
        
        for category_name, test_func in test_categories:
            self.log(f"Running {category_name} tests...")
            try:
                await test_func()
            except Exception as e:
                self.log(f"Error in {category_name} tests: {e}", "ERROR")
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        pending_tests = len([r for r in self.test_results if r["status"] == "PENDING"])
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Summary
        self.log("=" * 60)
        self.log("TEST SUITE SUMMARY")
        self.log("=" * 60)
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed: {passed_tests} ✅")
        self.log(f"Failed: {failed_tests} ❌")
        self.log(f"Pending: {pending_tests} ⚠️")
        self.log(f"Duration: {duration:.2f} seconds")
        self.log(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        return {
            "success": failed_tests == 0,
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pending": pending_tests,
            "duration": duration,
            "success_rate": passed_tests/total_tests*100,
            "results": self.test_results
        }

async def main():
    """Main entry point for the test suite"""
    test_suite = AweshTestSuite()
    results = await test_suite.run_all_tests()
    
    # Save results to file
    results_file = Path(__file__).parent / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    test_suite.log(f"Test results saved to {results_file}")
    
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)

if __name__ == "__main__":
    asyncio.run(main())
