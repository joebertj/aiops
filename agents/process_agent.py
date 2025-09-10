#!/usr/bin/env python3
"""
Process Agent for awesh security monitoring.
Monitors running processes and detects suspicious activity.
"""

import os
import sys
import time
import subprocess
from typing import Dict, List, Optional
from dataclasses import dataclass

# Add awesh directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'awesh'))

try:
    from process_monitor import ProcessMonitor, ProcessThreat
    HAVE_PROCESS_MONITOR = True
except ImportError:
    HAVE_PROCESS_MONITOR = False
    print("⚠️ ProcessMonitor not available")

from .base_agent import BaseAgent, AgentResult


@dataclass
class ProcessAlert:
    """Process security alert"""
    threat_level: str  # "low", "medium", "high", "critical"
    process_name: str
    suspicious_activity: str
    timestamp: float
    details: Dict


class ProcessAgent(BaseAgent):
    """Agent that monitors processes and detects suspicious activity"""
    
    def __init__(self):
        super().__init__(
            name="ProcessAgent",
            priority=2,  # High priority for security
            description="Monitors processes and detects suspicious activity"
        )
        self.process_monitor = None
        self.last_scan_time = 0
        self.scan_interval = 5  # Scan every 5 seconds
        self.active_threats = []
        
        if HAVE_PROCESS_MONITOR:
            try:
                self.process_monitor = ProcessMonitor()
                print(f"🔍 ProcessAgent initialized with ProcessMonitor")
            except Exception as e:
                print(f"⚠️ Failed to initialize ProcessMonitor: {e}")
                self.process_monitor = None
    
    def should_handle(self, prompt: str, context: Dict) -> bool:
        """Process agent always runs in background, but also handles process-related queries"""
        # Always run background monitoring
        self._background_monitoring()
        
        # Handle process-related queries
        process_keywords = [
            "process", "ps", "top", "htop", "monitor", "suspicious", 
            "threat", "security", "malware", "virus", "rogue"
        ]
        
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in process_keywords)
    
    async def process(self, prompt: str, context: Dict) -> AgentResult:
        """Process the prompt and return result"""
        if not self.process_monitor:
            return AgentResult(
                handled=False,
                response="Process monitoring not available"
            )
        
        # Handle process-related queries
        if "list processes" in prompt.lower() or "show processes" in prompt.lower():
            return await self._list_processes()
        elif "suspicious" in prompt.lower() or "threat" in prompt.lower():
            return await self._show_threats()
        elif "scan" in prompt.lower():
            return await self._scan_processes()
        else:
            # Just return current threat status
            return await self._get_threat_status()
    
    def _background_monitoring(self):
        """Background process monitoring"""
        if not self.process_monitor:
            return
        
        current_time = time.time()
        if current_time - self.last_scan_time < self.scan_interval:
            return
        
        try:
            # Scan for threats
            threats = self.process_monitor.scan_for_suspicious_processes()
            
            # Update active threats
            self.active_threats = threats
            
            # Get status for prompt and write to shared memory
            status = self.get_prompt_status()
            if status:
                self.write_status_to_memory(status)
            else:
                self.write_status_to_memory("✅ No threats detected")
            
            # Log new threats
            for threat in threats:
                if threat.threat_level in ["high", "critical"]:
                    print(f"🚨 HIGH THREAT DETECTED: {threat.process.name} - {threat.description}")
            
            self.last_scan_time = current_time
            
        except Exception as e:
            print(f"⚠️ Process monitoring error: {e}")
            # Write error status
            self.write_status_to_memory("🔍 Process monitoring error")
    
    async def _list_processes(self) -> AgentResult:
        """List current processes"""
        try:
            processes = self.process_monitor.get_current_processes()
            
            response = "🔍 **Current Processes:**\n\n"
            for proc in processes[:10]:  # Show top 10
                status_emoji = "🟢" if proc.suspicious_score < 0.3 else "🟡" if proc.suspicious_score < 0.7 else "🔴"
                response += f"{status_emoji} {proc.name} (PID: {proc.pid}) - {proc.cmdline[:50]}...\n"
            
            return AgentResult(
                handled=True,
                response=response,
                metadata={"process_count": len(processes)}
            )
        except Exception as e:
            return AgentResult(
                handled=True,
                response=f"❌ Error listing processes: {e}"
            )
    
    async def _show_threats(self) -> AgentResult:
        """Show current threats"""
        if not self.active_threats:
            return AgentResult(
                handled=True,
                response="✅ No active threats detected"
            )
        
        response = "🚨 **Active Threats:**\n\n"
        for threat in self.active_threats:
            threat_emoji = {
                "low": "🟡",
                "medium": "🟠", 
                "high": "🔴",
                "critical": "🚨"
            }.get(threat.threat_level, "❓")
            
            response += f"{threat_emoji} **{threat.threat_level.upper()}**: {threat.process_name}\n"
            response += f"   {threat.description}\n"
            response += f"   PID: {threat.pid}, User: {threat.user}\n\n"
        
        return AgentResult(
            handled=True,
            response=response,
            metadata={"threat_count": len(self.active_threats)}
        )
    
    async def _scan_processes(self) -> AgentResult:
        """Perform a fresh scan"""
        try:
            threats = self.process_monitor.scan_for_threats()
            self.active_threats = threats
            
            if not threats:
                return AgentResult(
                    handled=True,
                    response="✅ Process scan completed - no threats detected"
                )
            
            response = f"🔍 **Process Scan Results:**\n\n"
            response += f"Found {len(threats)} potential threats:\n\n"
            
            for threat in threats:
                threat_emoji = {
                    "low": "🟡",
                    "medium": "🟠",
                    "high": "🔴", 
                    "critical": "🚨"
                }.get(threat.threat_level, "❓")
                
                response += f"{threat_emoji} {threat.threat_level.upper()}: {threat.process_name}\n"
            
            return AgentResult(
                handled=True,
                response=response,
                metadata={"threat_count": len(threats)}
            )
        except Exception as e:
            return AgentResult(
                handled=True,
                response=f"❌ Error scanning processes: {e}"
            )
    
    async def _get_threat_status(self) -> AgentResult:
        """Get current threat status for prompt display"""
        if not self.active_threats:
            return AgentResult(handled=False)
        
        # Find highest threat level
        threat_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        max_threat = max(self.active_threats, key=lambda t: threat_levels.get(t.threat_level, 0))
        
        threat_emoji = {
            "low": "🟡",
            "medium": "🟠",
            "high": "🔴",
            "critical": "🚨"
        }.get(max_threat.threat_level, "❓")
        
        threat_text = f"{threat_emoji}{max_threat.threat_level.upper()}:{max_threat.process_name}"
        
        return AgentResult(
            handled=True,
            response=threat_text,
            metadata={
                "threat_level": max_threat.threat_level,
                "threat_count": len(self.active_threats),
                "display_in_prompt": True
            }
        )
    
    def get_prompt_status(self) -> Optional[str]:
        """Get status for display in prompt line 1"""
        if not self.active_threats:
            return None
        
        # Find highest threat level
        threat_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        max_threat = max(self.active_threats, key=lambda t: threat_levels.get(t.threat_level, 0))
        
        threat_emoji = {
            "low": "🟡",
            "medium": "🟠", 
            "high": "🔴",
            "critical": "🚨"
        }.get(max_threat.threat_level, "❓")
        
        return f"{threat_emoji}{max_threat.threat_level.upper()}:{max_threat.process_name}"
    
    def write_status_to_memory(self, status: str):
        """Write status to shared memory for frontend to read"""
        try:
            import mmap
            import os
            
            # Open shared memory object
            shm_fd = os.open("/dev/shm/awesh_process_status", os.O_CREAT | os.O_RDWR)
            if shm_fd == -1:
                return
            
            # Set size
            os.ftruncate(shm_fd, 256)
            
            # Map shared memory
            with mmap.mmap(shm_fd, 256) as mm:
                # Write status to shared memory
                mm.write(status.encode('utf-8'))
                mm.write(b'\x00')  # Null terminate
                
        except Exception as e:
            print(f"⚠️ ProcessAgent: Failed to write to shared memory: {e}")
