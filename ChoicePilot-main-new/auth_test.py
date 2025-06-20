#!/usr/bin/env python3
import requests
import json
import uuid
import time
import os
from dotenv import load_dotenv
import sys
import random
import string

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

def generate_random_email():
    """Generate a random email for testing"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"

def generate_random_password(length=12, include_upper=True, include_lower=True, include_digits=True, include_special=True):
    """Generate a random password with specified characteristics"""
    chars = ""
    if include_upper:
        chars += string.ascii_uppercase
    if include_lower:
        chars += string.ascii_lowercase
    if include_digits:
        chars += string.digits
    if include_special:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Ensure at least one character from each required type
    password = []
    if include_upper:
        password.append(random.choice(string.ascii_uppercase))
    if include_lower:
        password.append(random.choice(string.ascii_lowercase))
    if include_digits:
        password.append(random.choice(string.digits))
    if include_special:
        password.append(random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))
    
    # Fill the rest of the password
    remaining_length = length - len(password)
    password.extend(random.choices(chars, k=remaining_length))
    
    # Shuffle the password
    random.shuffle(password)
    
    return ''.join(password)

def test_registration_success():
    """Test successful user registration"""
    email = generate_random_email()
    password = generate_random_password()
    
    print(f"Testing registration with email: {email} and password: {password}")
    
    # Register a new user
    register_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    if response.status_code != 200:
        print(f"Error: Registration failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    
    # Check for required fields in response
    required_fields = ["message", "access_token", "user"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Registration response missing required field '{field}'")
            return False
    
    # Check user data
    user = data["user"]
    user_required_fields = ["id", "email", "plan", "credits", "email_verified"]
    for field in user_required_fields:
        if field not in user:
            print(f"Error: User data missing required field '{field}'")
            return False
    
    # Verify email_verified is True (as per the fix)
    if not user["email_verified"]:
        print(f"Error: email_verified should be True but got {user['email_verified']}")
        return False
    
    # Verify email matches
    if user["email"] != email:
        print(f"Error: Returned email '{user['email']}' doesn't match registered email '{email}'")
        return False
    
    print(f"Registration successful for {email}")
    return True

def test_registration_duplicate_email():
    """Test registration with duplicate email"""
    # First register a user
    email = generate_random_email()
    password = generate_random_password()
    
    register_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    if response.status_code != 200:
        print(f"Error: Initial registration failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Initial registration successful for {email}")
    
    # Try to register again with the same email
    duplicate_register_data = {
        "email": email,
        "password": generate_random_password()  # Different password
    }
    
    duplicate_response = requests.post(f"{API_URL}/auth/register", json=duplicate_register_data)
    
    # Should return 400 Bad Request for duplicate email
    if duplicate_response.status_code != 400:
        print(f"Error: Duplicate registration should return 400 but returned {duplicate_response.status_code}")
        print(f"Response: {duplicate_response.text}")
        return False
    
    # Check error message
    error_data = duplicate_response.json()
    if "detail" not in error_data:
        print(f"Error: Duplicate registration response missing 'detail' field: {error_data}")
        return False
    
    if "already registered" not in error_data["detail"].lower():
        print(f"Error: Duplicate registration error message should mention 'already registered' but got: {error_data['detail']}")
        return False
    
    print(f"Duplicate email registration correctly rejected with status code {duplicate_response.status_code}")
    return True

def test_registration_weak_password():
    """Test registration with weak password"""
    email = generate_random_email()
    weak_password = "weak"  # Less than 8 characters
    
    register_data = {
        "email": email,
        "password": weak_password
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    # Should return 400 Bad Request for weak password
    if response.status_code != 400:
        print(f"Error: Weak password registration should return 400 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check error message
    error_data = response.json()
    if "detail" not in error_data:
        print(f"Error: Weak password registration response missing 'detail' field: {error_data}")
        return False
    
    if "password" not in error_data["detail"].lower() or "8" not in error_data["detail"]:
        print(f"Error: Weak password error message should mention password length but got: {error_data['detail']}")
        return False
    
    print(f"Weak password registration correctly rejected with status code {response.status_code}")
    return True

def test_registration_invalid_email():
    """Test registration with invalid email format"""
    invalid_email = "not_an_email"
    password = generate_random_password()
    
    register_data = {
        "email": invalid_email,
        "password": password
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    # Should return 422 Unprocessable Entity for invalid email format
    if response.status_code != 422:
        print(f"Error: Invalid email registration should return 422 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Invalid email registration correctly rejected with status code {response.status_code}")
    return True

def test_login_success():
    """Test successful login"""
    # First register a user
    email = generate_random_email()
    password = generate_random_password()
    
    register_data = {
        "email": email,
        "password": password
    }
    
    register_response = requests.post(f"{API_URL}/auth/register", json=register_data)
    if register_response.status_code != 200:
        print(f"Error: Registration failed with status code {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return False
    
    print(f"Registration successful for {email}")
    
    # Now try to login
    login_data = {
        "email": email,
        "password": password
    }
    
    login_response = requests.post(f"{API_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"Error: Login failed with status code {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    login_data = login_response.json()
    
    # Check for required fields in response
    required_fields = ["message", "access_token", "user"]
    for field in required_fields:
        if field not in login_data:
            print(f"Error: Login response missing required field '{field}'")
            return False
    
    # Check user data
    user = login_data["user"]
    user_required_fields = ["id", "email", "plan", "credits", "email_verified"]
    for field in user_required_fields:
        if field not in user:
            print(f"Error: User data missing required field '{field}'")
            return False
    
    # Verify email matches
    if user["email"] != email:
        print(f"Error: Returned email '{user['email']}' doesn't match login email '{email}'")
        return False
    
    print(f"Login successful for {email}")
    return True

def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    # First register a user
    email = generate_random_email()
    password = generate_random_password()
    
    register_data = {
        "email": email,
        "password": password
    }
    
    register_response = requests.post(f"{API_URL}/auth/register", json=register_data)
    if register_response.status_code != 200:
        print(f"Error: Registration failed with status code {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return False
    
    print(f"Registration successful for {email}")
    
    # Try to login with wrong password
    login_data = {
        "email": email,
        "password": password + "wrong"
    }
    
    login_response = requests.post(f"{API_URL}/auth/login", json=login_data)
    
    # Should return 401 Unauthorized for invalid credentials
    if login_response.status_code != 401:
        print(f"Error: Invalid credentials login should return 401 but returned {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    # Check error message
    error_data = login_response.json()
    if "detail" not in error_data:
        print(f"Error: Invalid credentials login response missing 'detail' field: {error_data}")
        return False
    
    if "invalid" not in error_data["detail"].lower():
        print(f"Error: Invalid credentials error message should mention 'invalid' but got: {error_data['detail']}")
        return False
    
    print(f"Invalid credentials login correctly rejected with status code {login_response.status_code}")
    return True

def test_login_nonexistent_user():
    """Test login with non-existent user"""
    email = generate_random_email()  # This email shouldn't exist
    password = generate_random_password()
    
    login_data = {
        "email": email,
        "password": password
    }
    
    login_response = requests.post(f"{API_URL}/auth/login", json=login_data)
    
    # Should return 401 Unauthorized for non-existent user
    if login_response.status_code != 401:
        print(f"Error: Non-existent user login should return 401 but returned {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    # Check error message
    error_data = login_response.json()
    if "detail" not in error_data:
        print(f"Error: Non-existent user login response missing 'detail' field: {error_data}")
        return False
    
    if "invalid" not in error_data["detail"].lower():
        print(f"Error: Non-existent user error message should mention 'invalid' but got: {error_data['detail']}")
        return False
    
    print(f"Non-existent user login correctly rejected with status code {login_response.status_code}")
    return True

def test_cors_preflight():
    """Test CORS preflight requests"""
    # Test OPTIONS request to registration endpoint
    headers = {
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, Authorization"
    }
    
    response = requests.options(f"{API_URL}/auth/register", headers=headers)
    
    # Should return 200 OK for preflight request
    if response.status_code != 200:
        print(f"Error: CORS preflight request should return 200 but returned {response.status_code}")
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
    
    # Check if Origin is allowed
    allow_origin = response.headers.get("Access-Control-Allow-Origin")
    if allow_origin != "*" and allow_origin != "https://example.com":
        print(f"Error: Access-Control-Allow-Origin should be '*' or 'https://example.com' but got '{allow_origin}'")
        return False
    
    # Check if POST method is allowed
    allow_methods = response.headers.get("Access-Control-Allow-Methods")
    if "POST" not in allow_methods:
        print(f"Error: Access-Control-Allow-Methods should include 'POST' but got '{allow_methods}'")
        return False
    
    # Check if requested headers are allowed
    allow_headers = response.headers.get("Access-Control-Allow-Headers")
    if "Content-Type" not in allow_headers or "Authorization" not in allow_headers:
        print(f"Error: Access-Control-Allow-Headers should include 'Content-Type' and 'Authorization' but got '{allow_headers}'")
        return False
    
    print(f"CORS preflight request successful with proper headers")
    return True

def test_password_strength_requirements():
    """Test password strength requirements"""
    email = generate_random_email()
    
    # Test various password strengths
    password_tests = [
        {"password": "abc", "should_pass": False, "reason": "too short"},
        {"password": "abcdefg", "should_pass": False, "reason": "too short"},
        {"password": "abcdefgh", "should_pass": True, "reason": "meets minimum length"},
        {"password": "ABCDEFGH", "should_pass": True, "reason": "meets minimum length (uppercase)"},
        {"password": "12345678", "should_pass": True, "reason": "meets minimum length (digits)"},
        {"password": "!@#$%^&*", "should_pass": True, "reason": "meets minimum length (special chars)"},
        {"password": "Abc123!@", "should_pass": True, "reason": "strong password"}
    ]
    
    all_passed = True
    
    for test in password_tests:
        register_data = {
            "email": email,
            "password": test["password"]
        }
        
        response = requests.post(f"{API_URL}/auth/register", json=register_data)
        
        expected_status = 200 if test["should_pass"] else 400
        
        if response.status_code != expected_status:
            print(f"Error: Password '{test['password']}' ({test['reason']}) should {'pass' if test['should_pass'] else 'fail'} but got status code {response.status_code}")
            print(f"Response: {response.text}")
            all_passed = False
        else:
            print(f"Password test passed: '{test['password']}' ({test['reason']}) correctly {'accepted' if test['should_pass'] else 'rejected'}")
        
        # Use a different email for each test to avoid duplicate email errors
        email = generate_random_email()
    
    return all_passed

def test_registration_to_login_flow():
    """Test complete registration to login flow"""
    email = generate_random_email()
    password = generate_random_password()
    
    # Step 1: Register a new user
    register_data = {
        "email": email,
        "password": password
    }
    
    register_response = requests.post(f"{API_URL}/auth/register", json=register_data)
    if register_response.status_code != 200:
        print(f"Error: Registration failed with status code {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return False
    
    register_data = register_response.json()
    register_token = register_data.get("access_token")
    
    if not register_token:
        print("Error: Registration response missing access_token")
        return False
    
    print(f"Registration successful for {email}")
    
    # Step 2: Login with the registered user
    login_data = {
        "email": email,
        "password": password
    }
    
    login_response = requests.post(f"{API_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"Error: Login failed with status code {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    login_data = login_response.json()
    login_token = login_data.get("access_token")
    
    if not login_token:
        print("Error: Login response missing access_token")
        return False
    
    print(f"Login successful for {email}")
    
    # Step 3: Verify user info with the token
    headers = {"Authorization": f"Bearer {login_token}"}
    user_info_response = requests.get(f"{API_URL}/auth/me", headers=headers)
    
    if user_info_response.status_code != 200:
        print(f"Error: Get user info failed with status code {user_info_response.status_code}")
        print(f"Response: {user_info_response.text}")
        return False
    
    user_info = user_info_response.json()
    
    if user_info.get("email") != email:
        print(f"Error: User info email '{user_info.get('email')}' doesn't match registered email '{email}'")
        return False
    
    print(f"User info verification successful for {email}")
    
    # Step 4: Verify email_verified is True
    if not user_info.get("email_verified", False):
        print(f"Error: email_verified should be True but got {user_info.get('email_verified')}")
        return False
    
    print(f"Email verified status is True as expected")
    
    return True

def run_all_tests():
    """Run all authentication tests"""
    tests = [
        ("Registration Success", test_registration_success),
        ("Registration Duplicate Email", test_registration_duplicate_email),
        ("Registration Weak Password", test_registration_weak_password),
        ("Registration Invalid Email", test_registration_invalid_email),
        ("Login Success", test_login_success),
        ("Login Invalid Credentials", test_login_invalid_credentials),
        ("Login Non-existent User", test_login_nonexistent_user),
        ("CORS Preflight", test_cors_preflight),
        ("Password Strength Requirements", test_password_strength_requirements),
        ("Registration to Login Flow", test_registration_to_login_flow)
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