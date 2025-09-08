#!/usr/bin/env python3
"""
Cross-Platform GUI Client for Smart Kubernetes MCP Server
Works on Windows, Mac, and Linux with Dynamic Prompt Handling
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import asyncio
import json
import subprocess
import threading
import queue
from typing import Dict, Any
import sys
import os
import time
from datetime import datetime

class KubernetesMCPGUI:
    """Graphical client for the Kubernetes MCP server with dynamic prompt handling"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Kubernetes MCP Client - Dynamic Prompts")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Server process
        self.server_process = None
        self.server_ready = False
        
        # Message queue for async operations
        self.message_queue = queue.Queue()
        
        # Conversation history
        self.conversation_history = []
        
        # Setup UI
        self.setup_ui()
        
        # Start message processing
        self.process_messages()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🚀 Smart Kubernetes MCP Client - Dynamic Prompts", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Server status frame
        status_frame = ttk.LabelFrame(main_frame, text="Server Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Server controls
        self.start_button = ttk.Button(status_frame, text="Start Server", 
                                      command=self.start_server)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(status_frame, text="Stop Server", 
                                     command=self.stop_server, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Server: Stopped", 
                                     foreground='red')
        self.status_label.grid(row=0, column=2, padx=(20, 0))
        
        # Prompt input frame
        prompt_frame = ttk.LabelFrame(main_frame, text="Natural Language Prompt", padding="10")
        prompt_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Prompt entry
        self.prompt_var = tk.StringVar()
        self.prompt_entry = ttk.Entry(prompt_frame, textvariable=self.prompt_var, 
                                     font=('Arial', 12), width=70)
        self.prompt_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        prompt_frame.columnconfigure(0, weight=1)
        
        # Send button
        self.send_button = ttk.Button(prompt_frame, text="Send", 
                                     command=self.send_prompt, state='disabled')
        self.send_button.grid(row=0, column=1)
        
        # Quick prompt buttons with examples
        quick_frame = ttk.Frame(prompt_frame)
        quick_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        quick_prompts = [
            "Show me the cluster health",
            "What nodes do I have?",
            "Get all pods",
            "Show me the services",
            "Deploy nginx",
            "Trace network routes of pods",
            "Show pod resource usage",
            "List all namespaces"
        ]
        
        # Create scrollable frame for quick prompts
        canvas = tk.Canvas(quick_frame, height=30)
        scrollbar = ttk.Scrollbar(quick_frame, orient="horizontal", command=canvas.xview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)
        
        for i, prompt in enumerate(quick_prompts):
            btn = ttk.Button(scrollable_frame, text=prompt, 
                            command=lambda p=prompt: self.set_prompt(p))
            btn.grid(row=0, column=i, padx=(0, 5))
        
        canvas.pack(side="left", fill="x", expand=True)
        scrollbar.pack(side="bottom", fill="x")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Conversation tab
        self.conversation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.conversation_frame, text="Conversation")
        self.setup_conversation_tab()
        
        # Response tab
        self.response_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.response_frame, text="Latest Response")
        self.setup_response_tab()
        
        # History tab
        self.history_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text="Command History")
        self.setup_history_tab()
        
        # Bind Enter key to send prompt
        self.prompt_entry.bind('<Return>', lambda e: self.send_prompt())
        
        # Focus on prompt entry
        self.prompt_entry.focus()
    
    def setup_conversation_tab(self):
        """Setup the conversation tab with chat-like interface"""
        # Conversation display
        self.conversation_text = scrolledtext.ScrolledText(self.conversation_frame, 
                                                         font=('Arial', 10),
                                                         wrap=tk.WORD, height=25)
        self.conversation_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Clear conversation button
        clear_conv_button = ttk.Button(self.conversation_frame, text="Clear Conversation", 
                                      command=self.clear_conversation)
        clear_conv_button.pack(pady=(0, 10))
    
    def setup_response_tab(self):
        """Setup the response tab for latest response only"""
        # Response text area
        self.response_text = scrolledtext.ScrolledText(self.response_frame, 
                                                     font=('Consolas', 10),
                                                     wrap=tk.WORD, height=25)
        self.response_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Clear button
        clear_button = ttk.Button(self.response_frame, text="Clear Response", 
                                 command=self.clear_response)
        clear_button.pack(pady=(0, 10))
    
    def setup_history_tab(self):
        """Setup the history tab showing all commands"""
        # History listbox
        self.history_listbox = tk.Listbox(self.history_frame, font=('Arial', 10))
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # History controls
        history_controls = ttk.Frame(self.history_frame)
        history_controls.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        clear_history_button = ttk.Button(history_controls, text="Clear History", 
                                         command=self.clear_history)
        clear_history_button.pack(side=tk.LEFT)
        
        replay_button = ttk.Button(history_controls, text="Replay Selected", 
                                  command=self.replay_command)
        replay_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Bind double-click to replay
        self.history_listbox.bind('<Double-Button-1>', lambda e: self.replay_command())
    
    def set_prompt(self, prompt: str):
        """Set a quick prompt"""
        self.prompt_var.set(prompt)
        self.prompt_entry.focus()
    
    def start_server(self):
        """Start the MCP server"""
        try:
            # Start server in a separate thread
            server_thread = threading.Thread(target=self._start_server_thread)
            server_thread.daemon = True
            server_thread.start()
            
            self.start_button.config(state='disabled')
            self.status_label.config(text="Server: Starting...", foreground='orange')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
    
    def _start_server_thread(self):
        """Start server in background thread"""
        try:
            # Start server process
            self.server_process = subprocess.Popen(
                [sys.executable, "smart_k8s_mcp.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            # Initialize server
            self._initialize_server()
            
        except Exception as e:
            self.message_queue.put(("error", f"Server start failed: {e}"))
    
    def _initialize_server(self):
        """Initialize the MCP server"""
        try:
            # Send initialization message
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "gui-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Send message
            message_line = json.dumps(init_message) + "\n"
            self.server_process.stdin.write(message_line.encode())
            self.server_process.stdin.flush()
            
            # Read response
            response_line = self.server_process.stdout.readline()
            if response_line:
                response = json.loads(response_line.decode().strip())
                if "result" in response:
                    self.message_queue.put(("success", "Server initialized successfully"))
                    self.server_ready = True
                else:
                    self.message_queue.put(("error", f"Initialization failed: {response}"))
            else:
                self.message_queue.put(("error", "No response from server"))
                
        except Exception as e:
            self.message_queue.put(("error", f"Initialization error: {e}"))
    
    def stop_server(self):
        """Stop the MCP server"""
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait()
                self.server_process = None
            
            self.server_ready = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.send_button.config(state='disabled')
            self.status_label.config(text="Server: Stopped", foreground='red')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")
    
    def send_prompt(self):
        """Send a natural language prompt"""
        if not self.server_ready:
            messagebox.showwarning("Warning", "Server not ready. Please start the server first.")
            return
        
        prompt = self.prompt_var.get().strip()
        if not prompt:
            messagebox.showwarning("Warning", "Please enter a prompt.")
            return
        
        # Add to conversation history
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.conversation_history.append({
            'timestamp': timestamp,
            'prompt': prompt,
            'response': None
        })
        
        # Update conversation display
        self.update_conversation_display()
        
        # Update history listbox
        self.update_history_display()
        
        # Clear previous response
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, f"🤖 Processing: {prompt}\n")
        self.response_text.insert(tk.END, "=" * 50 + "\n\n")
        
        # Send prompt in background thread
        prompt_thread = threading.Thread(target=self._send_prompt_thread, args=(prompt,))
        prompt_thread.daemon = True
        prompt_thread.start()
        
        # Clear prompt entry
        self.prompt_var.set("")
    
    def _send_prompt_thread(self, prompt: str):
        """Send prompt in background thread"""
        try:
            # Send prompt message
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
            
            # Send message
            message_line = json.dumps(prompt_message) + "\n"
            self.server_process.stdin.write(message_line.encode())
            self.server_process.stdin.flush()
            
            # Read response
            response_line = self.server_process.stdout.readline()
            if response_line:
                response = json.loads(response_line.decode().strip())
                if "result" in response:
                    content = response["result"]["content"]
                    response_text = ""
                    for item in content:
                        if item["type"] == "text":
                            response_text += item["text"] + "\n"
                    
                    # Update conversation history with response
                    if self.conversation_history:
                        self.conversation_history[-1]['response'] = response_text
                    
                    # Update displays
                    self.root.after(0, self.update_conversation_display)
                    self.root.after(0, self.update_history_display)
                    
                    # Show response in response tab
                    self.message_queue.put(("response", response_text))
                    
                else:
                    self.message_queue.put(("error", f"Prompt failed: {response}"))
            else:
                self.message_queue.put(("error", "No response from server"))
                
        except Exception as e:
            self.message_queue.put(("error", f"Prompt error: {e}"))
    
    def update_conversation_display(self):
        """Update the conversation display"""
        try:
            self.conversation_text.delete(1.0, tk.END)
            
            for entry in self.conversation_history:
                # Add prompt
                self.conversation_text.insert(tk.END, f"[{entry['timestamp']}] 🤖 You: {entry['prompt']}\n", "prompt")
                self.conversation_text.insert(tk.END, "\n")
                
                # Add response if available
                if entry['response']:
                    self.conversation_text.insert(tk.END, f"🤖 Assistant: {entry['response']}\n", "response")
                    self.conversation_text.insert(tk.END, "\n" + "="*50 + "\n\n")
                else:
                    self.conversation_text.insert(tk.END, "⏳ Processing...\n\n")
            
            # Scroll to bottom
            self.conversation_text.see(tk.END)
            
            # Configure tags for styling
            self.conversation_text.tag_configure("prompt", foreground="blue", font=("Arial", 10, "bold"))
            self.conversation_text.tag_configure("response", foreground="green", font=("Consolas", 9))
            
        except Exception as e:
            print(f"Error updating conversation display: {e}")
    
    def update_history_display(self):
        """Update the history listbox"""
        try:
            self.history_listbox.delete(0, tk.END)
            
            for entry in self.conversation_history:
                status = "✅" if entry['response'] else "⏳"
                display_text = f"{status} [{entry['timestamp']}] {entry['prompt'][:50]}..."
                self.history_listbox.insert(tk.END, display_text)
                
        except Exception as e:
            print(f"Error updating history display: {e}")
    
    def replay_command(self):
        """Replay a selected command from history"""
        try:
            selection = self.history_listbox.curselection()
            if selection:
                index = selection[0]
                if index < len(self.conversation_history):
                    prompt = self.conversation_history[index]['prompt']
                    self.set_prompt(prompt)
                    
        except Exception as e:
            print(f"Error replaying command: {e}")
    
    def clear_conversation(self):
        """Clear the conversation display"""
        self.conversation_text.delete(1.0, tk.END)
    
    def clear_response(self):
        """Clear the response text area"""
        self.response_text.delete(1.0, tk.END)
    
    def clear_history(self):
        """Clear the command history"""
        self.conversation_history.clear()
        self.update_conversation_display()
        self.update_history_display()
    
    def process_messages(self):
        """Process messages from the queue"""
        try:
            while True:
                message_type, message = self.message_queue.get_nowait()
                
                if message_type == "success":
                    self.status_label.config(text="Server: Running", foreground='green')
                    self.stop_button.config(state='normal')
                    self.send_button.config(state='normal')
                    self.response_text.insert(tk.END, f"✅ {message}\n\n")
                    
                elif message_type == "error":
                    self.response_text.insert(tk.END, f"❌ {message}\n\n")
                    
                elif message_type == "response":
                    self.response_text.delete(1.0, tk.END)
                    self.response_text.insert(tk.END, f"🤖 Response:\n")
                    self.response_text.insert(tk.END, "=" * 50 + "\n\n")
                    self.response_text.insert(tk.END, message + "\n")
                
                self.response_text.see(tk.END)
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_messages)
    
    def on_closing(self):
        """Handle window closing"""
        if self.server_process:
            self.stop_server()
        self.root.destroy()

def main():
    """Main entry point"""
    root = tk.Tk()
    app = KubernetesMCPGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()
