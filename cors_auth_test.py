#!/usr/bin/env python3
import requests
import json
import uuid
import time
import os
from dotenv import load_dotenv
import sys

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
    """Test CORS preflight request for registration endpoint"""
    # Simulate a preflight OPTIONS request
    headers = {
        "Origin": "https://78dafde3-ec0f-4084-a604-f914c677c993.preview.emergentagent.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, Authorization"
    }
    
    response = requests.options(f"{API_URL}/auth/register", headers=headers)
    
    # Check status code
    if response.status_code != 200:
        print(f"Error: CORS preflight for registration returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check CORS headers
    cors_headers = [
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers"
    ]
    
    for header in cors_headers:
        if header not in response.headers:
            print(f"Error: CORS preflight response missing header '{header}'")
            return False
    
    # Check allowed methods
    allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
    if "POST" not in allowed_methods or "OPTIONS" not in allowed_methods:
        print(f"Error: CORS preflight response should allow POST and OPTIONS methods, got: {allowed_methods}")
        return False
    
    # Check allowed headers
    allowed_headers = response.headers.get("Access-Control-Allow-Headers", "")
    required_headers = ["Content-Type", "Authorization"]
    for header in required_headers:
        if header.lower() not in allowed_headers.lower():
            print(f"Error: CORS preflight response should allow '{header}' header, got: {allowed_headers}")
            return False
    
    print(f"CORS preflight for registration endpoint passed with headers: {dict(response.headers)}")
    return True

def test_cors_preflight_login():
    """Test CORS preflight request for login endpoint"""
    # Simulate a preflight OPTIONS request
    headers = {
        "Origin": "https://78dafde3-ec0f-4084-a604-f914c677c993.preview.emergentagent.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, Authorization"
    }
    
    response = requests.options(f"{API_URL}/auth/login", headers=headers)
    
    # Check status code
    if response.status_code != 200:
        print(f"Error: CORS preflight for login returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check CORS headers
    cors_headers = [
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers"
    ]
    
    for header in cors_headers:
        if header not in response.headers:
            print(f"Error: CORS preflight response missing header '{header}'")
            return False
    
    # Check allowed methods
    allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
    if "POST" not in allowed_methods or "OPTIONS" not in allowed_methods:
        print(f"Error: CORS preflight response should allow POST and OPTIONS methods, got: {allowed_methods}")
        return False
    
    # Check allowed headers
    allowed_headers = response.headers.get("Access-Control-Allow-Headers", "")
    required_headers = ["Content-Type", "Authorization"]
    for header in required_headers:
        if header.lower() not in allowed_headers.lower():
            print(f"Error: CORS preflight response should allow '{header}' header, got: {allowed_headers}")
            return False
    
    print(f"CORS preflight for login endpoint passed with headers: {dict(response.headers)}")
    return True

def test_user_registration():
    """Test user registration flow"""
    # Generate a unique email for testing
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "TestPassword123!"
    
    # Register the user
    register_data = {
        "email": test_email,
        "password": test_password
    }
    
    # Add origin header to simulate browser request
    headers = {
        "Origin": "https://78dafde3-ec0f-4084-a604-f914c677c993.preview.emergentagent.com",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data, headers=headers)
    
    # Check status code
    if response.status_code != 200:
        print(f"Error: Registration returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check response data
    data = response.json()
    required_fields = ["message", "access_token", "user"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Registration response missing required field '{field}'")
            return False
    
    # Check CORS headers in response
    if "Access-Control-Allow-Origin" not in response.headers:
        print(f"Error: Registration response missing CORS header 'Access-Control-Allow-Origin'")
        return False
    
    print(f"User registration successful for email: {test_email}")
    return True

def test_user_login():
    """Test user login flow"""
    # First register a user
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "TestPassword123!"
    
    # Register the user
    register_data = {
        "email": test_email,
        "password": test_password
    }
    
    register_response = requests.post(f"{API_URL}/auth/register", json=register_data)
    if register_response.status_code != 200:
        print(f"Error: Failed to register test user: {register_response.status_code} - {register_response.text}")
        return False
    
    # Now try to login
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    # Add origin header to simulate browser request
    headers = {
        "Origin": "https://78dafde3-ec0f-4084-a604-f914c677c993.preview.emergentagent.com",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{API_URL}/auth/login", json=login_data, headers=headers)
    
    # Check status code
    if response.status_code != 200:
        print(f"Error: Login returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check response data
    data = response.json()
    required_fields = ["message", "access_token", "user"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Login response missing required field '{field}'")
            return False
    
    # Check CORS headers in response
    if "Access-Control-Allow-Origin" not in response.headers:
        print(f"Error: Login response missing CORS header 'Access-Control-Allow-Origin'")
        return False
    
    print(f"User login successful for email: {test_email}")
    return True

def run_all_tests():
    """Run all CORS authentication tests"""
    tests = [
        ("CORS Preflight for Registration", test_cors_preflight_register),
        ("CORS Preflight for Login", test_cors_preflight_login),
        ("User Registration", test_user_registration),
        ("User Login", test_user_login)
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
