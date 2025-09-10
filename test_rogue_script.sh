#!/bin/bash

# ROGUE SCRIPT - TESTING PROCESS AGENT DETECTION
# This script is designed to trigger security alerts but has no actual payload
# Purpose: Test if our process agent captures and displays suspicious activity

echo "🚨 ROGUE SCRIPT DETECTED - TESTING SECURITY MONITORING"
echo "This is a test script to verify process agent functionality"
echo "No actual malicious payload - just testing detection capabilities"

# Simulate suspicious behavior patterns
echo "Simulating suspicious network activity..."
echo "Simulating file system access patterns..."
echo "Simulating process spawning behavior..."

# Create a temporary file with suspicious name
touch /tmp/.hidden_suspicious_file_$(date +%s)

# Simulate network connection attempt (but don't actually connect)
echo "Attempting connection to suspicious host: evil.example.com:6666"

# Simulate privilege escalation attempt (but don't actually do it)
echo "Checking for privilege escalation opportunities..."

# Simulate data exfiltration attempt (but don't actually do it)
echo "Scanning for sensitive data files..."

# Clean up test file
rm -f /tmp/.hidden_suspicious_file_*

echo "✅ Rogue script test completed - no actual harm done"
echo "If process agent is working, this should appear in prompt line 1"
