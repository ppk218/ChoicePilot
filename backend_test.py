#!/usr/bin/env python3
import requests
import json
import uuid
import time
import os
import re
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

# Authentication helper functions
def register_test_user(name="John Smith", email=None, password="TestPassword123!"):
    """Register a test user and return the auth token"""
    try:
        # Create test user data with random email if not provided
        if not email:
            email = f"test_{uuid.uuid4().hex[:8]}@example.com"
            
        test_user = {
            "name": name,
            "email": email,
            "password": password
        }
        
        # Register the user
        register_response = requests.post(f"{API_URL}/auth/register", json=test_user)
        
        # Return the response and user data for further analysis
        return register_response, test_user
    except Exception as e:
        print(f"Error registering test user: {str(e)}")
        return None, None

def login_test_user(email, password):
    """Login a test user and return the auth token"""
    try:
        # Login data
        login_data = {
            "email": email,
            "password": password
        }
        
        # Login the user
        login_response = requests.post(f"{API_URL}/auth/login", json=login_data)
        if login_response.status_code == 200:
            print(f"Successfully logged in test user: {email}")
            return login_response.json().get("access_token")
        else:
            print(f"Failed to login test user: {login_response.status_code} - {login_response.text}")
            return None
    except Exception as e:
        print(f"Error logging in test user: {str(e)}")
        return None

def get_auth_headers(token):
    """Get authorization headers for authenticated requests"""
    if not token:
        print("Warning: No auth token available")
        return {}
    
    return {"Authorization": f"Bearer {token}"}

# Test functions for authentication validation
def test_email_validation():
    """Test that email validation properly rejects invalid emails"""
    print("Testing email validation...")
    
    # Test cases with invalid emails
    invalid_emails = [
        "abc123",  # No @ symbol
        "user@",   # No domain
        "@domain.com",  # No username
        "user@domain",  # No TLD
        "user.domain.com",  # Missing @
        "user@.com",  # Missing domain
        "user@domain..com",  # Double dot
    ]
    
    all_passed = True
    
    for invalid_email in invalid_emails:
        response, user_data = register_test_user(email=invalid_email)
        
        # Should be rejected with 400 or 422 status code
        if response.status_code == 200:
            print(f"❌ Failed: Invalid email '{invalid_email}' was accepted")
            all_passed = False
        else:
            print(f"✓ Success: Invalid email '{invalid_email}' was rejected with status {response.status_code}")
    
    # Test with valid email
    valid_email = f"valid_{uuid.uuid4().hex[:8]}@example.com"
    response, user_data = register_test_user(email=valid_email)
    
    if response.status_code != 200:
        print(f"❌ Failed: Valid email '{valid_email}' was rejected with status {response.status_code}")
        all_passed = False
    else:
        print(f"✓ Success: Valid email '{valid_email}' was accepted")
    
    return all_passed

def test_name_validation():
    """Test that name validation requires alphabetic characters only"""
    print("Testing name validation...")
    
    # Test cases with invalid names
    invalid_names = [
        "123456",  # Numbers only
        "User123",  # Alphanumeric
        "!@#$%^",  # Special characters only
        "User!",   # With special character
        "",        # Empty string
    ]
    
    all_passed = True
    valid_email = f"name_test_{uuid.uuid4().hex[:8]}@example.com"
    
    for invalid_name in invalid_names:
        response, user_data = register_test_user(name=invalid_name, email=valid_email)
        
        # Should be rejected with 400 or 422 status code
        if response.status_code == 200:
            print(f"❌ Failed: Invalid name '{invalid_name}' was accepted")
            all_passed = False
        else:
            print(f"✓ Success: Invalid name '{invalid_name}' was rejected with status {response.status_code}")
        
        # Use a new email for each test to avoid "already registered" errors
        valid_email = f"name_test_{uuid.uuid4().hex[:8]}@example.com"
    
    # Test with valid name
    valid_name = "John Smith"
    response, user_data = register_test_user(name=valid_name, email=valid_email)
    
    if response.status_code != 200:
        print(f"❌ Failed: Valid name '{valid_name}' was rejected with status {response.status_code}")
        all_passed = False
    else:
        print(f"✓ Success: Valid name '{valid_name}' was accepted")
    
    return all_passed

