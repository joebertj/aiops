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
echo "🔄 Starting continuous monitoring loop..."

# Continuous suspicious activity loop
while true; do
    echo "🚨 ROGUE ACTIVITY: $(date) - Simulating ongoing suspicious behavior"
    
    # Simulate suspicious network activity
    echo "📡 Simulating network reconnaissance..."
    echo "🔍 Scanning for open ports on localhost..."
    
    # Simulate file system access patterns
    echo "📁 Accessing sensitive directories..."
    echo "🔐 Checking for privilege escalation vectors..."
    
    # Create temporary suspicious files
    touch /tmp/.rogue_temp_$(date +%s)
    echo "malicious_payload_simulation" > /tmp/.rogue_data_$(date +%s)
    
    # Simulate process spawning
    echo "👾 Spawning child processes..."
    
    # Simulate data exfiltration attempt
    echo "💾 Attempting data exfiltration simulation..."
    echo "🌐 Connecting to command and control server simulation..."
    
    # Clean up old temp files (keep it suspicious but not too messy)
    find /tmp -name ".rogue_*" -mmin +5 -delete 2>/dev/null
    
    # Sleep for 30 seconds before next cycle
    sleep 30
done
