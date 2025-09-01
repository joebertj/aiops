#!/usr/bin/env python3
"""
Interactive Client for Smart Kubernetes MCP Server
Test natural language prompts and see Kubernetes API calls in action
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any

class InteractiveMCPClient:
    """Interactive client for testing natural language prompts"""
    
    def __init__(self):
        self.process = None
        self.server_ready = False
    
    async def start_server(self):
        """Start the MCP server as a subprocess"""
        try:
            self.process = await asyncio.create_subprocess_exec(
                "python3", "smart_k8s_mcp.py",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            print("🚀 Started Smart Kubernetes MCP Server")
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to the MCP server and get response"""
        if not self.process:
            raise Exception("Server not started")
        
        try:
            # Send message
            message_line = json.dumps(message) + "\n"
            self.process.stdin.write(message_line.encode())
            await self.process.stdin.drain()
            
            # Read response
            response_line = await self.process.stdout.readline()
            if response_line:
                return json.loads(response_line.decode().strip())
            else:
                return {"error": "No response from server"}
                
        except Exception as e:
            print(f"❌ Error communicating with server: {e}")
            return {"error": str(e)}
    
    async def initialize_server(self):
        """Initialize the MCP server"""
        print("🔧 Initializing server...")
        
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "interactive-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self.send_message(init_message)
        if "result" in response:
            print("✅ Server initialized successfully")
            print(f"   Server: {response['result']['serverInfo']['name']} v{response['result']['serverInfo']['version']}")
            self.server_ready = True
        else:
            print(f"❌ Initialization failed: {response}")
    
    async def process_prompt(self, prompt: str):
        """Process a natural language prompt"""
        if not self.server_ready:
            print("❌ Server not ready")
            return
        
        print(f"\n🤖 Processing: {prompt}")
        print("-" * 50)
        
        # Send prompt
        prompt_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "prompts/call",
            "params": {
                "name": "cluster_health",
                "arguments": {
                    "prompt": prompt
                }
            }
        }
        
        response = await self.send_message(prompt_message)
        if "result" in response:
            content = response["result"]["content"]
            for item in content:
                if item["type"] == "text":
                    print(item["text"])
                    print()
        else:
            print(f"❌ Prompt processing failed: {response}")
    
    async def run_interactive(self):
        """Run interactive prompt loop"""
        print("🧪 Smart Kubernetes MCP Interactive Client")
        print("=" * 50)
        print("💡 Type natural language prompts to interact with your cluster")
        print("💡 Examples:")
        print("   • 'Show me the cluster health'")
        print("   • 'What nodes do I have?'")
        print("   • 'Get pods in default namespace'")
        print("   • 'Show me the services'")
        print("   • 'Check cluster status'")
        print("💡 Type 'quit' to exit")
        print()
        
        # Start server
        if not await self.start_server():
            return
        
        try:
            # Wait a moment for server to start
            await asyncio.sleep(1)
            
            # Initialize server
            await self.initialize_server()
            
            if not self.server_ready:
                print("❌ Server initialization failed")
                return
            
            # Interactive loop
            while True:
                try:
                    prompt = input("🤖 Enter your prompt: ").strip()
                    
                    if prompt.lower() in ['quit', 'exit', 'q']:
                        print("👋 Goodbye!")
                        break
                    
                    if not prompt:
                        continue
                    
                    await self.process_prompt(prompt)
                    
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except EOFError:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        except Exception as e:
            print(f"❌ Interactive session error: {e}")
        
        finally:
            # Cleanup
            if self.process:
                self.process.terminate()
                await self.process.wait()
                print("🛑 Server stopped")

async def main():
    """Main entry point"""
    client = InteractiveMCPClient()
    await client.run_interactive()

if __name__ == "__main__":
    asyncio.run(main())