def test_password_requirements():
    """Test that password requirements are enforced (8+ chars, uppercase, lowercase, number, symbol)"""
    print("Testing password requirements...")
    
    # Test cases with invalid passwords
    invalid_passwords = [
        "short",  # Too short
        "password",  # No uppercase, number, or symbol
        "PASSWORD",  # No lowercase, number, or symbol
        "Password",  # No number or symbol
        "Password1",  # No symbol
        "password!",  # No uppercase or number
        "PASSWORD1",  # No lowercase or symbol
        "Pass!",  # Too short with requirements
    ]
    
    all_passed = True
    valid_email = f"pwd_test_{uuid.uuid4().hex[:8]}@example.com"
    
    for invalid_password in invalid_passwords:
        response, user_data = register_test_user(password=invalid_password, email=valid_email)
        
        # Should be rejected with 400 or 422 status code
        if response.status_code == 200:
            print(f"❌ Failed: Invalid password '{invalid_password}' was accepted")
            all_passed = False
        else:
            print(f"✓ Success: Invalid password '{invalid_password}' was rejected with status {response.status_code}")
        
        # Use a new email for each test to avoid "already registered" errors
        valid_email = f"pwd_test_{uuid.uuid4().hex[:8]}@example.com"
    
    # Test with valid password
    valid_password = "TestPassword123!"
    response, user_data = register_test_user(password=valid_password, email=valid_email)
    
    if response.status_code != 200:
        print(f"❌ Failed: Valid password '{valid_password}' was rejected with status {response.status_code}")
        all_passed = False
    else:
        print(f"✓ Success: Valid password '{valid_password}' was accepted")
    
    return all_passed

