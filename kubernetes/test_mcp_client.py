#!/usr/bin/env python3
"""
Test Client for Kubernetes MCP Server
Demonstrates how to interact with the MCP server
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any

class MCPTestClient:
    """Test client for the Kubernetes MCP server"""
    
    def __init__(self):
        self.process = None
        self.server_ready = False
    
    async def start_server(self):
        """Start the MCP server as a subprocess"""
        try:
            self.process = await asyncio.create_subprocess_exec(
                "python3", "kubernetes_mcp_server.py",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            print("🚀 Started Kubernetes MCP Server")
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
    
    async def test_initialization(self):
        """Test server initialization"""
        print("\n🔧 Testing server initialization...")
        
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
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
    
    async def test_list_tools(self):
        """Test listing available tools"""
        if not self.server_ready:
            print("❌ Server not ready")
            return
        
        print("\n🛠️  Testing tool listing...")
        
        list_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = await self.send_message(list_message)
        if "result" in response:
            tools = response["result"]["tools"]
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   • {tool['name']}: {tool['description']}")
        else:
            print(f"❌ Tool listing failed: {response}")
    
    async def test_get_nodes(self):
        """Test getting cluster nodes"""
        if not self.server_ready:
            print("❌ Server not ready")
            return
        
        print("\n🖥️  Testing get_nodes tool...")
        
        call_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_nodes",
                "arguments": {}
            }
        }
        
        response = await self.send_message(call_message)
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            nodes_data = json.loads(content)
            print(f"✅ Retrieved {len(nodes_data['nodes'])} nodes:")
            for node in nodes_data["nodes"]:
                status_icon = "🟢" if node["ready"] else "🔴"
                print(f"   {status_icon} {node['name']} - CPU: {node['cpu']}, Memory: {node['memory']}")
        else:
            print(f"❌ Get nodes failed: {response}")
    
    async def test_get_namespaces(self):
        """Test getting namespaces"""
        if not self.server_ready:
            print("❌ Server not ready")
            return
        
        print("\n📁 Testing get_namespaces tool...")
        
        call_message = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_namespaces",
                "arguments": {}
            }
        }
        
        response = await self.send_message(call_message)
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            namespaces_data = json.loads(content)
            print(f"✅ Retrieved {len(namespaces_data['namespaces'])} namespaces:")
            for ns in namespaces_data["namespaces"]:
                status_icon = "🟢" if ns["status"] == "Active" else "🔴"
                print(f"   {status_icon} {ns['name']} - {ns['status']}")
        else:
            print(f"❌ Get namespaces failed: {response}")
    
    async def run_tests(self):
        """Run all tests"""
        print("🧪 Starting MCP Server Tests")
        print("=" * 40)
        
        # Start server
        if not await self.start_server():
            return
        
        try:
            # Wait a moment for server to start
            await asyncio.sleep(1)
            
            # Run tests
            await self.test_initialization()
            await self.test_list_tools()
            await self.test_get_nodes()
            await self.test_get_namespaces()
            
            print("\n✨ All tests completed!")
            
        except Exception as e:
            print(f"❌ Test error: {e}")
        
        finally:
            # Cleanup
            if self.process:
                self.process.terminate()
                await self.process.wait()
                print("🛑 Server stopped")

async def main():
    """Main entry point"""
    client = MCPTestClient()
    await client.run_tests()

if __name__ == "__main__":
    asyncio.run(main())
