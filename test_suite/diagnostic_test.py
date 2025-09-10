#!/usr/bin/env python3
"""
Diagnostic Test for Awesh
Focuses on identifying specific issues with security agent and AI
"""

import asyncio
import subprocess
import os
import time
import tempfile
from pathlib import Path

class DiagnosticTester:
    def __init__(self):
        self.awesh_binary = Path.home() / ".local" / "bin" / "awesh"
        self.awesh_sec_binary = Path.home() / ".local" / "bin" / "awesh_sec"
        self.results = []
    
    def log(self, message, status="INFO"):
        print(f"[{time.strftime('%H:%M:%S')}] {status}: {message}")
    
    def test_result(self, test_name, passed, details=""):
        emoji = "✅" if passed else "❌"
        self.log(f"{emoji} {test_name}: {'PASS' if passed else 'FAIL'}")
        if details:
            self.log(f"    {details}")
        self.results.append((test_name, passed, details))
    
    async def test_security_agent_direct(self):
        """Test security agent directly to see why it's crashing"""
        self.log("Testing security agent directly...")
        
        try:
            # Test if binary exists
            if not self.awesh_sec_binary.exists():
                self.test_result("awesh_sec_binary_exists", False, "Binary not found")
                return
            
            self.test_result("awesh_sec_binary_exists", True, f"Found at {self.awesh_sec_binary}")
            
            # Test if binary is executable
            if not os.access(self.awesh_sec_binary, os.X_OK):
                self.test_result("awesh_sec_binary_executable", False, "Not executable")
                return
            
            self.test_result("awesh_sec_binary_executable", True)
            
            # Try to run security agent directly
            try:
                result = subprocess.run(
                    [str(self.awesh_sec_binary)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                self.log(f"Security agent exit code: {result.returncode}")
                self.log(f"Security agent stdout: {result.stdout}")
                self.log(f"Security agent stderr: {result.stderr}")
                
                if result.returncode == 0:
                    self.test_result("awesh_sec_direct_run", True, "Ran successfully")
                else:
                    self.test_result("awesh_sec_direct_run", False, f"Exit code: {result.returncode}")
                    
            except subprocess.TimeoutExpired:
                self.test_result("awesh_sec_direct_run", False, "Timeout - may be hanging")
            except Exception as e:
                self.test_result("awesh_sec_direct_run", False, f"Error: {e}")
                
        except Exception as e:
            self.test_result("awesh_sec_direct_test", False, str(e))
    
    async def test_backend_connection(self):
        """Test backend connection and AI initialization"""
        self.log("Testing backend connection...")
        
        try:
            # Start backend directly
            process = await asyncio.create_subprocess_exec(
                "python3", "-m", "awesh_backend",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for READY signal
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input="STATUS\n".encode()),
                    timeout=10
                )
                
                output = stdout.decode()
                self.log(f"Backend output: {output}")
                
                if "AI_PROVIDER:" in output:
                    self.test_result("backend_ai_provider", True, "AI provider configured")
                else:
                    self.test_result("backend_ai_provider", False, "AI provider not configured")
                
                if "MODEL:" in output:
                    self.test_result("backend_model", True, "Model configured")
                else:
                    self.test_result("backend_model", False, "Model not configured")
                
                if "READY:True" in output:
                    self.test_result("backend_ready", True, "Backend ready")
                else:
                    self.test_result("backend_ready", False, "Backend not ready")
                    
            except asyncio.TimeoutError:
                self.test_result("backend_connection", False, "Backend timeout")
            
            # Clean up
            process.terminate()
            
        except Exception as e:
            self.test_result("backend_connection", False, str(e))
    
    async def test_shared_memory(self):
        """Test shared memory functionality"""
        self.log("Testing shared memory...")
        
        try:
            import mmap
            import tempfile
            
            # Test creating shared memory
            shm_name = f"/awesh_security_status_{os.getenv('USER', 'unknown')}"
            
            try:
                # Try to create shared memory
                shm_fd = os.open(shm_name, os.O_CREAT | os.O_RDWR, 0o666)
                os.ftruncate(shm_fd, 512)
                
                # Map it
                shared_mem = mmap.mmap(shm_fd, 512)
                shared_mem.write(b"Test status")
                shared_mem.seek(0)
                
                # Read it back
                content = shared_mem.read(20).decode()
                shared_mem.close()
                os.close(shm_fd)
                
                if content == "Test status":
                    self.test_result("shared_memory_basic", True, "Basic shared memory works")
                else:
                    self.test_result("shared_memory_basic", False, f"Content mismatch: {content}")
                
                # Clean up
                os.unlink(shm_name)
                
            except Exception as e:
                self.test_result("shared_memory_basic", False, f"Error: {e}")
                
        except ImportError:
            self.test_result("shared_memory_basic", False, "mmap module not available")
        except Exception as e:
            self.test_result("shared_memory_basic", False, str(e))
    
    async def test_config_loading(self):
        """Test configuration loading"""
        self.log("Testing configuration loading...")
        
        config_file = Path.home() / ".aweshrc"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                
                # Check for required settings
                if "AI_PROVIDER=openrouter" in content:
                    self.test_result("config_ai_provider", True, "OpenRouter configured")
                else:
                    self.test_result("config_ai_provider", False, "OpenRouter not configured")
                
                if "MODEL=meta-llama" in content:
                    self.test_result("config_model", True, "Llama model configured")
                else:
                    self.test_result("config_model", False, "Llama model not configured")
                
                if "OPENROUTER_API_KEY=" in content:
                    self.test_result("config_api_key", True, "API key present")
                else:
                    self.test_result("config_api_key", False, "API key missing")
                    
            except Exception as e:
                self.test_result("config_loading", False, str(e))
        else:
            self.test_result("config_loading", False, "Config file not found")
    
    async def run_diagnostic_tests(self):
        """Run all diagnostic tests"""
        self.log("Starting diagnostic tests...")
        start_time = time.time()
        
        await self.test_config_loading()
        await self.test_shared_memory()
        await self.test_backend_connection()
        await self.test_security_agent_direct()
        
        # Summary
        total = len(self.results)
        passed = len([r for r in self.results if r[1]])
        failed = total - passed
        
        duration = time.time() - start_time
        
        self.log("=" * 60)
        self.log("DIAGNOSTIC TEST SUMMARY")
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
    tester = DiagnosticTester()
    success = await tester.run_diagnostic_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
