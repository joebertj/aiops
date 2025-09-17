#!/usr/bin/env python3
"""
Advanced Test Suite for Awesh
Tests specific functionality like AI responses, security detection, etc.
"""

import asyncio
import subprocess
import os
import time
import tempfile
from pathlib import Path

class AdvancedTester:
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
    
    async def run_awesh_command(self, command, timeout=10):
        """Run a command through awesh and return the result"""
        try:
            process = await asyncio.create_subprocess_exec(
                str(self.awesh_binary),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=f"{command}\nexit\n".encode()),
                timeout=timeout
            )
            
            return {
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "exit_code": process.returncode
            }
        except asyncio.TimeoutError:
            return {"stdout": "", "stderr": "Timeout", "exit_code": -1}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "exit_code": -1}
    
    async def test_ai_responses(self):
        """Test AI response format and content"""
        self.log("Testing AI responses...")
        
        ai_queries = [
            ("what is 2+2?", "awesh_edit:"),
            ("list files in this directory", "awesh_cmd:"),
            ("explain what a shell is", "awesh_edit:"),
            ("show me the current time", "awesh_cmd:"),
        ]
        
        for query, expected_format in ai_queries:
            result = await self.run_awesh_command(query, timeout=20)
            output = result["stdout"]
            
            if expected_format in output:
                self.test_result(f"ai_response_{query.replace(' ', '_').replace('?', '')}", 
                               True, f"Got {expected_format} response")
            else:
                self.test_result(f"ai_response_{query.replace(' ', '_').replace('?', '')}", 
                               False, f"Expected {expected_format}, got: {output[:100]}...")
    
    async def test_prompt_format(self):
        """Test prompt format and dynamic elements"""
        self.log("Testing prompt format...")
        
        result = await self.run_awesh_command("pwd", timeout=15)
        output = result["stdout"]
        
        # Check for required prompt elements
        prompt_elements = [
            ("🤖", "AI emoji"),
            ("🔒", "Security emoji"),
            ("☸️", "Kubernetes emoji"),
            ("🌿", "Git emoji"),
            (">", "Prompt indicator"),
        ]
        
        for element, description in prompt_elements:
            if element in output:
                self.test_result(f"prompt_{description.replace(' ', '_')}", True, f"Found {element}")
            else:
                self.test_result(f"prompt_{description.replace(' ', '_')}", False, f"Missing {element}")
    
    async def test_natural_queries(self):
        """Test natural language queries for Docker and Kubernetes"""
        self.log("Testing natural language queries...")
        
        natural_queries = [
            ("show my docker containers", "Docker query"),
            ("list kubernetes pods", "Kubernetes query"),
            ("what's my current directory", "Directory query"),
            ("show system resources", "System query"),
        ]
        
        for query, description in natural_queries:
            result = await self.run_awesh_command(query, timeout=20)
            output = result["stdout"]
            
            # Check if AI processed the query (not just bash)
            if "awesh_cmd:" in output or "awesh_edit:" in output:
                self.test_result(f"natural_{query.replace(' ', '_')}", True, description)
            else:
                self.test_result(f"natural_{query.replace(' ', '_')}", False, 
                               f"No AI response for {description}")
    
    async def test_security_detection(self):
        """Test security agent and rogue process detection"""
        self.log("Testing security detection...")
        
        # Test 1: Check if security agent is running
        result = await self.run_awesh_command("ps aux | grep awesh_sec | grep -v grep")
        if "awesh_sec" in result["stdout"]:
            self.test_result("security_agent_running", True, "Security agent process found")
        else:
            self.test_result("security_agent_running", False, "Security agent not running")
        
        # Test 2: Create a test rogue process
        try:
            # Create a simple test script
            test_script = Path("/tmp/test_rogue.sh")
            with open(test_script, 'w') as f:
                f.write("#!/bin/bash\nwhile true; do echo 'test rogue process'; sleep 10; done\n")
            test_script.chmod(0o755)
            
            # Start the rogue process
            rogue_proc = subprocess.Popen([str(test_script)], 
                                        stdout=subprocess.DEVNULL, 
                                        stderr=subprocess.DEVNULL)
            
            # Wait for security agent to potentially detect it
            await asyncio.sleep(15)
            
            # Check if it's detected in the prompt
            result = await self.run_awesh_command("pwd", timeout=15)
            output = result["stdout"]
            
            if "👹" in output or "rogue" in output.lower():
                self.test_result("rogue_detection", True, "Rogue process detected in prompt")
            else:
                self.test_result("rogue_detection", False, "Rogue process not detected")
            
            # Clean up
            rogue_proc.terminate()
            test_script.unlink()
            
        except Exception as e:
            self.test_result("rogue_detection", False, f"Test failed: {e}")
    
    async def test_awex_commands(self):
        """Test all aweX control commands"""
        self.log("Testing aweX control commands...")
        
        awex_commands = [
            ("awea", "AI status"),
            ("awes", "Verbose status"),
            ("awev", "Verbose level"),
            ("aweh", "Help"),
        ]
        
        for command, description in awex_commands:
            result = await self.run_awesh_command(command, timeout=15)
            
            if result["exit_code"] == 0 and result["stdout"]:
                self.test_result(f"awex_{command}", True, description)
            else:
                self.test_result(f"awex_{command}", False, 
                               f"Exit code: {result['exit_code']}")
    
    async def test_shared_memory(self):
        """Test shared memory communication"""
        self.log("Testing shared memory...")
        
        try:
            import mmap
            import tempfile
            
            # Try to read shared memory
            shm_name = f"/awesh_security_status_{os.getenv('USER', 'unknown')}"
            try:
                with open(shm_name, 'r') as f:
                    content = f.read()
                    if content and content.strip():
                        self.test_result("shared_memory_read", True, f"Content: {content[:50]}...")
                    else:
                        self.test_result("shared_memory_read", False, "Empty shared memory")
            except FileNotFoundError:
                self.test_result("shared_memory_read", False, "Shared memory not found")
        except Exception as e:
            self.test_result("shared_memory_read", False, f"Error: {e}")
    
    async def run_advanced_tests(self):
        """Run all advanced tests"""
        self.log("Starting advanced awesh tests...")
        start_time = time.time()
        
        await self.test_prompt_format()
        await self.test_awex_commands()
        await self.test_ai_responses()
        await self.test_natural_queries()
        await self.test_security_detection()
        await self.test_shared_memory()
        
        # Summary
        total = len(self.results)
        passed = len([r for r in self.results if r[1]])
        failed = total - passed
        
        duration = time.time() - start_time
        
        self.log("=" * 60)
        self.log("ADVANCED TEST SUMMARY")
        self.log("=" * 60)
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
    tester = AdvancedTester()
    success = await tester.run_advanced_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)













