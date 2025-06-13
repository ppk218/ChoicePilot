#!/usr/bin/env python3
import requests
import json
import uuid
import time
import os
from dotenv import load_dotenv
import sys
import re

# Load environment variables from frontend/.env
load_dotenv("frontend/.env")

# Get backend URL from environment
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure URL ends with /api for all requests
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

def run_test(test_name, test_func):
    """Run a test and track results"""
    test_results["total"] += 1
    print(f"\n{'='*80}\nRunning test: {test_name}\n{'='*80}")
    
    try:
        result = test_func()
        if result:
            test_results["passed"] += 1
            test_results["tests"].append({"name": test_name, "status": "PASSED"})
            print(f"✅ Test PASSED: {test_name}")
            return True
        else:
            test_results["failed"] += 1
            test_results["tests"].append({"name": test_name, "status": "FAILED"})
            print(f"❌ Test FAILED: {test_name}")
            return False
    except Exception as e:
        test_results["failed"] += 1
        test_results["tests"].append({"name": test_name, "status": "ERROR", "error": str(e)})
        print(f"❌ Test ERROR: {test_name} - {str(e)}")
        return False

def test_cors_preflight_register():
    """Test CORS preflight request to /api/auth/register"""
    headers = {
        "Origin": BACKEND_URL,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization"
    }
    
    response = requests.options(f"{API_URL}/auth/register", headers=headers)
    
    if response.status_code != 200:
        print(f"Error: CORS preflight request returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check CORS headers
    required_headers = [
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers"
    ]
    
    for header in required_headers:
        if header not in response.headers:
            print(f"Error: CORS preflight response missing required header '{header}'")
            return False
    
    # Check that POST is in allowed methods
    allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
    if "POST" not in allowed_methods:
        print(f"Error: POST method not allowed in CORS preflight response: {allowed_methods}")
        return False
    
    # Check that required headers are allowed
    allowed_headers = response.headers.get("Access-Control-Allow-Headers", "")
    if "content-type" not in allowed_headers.lower() or "authorization" not in allowed_headers.lower():
        print(f"Error: Required headers not allowed in CORS preflight response: {allowed_headers}")
        return False
    
    print(f"CORS preflight request successful with headers: {response.headers}")
    return True

def test_register_valid_user():
    """Test registration with valid email and strong password"""
    # Generate a unique email to avoid conflicts
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "StrongP@ssw0rd123"
    
    register_data = {
        "email": test_email,
        "password": test_password
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    if response.status_code != 200:
        print(f"Error: Registration failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["message", "access_token", "user"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Registration response missing required field '{field}'")
            return False
    
    user_data = data["user"]
    user_required_fields = ["id", "email", "plan", "credits", "email_verified"]
    for field in user_required_fields:
        if field not in user_data:
            print(f"Error: User data missing required field '{field}'")
            return False
    
    if user_data["email"] != test_email:
        print(f"Error: Returned email '{user_data['email']}' doesn't match registered email '{test_email}'")
        return False
    
    print(f"Registration successful for email: {test_email}")
    print(f"Response: {data}")
    return True

def test_register_weak_password():
    """Test registration with weak password"""
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "weak"  # Too short
    
    register_data = {
        "email": test_email,
        "password": test_password
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    # Should return 400 Bad Request for weak password
    if response.status_code != 400:
        print(f"Error: Registration with weak password should return 400 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "detail" not in data:
        print(f"Error: Error response missing 'detail' field: {data}")
        return False
    
    error_message = data["detail"]
    if "password" not in error_message.lower() or "8" not in error_message:
        print(f"Error: Error message doesn't mention password length requirement: {error_message}")
        return False
    
    print(f"Registration correctly rejected weak password with error: {error_message}")
    return True

def test_register_duplicate_email():
    """Test registration with duplicate email"""
    # First register a user
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "StrongP@ssw0rd123"
    
    register_data = {
        "email": test_email,
        "password": test_password
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    if response.status_code != 200:
        print(f"Error: Initial registration failed: {response.status_code} - {response.text}")
        return False
    
    # Try to register again with the same email
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    # Should return 400 Bad Request for duplicate email
    if response.status_code != 400:
        print(f"Error: Registration with duplicate email should return 400 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "detail" not in data:
        print(f"Error: Error response missing 'detail' field: {data}")
        return False
    
    error_message = data["detail"]
    if "email" not in error_message.lower() or "registered" not in error_message.lower():
        print(f"Error: Error message doesn't mention email already registered: {error_message}")
        return False
    
    print(f"Registration correctly rejected duplicate email with error: {error_message}")
    return True

def test_register_invalid_email():
    """Test registration with invalid email format"""
    test_email = "invalid-email"  # Not a valid email format
    test_password = "StrongP@ssw0rd123"
    
    register_data = {
        "email": test_email,
        "password": test_password
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    # Should return 422 Unprocessable Entity for invalid email format
    if response.status_code != 422:
        print(f"Error: Registration with invalid email should return 422 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "detail" not in data:
        print(f"Error: Error response missing 'detail' field: {data}")
        return False
    
    # Check that the error message mentions email validation
    error_details = data["detail"]
    email_error = False
    for error in error_details:
        if "email" in error.get("loc", []) and "valid email" in error.get("msg", "").lower():
            email_error = True
            break
    
    if not email_error:
        print(f"Error: Error message doesn't mention email validation: {error_details}")
        return False
    
    print(f"Registration correctly rejected invalid email format")
    return True

def test_password_validation():
    """Test enhanced password validation"""
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    
    # Test various password strengths
    password_tests = [
        {"password": "short", "should_pass": False, "reason": "too short"},
        {"password": "password123", "should_pass": True, "reason": "meets minimum length"},
        {"password": "PASSWORD123", "should_pass": True, "reason": "meets minimum length"},
        {"password": "Password123!", "should_pass": True, "reason": "strong password"},
        {"password": "abcdefghijklm", "should_pass": True, "reason": "meets minimum length"}
    ]
    
    all_passed = True
    for test_case in password_tests:
        register_data = {
            "email": test_email,
            "password": test_case["password"]
        }
        
        response = requests.post(f"{API_URL}/auth/register", json=register_data)
        
        expected_status = 200 if test_case["should_pass"] else 400
        if response.status_code != expected_status:
            print(f"Error: Password '{test_case['password']}' ({test_case['reason']}) should {'pass' if test_case['should_pass'] else 'fail'} but got status code {response.status_code}")
            print(f"Response: {response.text}")
            all_passed = False
        else:
            print(f"Password test passed: '{test_case['password']}' ({test_case['reason']}) correctly {'accepted' if test_case['should_pass'] else 'rejected'}")
    
    return all_passed

def run_all_tests():
    """Run all authentication registration tests"""
    tests = [
        ("CORS Preflight Request", test_cors_preflight_register),
        ("Register Valid User", test_register_valid_user),
        ("Register Weak Password", test_register_weak_password),
        ("Register Duplicate Email", test_register_duplicate_email),
        ("Register Invalid Email", test_register_invalid_email),
        ("Password Validation", test_password_validation)
    ]
    
    for test_name, test_func in tests:
        run_test(test_name, test_func)
    
    # Print summary
    print(f"\n{'='*80}\nTest Summary\n{'='*80}")
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    print(f"Success rate: {(test_results['passed'] / test_results['total']) * 100:.1f}%")
    
    # Print individual test results
    print("\nDetailed Results:")
    for test in test_results["tests"]:
        status = "✅" if test["status"] == "PASSED" else "❌"
        print(f"{status} {test['name']}: {test['status']}")
        if test.get("error"):
            print(f"   Error: {test['error']}")
    
    return test_results["failed"] == 0

if __name__ == "__main__":
    run_all_tests()