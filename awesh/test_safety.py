#!/usr/bin/env python3
"""
Test script for awesh command safety system
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from command_safety import CommandSafetyFilter


def test_command_safety():
    """Test the command safety filter"""
    safety_filter = CommandSafetyFilter()
    
    # Test cases: (command, should_be_safe, should_require_confirmation)
    test_cases = [
        # Safe commands
        ("ls -la", True, False),
        ("cat file.txt", True, False),
        ("grep pattern file.txt", True, False),
        ("df -h", True, False),
        
        # Dangerous commands (should be blocked)
        ("rm -rf /", False, False),
        ("rm -rf *", False, False),
        ("dd if=/dev/zero of=/dev/sda", False, False),
        ("chmod 777 /", False, False),
        ("kill -9 1", False, False),
        ("sudo su -", False, False),
        
        # Commands requiring confirmation
        ("rm file.txt", True, True),
        ("chmod 755 script.sh", True, True),
        ("sudo apt-get install package", True, True),
        ("kill 1234", True, True),
        ("systemctl stop nginx", True, True),
    ]
    
    print("Testing Command Safety Filter")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for command, expected_safe, expected_confirmation in test_cases:
        is_safe, unsafe_reason = safety_filter.is_command_safe(command)
        needs_confirmation, confirm_reason = safety_filter.requires_confirmation(command)
        
        # Check safety
        if is_safe == expected_safe:
            safety_result = "✅ PASS"
            passed += 1
        else:
            safety_result = "❌ FAIL"
            failed += 1
        
        # Check confirmation requirement
        if needs_confirmation == expected_confirmation:
            confirm_result = "✅ PASS"
            passed += 1
        else:
            confirm_result = "❌ FAIL"
            failed += 1
        
        print(f"\nCommand: {command}")
        print(f"  Safety: {safety_result} (Expected: {'Safe' if expected_safe else 'Unsafe'}, Got: {'Safe' if is_safe else 'Unsafe'})")
        if not is_safe:
            print(f"    Reason: {unsafe_reason}")
        print(f"  Confirmation: {confirm_result} (Expected: {'Yes' if expected_confirmation else 'No'}, Got: {'Yes' if needs_confirmation else 'No'})")
        if needs_confirmation:
            print(f"    Reason: {confirm_reason}")
    
    print(f"\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def test_ai_response_sanitization():
    """Test AI response sanitization"""
    safety_filter = CommandSafetyFilter()
    
    print("\nTesting AI Response Sanitization")
    print("=" * 50)
    
    # Test AI response with dangerous command
    dangerous_response = """Here's how to clean up your system:

awesh: rm -rf /tmp/*
awesh: rm -rf /

This will remove all temporary files and clean your system."""
    
    sanitized = safety_filter.sanitize_ai_response(dangerous_response)
    print("Original response:")
    print(dangerous_response)
    print("\nSanitized response:")
    print(sanitized)
    
    # Check that dangerous command was blocked
    if "BLOCKED" in sanitized and "rm -rf /" in sanitized:
        print("\n✅ Dangerous command successfully blocked")
        return True
    else:
        print("\n❌ Dangerous command was not blocked")
        return False


def test_safe_alternatives():
    """Test safe alternative suggestions"""
    safety_filter = CommandSafetyFilter()
    
    print("\nTesting Safe Alternatives")
    print("=" * 50)
    
    dangerous_commands = [
        "rm -rf file.txt",
        "chmod 777 script.sh", 
        "kill -9 1234",
        "dd if=/dev/zero of=file.bin"
    ]
    
    for cmd in dangerous_commands:
        alternative = safety_filter.get_safe_alternative(cmd)
        print(f"Dangerous: {cmd}")
        print(f"Safe alternative: {alternative or 'None suggested'}")
        print()


if __name__ == "__main__":
    print("🔒 Awesh Command Safety Test Suite")
    print("=" * 60)
    
    # Run all tests
    safety_test_passed = test_command_safety()
    sanitization_test_passed = test_ai_response_sanitization()
    
    # Show safe alternatives
    test_safe_alternatives()
    
    # Final result
    print("=" * 60)
    if safety_test_passed and sanitization_test_passed:
        print("🎉 All tests passed! Safety system is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the safety system.")
        sys.exit(1)
