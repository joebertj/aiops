#!/usr/bin/env python3
"""
Test script for sensitive data filtering
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sensitive_data_filter import SensitiveDataFilter


def test_sensitive_data_detection():
    """Test detection of various sensitive data patterns"""
    filter_obj = SensitiveDataFilter()
    
    print("Testing Sensitive Data Detection")
    print("=" * 50)
    
    test_cases = [
        # API Keys
        ("export API_KEY=sk-1234567890abcdef1234567890abcdef", True, "API key"),
        ("apikey=ghp_1234567890abcdef1234567890abcdef123456", True, "GitHub Personal Access Token"),
        ("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature", True, "Bearer token"),
        
        # AWS Keys
        ("AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF", True, "AWS Access Key ID"),
        ("aws_secret_access_key=abcdef1234567890abcdef1234567890abcdef12", True, "AWS Secret Access Key pattern"),
        
        # Passwords
        ("password=mySecretPassword123", True, "Password"),
        ("DB_PASSWORD=supersecret", True, "Database password"),
        ("mysql_password=dbpass123", True, "Database password"),
        
        # Private Keys
        ("-----BEGIN RSA PRIVATE KEY-----", True, "Private key"),
        ("-----BEGIN OPENSSH PRIVATE KEY-----", True, "SSH private key"),
        
        # JWT Tokens
        ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c", True, "JWT token"),
        
        # Safe content
        ("This is just regular text", False, None),
        ("ls -la /home/user", False, None),
        ("echo 'Hello World'", False, None),
    ]
    
    passed = 0
    failed = 0
    
    for text, expected_sensitive, expected_type in test_cases:
        contains_sensitive, detected_types = filter_obj.contains_sensitive_data(text)
        
        if contains_sensitive == expected_sensitive:
            result = "✅ PASS"
            passed += 1
        else:
            result = "❌ FAIL"
            failed += 1
        
        print(f"\nText: {text[:50]}{'...' if len(text) > 50 else ''}")
        print(f"Result: {result} (Expected: {'Sensitive' if expected_sensitive else 'Safe'}, Got: {'Sensitive' if contains_sensitive else 'Safe'})")
        if detected_types:
            print(f"Detected: {', '.join(detected_types)}")
    
    print(f"\n" + "=" * 50)
    print(f"Detection Results: {passed} passed, {failed} failed")
    return failed == 0


def test_sensitive_file_detection():
    """Test detection of sensitive files"""
    filter_obj = SensitiveDataFilter()
    
    print("\nTesting Sensitive File Detection")
    print("=" * 50)
    
    test_files = [
        # Sensitive files
        ("/home/user/.ssh/id_rsa", True, "Sensitive file name"),
        ("/home/user/.env", True, "Sensitive file name"),
        ("config/secrets.json", True, "Sensitive file name"),
        ("certs/server.key", True, "Sensitive file extension"),
        ("/home/user/.aws/credentials", True, "File in sensitive directory"),
        
        # Safe files
        ("/home/user/document.txt", False, None),
        ("/var/log/app.log", False, None),
        ("src/main.py", False, None),
    ]
    
    passed = 0
    failed = 0
    
    for file_path, expected_sensitive, expected_reason_type in test_files:
        is_sensitive, reason = filter_obj.is_sensitive_file(file_path)
        
        if is_sensitive == expected_sensitive:
            result = "✅ PASS"
            passed += 1
        else:
            result = "❌ FAIL"
            failed += 1
        
        print(f"\nFile: {file_path}")
        print(f"Result: {result} (Expected: {'Sensitive' if expected_sensitive else 'Safe'}, Got: {'Sensitive' if is_sensitive else 'Safe'})")
        if reason:
            print(f"Reason: {reason}")
    
    print(f"\n" + "=" * 50)
    print(f"File Detection Results: {passed} passed, {failed} failed")
    return failed == 0


def test_data_filtering():
    """Test filtering of sensitive data"""
    filter_obj = SensitiveDataFilter()
    
    print("\nTesting Data Filtering")
    print("=" * 50)
    
    test_text = """
Configuration:
API_KEY=sk-1234567890abcdef1234567890abcdef
password=mySecretPassword123
database_url=postgresql://user:pass@localhost/db
token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature

