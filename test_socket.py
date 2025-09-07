#!/usr/bin/env python3
"""
Simple test to check if socket communication works
"""
import socket
import os

SOCKET_PATH = os.path.expanduser("~/.awesh.sock")

try:
    # Remove existing socket
    os.unlink(SOCKET_PATH)
except OSError:
    pass

# Create socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.bind(SOCKET_PATH)
sock.listen(1)

print(f"Test server listening on {SOCKET_PATH}")

while True:
    client, addr = sock.accept()
    print("Client connected")
    
    try:
        while True:
            data = client.recv(1024)
            if not data:
                break
            
            command = data.decode('utf-8').strip()
            print(f"Received: '{command}'")
            
            if command == "STATUS":
                response = "AI_LOADING"
            else:
                response = f"Echo: {command}\n"
            
            print(f"Sending: '{response}'")
            client.send(response.encode('utf-8'))
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
        print("Client disconnected")