# Test functions for decision flow API integration
def test_authenticated_decision_flow():
    """Test the decision step endpoint for authenticated users"""
    print("Testing authenticated decision flow...")
    
    # Register a test user
    response, user_data = register_test_user()
    if response.status_code != 200:
        print(f"Error: Failed to register test user: {response.status_code} - {response.text}")
        return False
    
    token = response.json().get("access_token")
    headers = get_auth_headers(token)
    
    # Test initial step
    initial_payload = {
        "message": "Should I accept a job offer in a new city?",
        "step": "initial"
    }
    
    print("Testing authenticated decision flow - initial step")
    initial_response = requests.post(f"{API_URL}/decision/step", json=initial_payload, headers=headers)
    
    if initial_response.status_code != 200:
        print(f"Error: Authenticated decision flow initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    required_fields = ["decision_id", "step", "step_number", "response", "followup_question"]
    for field in required_fields:
        if field not in initial_data:
            print(f"Error: Authenticated decision flow response missing required field '{field}'")
            return False
    
    decision_id = initial_data["decision_id"]
    print(f"Authenticated decision flow created with ID: {decision_id}")
    
    # Verify that the response is not mock data
    if "Let me ask you a few questions" not in initial_data["response"]:
        print(f"Error: Unexpected response format: {initial_data['response']}")
        return False
    
    # Verify that the followup question is present
    if not initial_data["followup_question"] or not initial_data["followup_question"].get("question"):
        print(f"Error: Missing followup question: {initial_data['followup_question']}")
        return False
    
    print(f"Followup question: {initial_data['followup_question']['question']}")
    
    return True

def test_anonymous_decision_flow():
    """Test the anonymous decision flow endpoint"""
    print("Testing anonymous decision flow...")
    
    # Test initial step
    initial_payload = {
        "message": "Should I buy a MacBook Pro or a Dell XPS for programming?",
        "step": "initial"
    }
    
    print("Testing anonymous decision flow - initial step")
    initial_response = requests.post(f"{API_URL}/decision/step/anonymous", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Anonymous decision flow initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    required_fields = ["decision_id", "step", "step_number", "response", "followup_question"]
    for field in required_fields:
        if field not in initial_data:
            print(f"Error: Anonymous decision flow response missing required field '{field}'")
            return False
    
    decision_id = initial_data["decision_id"]
    print(f"Anonymous decision flow created with ID: {decision_id}")
    
    # Verify that the response is not mock data
    if "Let me ask you a few questions" not in initial_data["response"]:
        print(f"Error: Unexpected response format: {initial_data['response']}")
        return False
    
    # Verify that the followup question is present
    if not initial_data["followup_question"] or not initial_data["followup_question"].get("question"):
        print(f"Error: Missing followup question: {initial_data['followup_question']}")
        return False
    
    print(f"Followup question: {initial_data['followup_question']['question']}")
    
    # Test followup step
    followup_payload = {
        "message": "My budget is $2000 and I need it for web development and machine learning.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nTesting anonymous decision flow - followup step")
    followup_response = requests.post(f"{API_URL}/decision/step/anonymous", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Anonymous decision flow followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    if "followup_question" not in followup_data or not followup_data["followup_question"].get("question"):
        print(f"Error: Missing second followup question: {followup_data}")
        return False
    
    print(f"Second followup question: {followup_data['followup_question']['question']}")
    
    return True

def test_decision_feedback():
    """Test the decision feedback endpoint"""
    print("Testing decision feedback endpoint...")
    
    # First create an anonymous decision
    initial_payload = {
        "message": "Should I learn Python or JavaScript first?",
        "step": "initial"
    }
    
    print("Creating a decision for feedback testing")
    initial_response = requests.post(f"{API_URL}/decision/step/anonymous", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Failed to create decision for feedback testing: {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    decision_id = initial_response.json()["decision_id"]
    print(f"Created decision with ID: {decision_id}")
    
    # Test positive feedback
    positive_feedback = {
        "helpful": True
    }
    
    print("\nTesting decision feedback - positive")
    positive_response = requests.post(f"{API_URL}/decision/feedback/{decision_id}", json=positive_feedback)
    
    if positive_response.status_code != 200:
        print(f"Error: Decision feedback (positive) returned status code {positive_response.status_code}")
        print(f"Response: {positive_response.text}")
        return False
    
    positive_data = positive_response.json()
    if "message" not in positive_data or "decision_id" not in positive_data:
        print(f"Error: Decision feedback response missing required fields: {positive_data}")
        return False
    
    print(f"Positive feedback submitted successfully: {positive_data['message']}")
    
    # Create another decision for negative feedback
    second_decision_payload = {
        "message": "Should I relocate to a different city for a new job?",
        "step": "initial"
    }
    
    second_decision_response = requests.post(f"{API_URL}/decision/step/anonymous", json=second_decision_payload)
    second_decision_id = second_decision_response.json()["decision_id"]
    
    # Test negative feedback with text
    negative_feedback = {
        "helpful": False,
        "feedback_text": "I was looking for more specific information about job prospects."
    }
    
    print("\nTesting decision feedback - negative with text")
    negative_response = requests.post(f"{API_URL}/decision/feedback/{second_decision_id}", json=negative_feedback)
    
    if negative_response.status_code != 200:
        print(f"Error: Decision feedback (negative) returned status code {negative_response.status_code}")
        print(f"Response: {negative_response.text}")
        return False
    
    negative_data = negative_response.json()
    if "message" not in negative_data or "decision_id" not in negative_data:
        print(f"Error: Decision feedback response missing required fields: {negative_data}")
        return False
    
    print(f"Negative feedback submitted successfully: {negative_data['message']}")
    
    # Test invalid feedback (missing helpful field)
    invalid_feedback = {
        "feedback_text": "This is missing the helpful field."
    }
    
    print("\nTesting decision feedback - invalid (missing helpful field)")
    invalid_response = requests.post(f"{API_URL}/decision/feedback/{decision_id}", json=invalid_feedback)
    
    # Should return 400 Bad Request
    if invalid_response.status_code != 400:
        print(f"Error: Invalid feedback should return 400 but returned {invalid_response.status_code}")
        print(f"Response: {invalid_response.text}")
        return False
    
    print(f"Invalid feedback correctly returns 400 Bad Request")
    
    return True

def test_auth_endpoints():
    """Test the core authentication endpoints"""
    print("Testing core authentication endpoints...")
    
    # Test user registration
    response, user_data = register_test_user()
    if response.status_code != 200:
        print(f"Error: Failed to register test user: {response.status_code} - {response.text}")
        return False
    
    token = response.json().get("access_token")
    print(f"Successfully registered user: {user_data['email']}")
    
    # Test user login
    login_token = login_test_user(user_data['email'], user_data['password'])
    if not login_token:
        print("Error: Failed to login test user")
        return False
    
    print(f"Successfully logged in user: {user_data['email']}")
    
    # Test get current user info
    headers = get_auth_headers(login_token)
    user_info_response = requests.get(f"{API_URL}/auth/me", headers=headers)
    
    if user_info_response.status_code != 200:
        print(f"Error: Get user info returned status code {user_info_response.status_code}")
        print(f"Response: {user_info_response.text}")
        return False
    
    user_info = user_info_response.json()
    required_fields = ["id", "name", "email", "plan", "credits"]
    for field in required_fields:
        if field not in user_info:
            print(f"Error: User info missing required field '{field}'")
            return False
    
    print(f"Successfully retrieved user info: {user_info['email']}")
    
    # Verify that decision IDs are generated properly (UUID format)
    # Create a decision to check ID format
    decision_payload = {
        "message": "Should I invest in stocks or real estate?",
        "step": "initial"
    }
    
    decision_response = requests.post(f"{API_URL}/decision/step", json=decision_payload, headers=headers)
    if decision_response.status_code != 200:
        print(f"Error: Failed to create decision: {decision_response.status_code}")
        return False
    
    decision_id = decision_response.json()["decision_id"]
    
    # Check if decision_id is a valid UUID
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$', re.IGNORECASE)
    if not uuid_pattern.match(decision_id):
        print(f"Error: Decision ID '{decision_id}' is not a valid UUID")
        return False
    
    print(f"Successfully verified decision ID format: {decision_id}")
    
    return True

def test_decision_types():
    """Test that the API handles different decision types"""
    print("Testing different decision types...")
    
    # Register a test user
    response, user_data = register_test_user()
    if response.status_code != 200:
        print(f"Error: Failed to register test user: {response.status_code} - {response.text}")
        return False
    
    token = response.json().get("access_token")
    headers = get_auth_headers(token)
    
    # Test different decision types
    decision_types = [
        {"message": "Should I change careers from marketing to software development?", "type": "career"},
        {"message": "Should I buy a new laptop or upgrade my current one?", "type": "purchase"},
        {"message": "Should I move to Seattle for a new job opportunity?", "type": "relocation"},
        {"message": "Should I learn to play guitar or piano in my free time?", "type": "general"}
    ]
    
    all_passed = True
    
    for decision in decision_types:
        payload = {
            "message": decision["message"],
            "step": "initial"
        }
        
        print(f"\nTesting {decision['type']} decision type")
        response = requests.post(f"{API_URL}/decision/step", json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"Error: {decision['type']} decision returned status code {response.status_code}")
            print(f"Response: {response.text}")
            all_passed = False
            continue
        
        data = response.json()
        if "decision_id" not in data or "followup_question" not in data:
            print(f"Error: {decision['type']} decision missing required fields")
            all_passed = False
            continue
        
        print(f"Successfully created {decision['type']} decision with ID: {data['decision_id']}")
        print(f"Followup question: {data['followup_question']['question']}")
    
    return all_passed

def run_focused_tests():
    """Run the focused tests for the fixed issues"""
    tests = [
        ("Email Validation", test_email_validation),
        ("Name Validation", test_name_validation),
        ("Password Requirements", test_password_requirements),
        ("Authenticated Decision Flow", test_authenticated_decision_flow),
        ("Anonymous Decision Flow", test_anonymous_decision_flow),
        ("Decision Feedback", test_decision_feedback),
        ("Core Authentication", test_auth_endpoints),
        ("Decision Types", test_decision_types)
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
    run_focused_tests()