Regular content that should not be filtered.
"""
    
    print("Original text:")
    print(test_text)
    
    filtered_text = filter_obj.filter_sensitive_data(test_text)
    
    print("\nFiltered text:")
    print(filtered_text)
    
    # Check that sensitive data was redacted
    if "sk-1234567890abcdef1234567890abcdef" not in filtered_text:
        print("✅ API key successfully redacted")
    else:
        print("❌ API key was not redacted")
        return False
    
    if "mySecretPassword123" not in filtered_text:
        print("✅ Password successfully redacted")
    else:
        print("❌ Password was not redacted")
        return False
    
    if "Regular content" in filtered_text:
        print("✅ Non-sensitive content preserved")
    else:
        print("❌ Non-sensitive content was removed")
        return False
    
    return True


def test_command_output_filtering():
    """Test filtering of command outputs"""
    filter_obj = SensitiveDataFilter()
    
    print("\nTesting Command Output Filtering")
    print("=" * 50)
    
    # Test env command output
    env_output = """
HOME=/home/user
API_KEY=sk-1234567890abcdef1234567890abcdef
PATH=/usr/bin:/bin
SECRET_TOKEN=abc123def456
USER=testuser
"""
    
    filtered_output = filter_obj.filter_command_output("env", env_output)
    
    print("Original env output:")
    print(env_output)
    print("\nFiltered env output:")
    print(filtered_output)
    
    # Check filtering
    if "sk-1234567890abcdef1234567890abcdef" not in filtered_output:
        print("✅ API key filtered from env output")
        env_test_passed = True
    else:
        print("❌ API key not filtered from env output")
        env_test_passed = False
    
    # Test cat of sensitive file
    sensitive_file_output = filter_obj.filter_command_output("cat .env", "API_KEY=secret123")
    
    if "[REDACTED:" in sensitive_file_output:
        print("✅ Sensitive file output blocked")
        file_test_passed = True
    else:
        print("❌ Sensitive file output not blocked")
        file_test_passed = False
    
    return env_test_passed and file_test_passed


def test_ai_blocking():
    """Test blocking of high-risk content from AI"""
    filter_obj = SensitiveDataFilter()
    
    print("\nTesting AI Content Blocking")
    print("=" * 50)
    
    test_cases = [
        # Should be blocked
        ("Here's my private key: -----BEGIN RSA PRIVATE KEY-----", True),
        ("My password is mySecretPassword123", True),
        ("API key: sk-1234567890abcdef1234567890abcdef", True),
        
        # Should be filtered but not blocked
        ("The config has token=abc123 in it", False),
        ("Check the environment variables", False),
        ("This is regular text", False),
    ]
    
    passed = 0
    failed = 0
    
    for text, should_block in test_cases:
        should_block_result, reason = filter_obj.should_block_from_ai(text)
        
        if should_block_result == should_block:
            result = "✅ PASS"
            passed += 1
        else:
            result = "❌ FAIL"
            failed += 1
        
        print(f"\nText: {text[:50]}{'...' if len(text) > 50 else ''}")
        print(f"Result: {result} (Expected: {'Block' if should_block else 'Allow'}, Got: {'Block' if should_block_result else 'Allow'})")
        if reason:
            print(f"Reason: {reason}")
    
    print(f"\n" + "=" * 50)
    print(f"AI Blocking Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("🔒 Awesh Sensitive Data Filter Test Suite")
    print("=" * 60)
    
    # Run all tests
    detection_passed = test_sensitive_data_detection()
    file_detection_passed = test_sensitive_file_detection()
    filtering_passed = test_data_filtering()
    command_filtering_passed = test_command_output_filtering()
    ai_blocking_passed = test_ai_blocking()
    
    # Final result
    print("=" * 60)
    all_passed = all([
        detection_passed, file_detection_passed, filtering_passed,
        command_filtering_passed, ai_blocking_passed
    ])
    
    if all_passed:
        print("🎉 All sensitive data filter tests passed!")
        sys.exit(0)
    else:
        print("❌ Some sensitive data filter tests failed.")
        sys.exit(1)
