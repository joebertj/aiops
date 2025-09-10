#!/usr/bin/env python3
"""
Quick Test Runner for Awesh
Simple tests to verify basic functionality
"""

import asyncio
import subprocess
import os
import time
from pathlib import Path

class QuickTester:
    def __init__(self):
        self.awesh_binary = Path.home() / ".local" / "bin" / "awesh"
        self.results = []
    
    def log(self, message, status="INFO"):
        print(f"[{time.strftime('%H:%M:%S')}] {status}: {message}")
    
    def test_result(self, test_name, passed, details=""):
        emoji = "✅" if passed else "❌"
        self.log(f"{emoji} {test_name}: {'PASS' if passed else 'FAIL'}")
        if details:
            self.log(f"    {details}")
        self.results.append((test_name, passed, details))
    
    async def test_awesh_startup(self):
        """Test if awesh starts without errors"""
        self.log("Testing awesh startup...")
        
        try:
            # Test basic startup (awesh doesn't have --version flag)
            result = subprocess.run(
                [str(self.awesh_binary)],
                capture_output=True,
                text=True,
                timeout=5,
                input="exit\n"
            )
            
            if result.returncode == 0:
                self.test_result("awesh_startup", True, f"Version: {result.stdout.strip()}")
            else:
                self.test_result("awesh_startup", False, f"Exit code: {result.returncode}")
                
        except subprocess.TimeoutExpired:
            self.test_result("awesh_startup", False, "Timeout")
        except Exception as e:
            self.test_result("awesh_startup", False, str(e))
    
    async def test_basic_commands(self):
        """Test basic bash commands"""
        self.log("Testing basic bash commands...")
        
        commands = [
            ("ls", "list files"),
            ("pwd", "print directory"),
            ("echo hello", "echo command"),
            ("date", "get date"),
        ]
        
        for cmd, desc in commands:
            try:
                # Run through awesh
                process = await asyncio.create_subprocess_exec(
                    str(self.awesh_binary),
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=f"{cmd}\nexit\n".encode()),
                    timeout=15
                )
                
                if process.returncode == 0:
                    self.test_result(f"bash_{cmd}", True, desc)
                else:
                    self.test_result(f"bash_{cmd}", False, f"Exit: {process.returncode}")
                    
            except asyncio.TimeoutError:
                self.test_result(f"bash_{cmd}", False, "Timeout")
            except Exception as e:
                self.test_result(f"bash_{cmd}", False, str(e))
    
    async def test_ai_commands(self):
        """Test AI-related commands"""
        self.log("Testing AI commands...")
        
        try:
            # Test awea command
            process = await asyncio.create_subprocess_exec(
                str(self.awesh_binary),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input="awea\nexit\n".encode()),
                timeout=15
            )
            
            output = stdout.decode()
            if "AI Provider" in output or "Model" in output:
                self.test_result("awea_command", True, "AI status command works")
            else:
                self.test_result("awea_command", False, "No AI status output")
                
        except Exception as e:
            self.test_result("awea_command", False, str(e))
    
    async def test_process_detection(self):
        """Test if awesh processes are running"""
        self.log("Testing process detection...")
        
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            
            processes = result.stdout
            
            # Check for awesh processes
            if "awesh" in processes:
                self.test_result("awesh_process", True, "Awesh process found")
            else:
                self.test_result("awesh_process", False, "No awesh process found")
            
            # Check for security agent
            if "awesh_sec" in processes:
                self.test_result("security_agent_process", True, "Security agent running")
            else:
                self.test_result("security_agent_process", False, "Security agent not running")
                
        except Exception as e:
            self.test_result("process_detection", False, str(e))
    
    async def test_config_file(self):
        """Test configuration file"""
        self.log("Testing configuration...")
        
        config_file = Path.home() / ".aweshrc"
        
        if config_file.exists():
            self.test_result("config_exists", True, f"Found at {config_file}")
            
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                    
                if "AI_PROVIDER" in content:
                    self.test_result("config_ai_provider", True, "AI_PROVIDER set")
                else:
                    self.test_result("config_ai_provider", False, "AI_PROVIDER missing")
                    
                if "MODEL" in content:
                    self.test_result("config_model", True, "MODEL set")
                else:
                    self.test_result("config_model", False, "MODEL missing")
                    
            except Exception as e:
                self.test_result("config_read", False, str(e))
        else:
            self.test_result("config_exists", False, "Configuration file not found")
    
    async def run_quick_tests(self):
        """Run all quick tests"""
        self.log("Starting quick awesh tests...")
        start_time = time.time()
        
        await self.test_awesh_startup()
        await self.test_config_file()
        await self.test_process_detection()
        await self.test_basic_commands()
        await self.test_ai_commands()
        
        # Summary
        total = len(self.results)
        passed = len([r for r in self.results if r[1]])
        failed = total - passed
        
        duration = time.time() - start_time
        
        self.log("=" * 50)
        self.log("QUICK TEST SUMMARY")
        self.log("=" * 50)
        self.log(f"Total: {total}")
        self.log(f"Passed: {passed} ✅")
        self.log(f"Failed: {failed} ❌")
        self.log(f"Duration: {duration:.2f}s")
        self.log(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            self.log("\nFailed Tests:")
            for name, passed, details in self.results:
                if not passed:
                    self.log(f"  ❌ {name}: {details}")
        
        return passed == total

async def main():
    tester = QuickTester()
    success = await tester.run_quick_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
