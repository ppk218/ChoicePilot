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

# Test user credentials for authenticated endpoints
TEST_USER = {
    "name": "Test User",
    "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
    "password": "TestPassword123!"
}

# Store auth token for authenticated requests
AUTH_TOKEN = None

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

def get_auth_headers(token=None):
    """Get authorization headers for authenticated requests"""
    global AUTH_TOKEN
    
    if token:
        AUTH_TOKEN = token
    elif not AUTH_TOKEN:
        # Register and get token
        register_response = requests.post(f"{API_URL}/auth/register", json=TEST_USER)
        if register_response.status_code == 200:
            AUTH_TOKEN = register_response.json().get("access_token")
        else:
            print(f"Failed to register test user: {register_response.status_code} - {register_response.text}")
            return {}
    
    if not AUTH_TOKEN:
        print("Warning: No auth token available")
        return {}
    
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}

# Authentication Tests
def test_register_endpoint():
    """Test user registration"""
    # Create a unique test user
    test_user = {
        "name": "Test User",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!"
    }
    
    # Register the user
    response = requests.post(f"{API_URL}/auth/register", json=test_user)
    
    if response.status_code != 200:
        print(f"Error: Register endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["message", "access_token", "user"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Register response missing required field '{field}'")
            return False
    
    user_data = data["user"]
    user_required_fields = ["id", "name", "email", "plan", "credits", "email_verified"]
    for field in user_required_fields:
        if field not in user_data:
            print(f"Error: User data missing required field '{field}'")
            return False
    
    if user_data["email"] != test_user["email"]:
        print(f"Error: Returned email '{user_data['email']}' doesn't match sent email '{test_user['email']}'")
        return False
    
    if not data["access_token"]:
        print("Error: Access token is empty")
        return False
    
    print(f"Registration successful for user: {user_data['email']}")
    return True

def test_register_weak_password():
    """Test registration with weak password"""
    # Create a test user with weak password
    test_user = {
        "name": "Test User",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "weak"  # Too short
    }
    
    # Register the user
    response = requests.post(f"{API_URL}/auth/register", json=test_user)
    
    # Should return 400 Bad Request
    if response.status_code != 400:
        print(f"Error: Register with weak password should return 400 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print("Registration correctly rejects weak passwords")
    return True

def test_register_duplicate_email():
    """Test registration with duplicate email"""
    # Create a test user
    test_user = {
        "name": "Test User",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!"
    }
    
    # Register the user
    response = requests.post(f"{API_URL}/auth/register", json=test_user)
    if response.status_code != 200:
        print(f"Error: First registration failed: {response.status_code} - {response.text}")
        return False
    
    # Try to register again with the same email
    response = requests.post(f"{API_URL}/auth/register", json=test_user)
    
    # Should return 400 Bad Request
    if response.status_code != 400:
        print(f"Error: Register with duplicate email should return 400 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print("Registration correctly rejects duplicate emails")
    return True

def test_login_endpoint():
    """Test user login"""
    # Create a test user
    test_user = {
        "name": "Test User",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!"
    }
    
    # Register the user
    register_response = requests.post(f"{API_URL}/auth/register", json=test_user)
    if register_response.status_code != 200:
        print(f"Error: Registration failed: {register_response.status_code} - {register_response.text}")
        return False
    
    # Login with the same credentials
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"Error: Login endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["message", "access_token", "user"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Login response missing required field '{field}'")
            return False
    
    if not data["access_token"]:
        print("Error: Access token is empty")
        return False
    
    print(f"Login successful for user: {login_data['email']}")
    return True

def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    # Create login data with invalid credentials
    login_data = {
        "email": f"nonexistent_{uuid.uuid4().hex[:8]}@example.com",
        "password": "InvalidPassword123!"
    }
    
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    
    # Should return 401 Unauthorized
    if response.status_code != 401:
        print(f"Error: Login with invalid credentials should return 401 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print("Login correctly rejects invalid credentials")
    return True

def test_auth_me_endpoint():
    """Test getting current user info"""
    # Register a test user and get token
    test_user = {
        "name": "Test User",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!"
    }
    
    register_response = requests.post(f"{API_URL}/auth/register", json=test_user)
    if register_response.status_code != 200:
        print(f"Error: Registration failed: {register_response.status_code} - {register_response.text}")
        return False
    
    token = register_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current user info
    response = requests.get(f"{API_URL}/auth/me", headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Auth/me endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["id", "name", "email", "plan", "credits", "email_verified"]
    for field in required_fields:
        if field not in data:
            print(f"Error: User info missing required field '{field}'")
            return False
    
    if data["email"] != test_user["email"]:
        print(f"Error: Returned email '{data['email']}' doesn't match expected email '{test_user['email']}'")
        return False
    
    print(f"Auth/me endpoint returned correct user info for: {data['email']}")
    return True

def test_auth_me_no_token():
    """Test auth/me endpoint without token"""
    response = requests.get(f"{API_URL}/auth/me")
    
    # Should return 401 Unauthorized or 403 Forbidden
    if response.status_code not in [401, 403]:
        print(f"Error: Auth/me without token should return 401 or 403 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print("Auth/me endpoint correctly requires authentication")
    return True

# Decision Flow Tests
def test_decision_step_endpoint():
    """Test the decision step endpoint for authenticated users"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Create initial decision step
    initial_data = {
        "message": "I'm trying to decide between a MacBook Pro and a Dell XPS for programming work.",
        "step": "initial"
    }
    
    response = requests.post(f"{API_URL}/decision/step", json=initial_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Decision step endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["decision_id", "step", "step_number", "response", "followup_question"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Decision step response missing required field '{field}'")
            return False
    
    if data["step"] != "followup" or data["step_number"] != 1:
        print(f"Error: Initial step should transition to followup step 1, but got {data['step']} step {data['step_number']}")
        return False
    
    # Store decision_id for next step
    decision_id = data["decision_id"]
    
    # Test followup step
    followup_data = {
        "message": "My budget is around $2000 and I need it for software development and machine learning.",
        "decision_id": decision_id,
        "step": "followup",
        "step_number": 1
    }
    
    response = requests.post(f"{API_URL}/decision/step", json=followup_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Followup step endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if data["step"] != "followup" or data["step_number"] != 2:
        print(f"Error: First followup should transition to followup step 2, but got {data['step']} step {data['step_number']}")
        return False
    
    # Test second followup step
    followup_data = {
        "message": "Battery life and performance are most important to me.",
        "decision_id": decision_id,
        "step": "followup",
        "step_number": 2
    }
    
    response = requests.post(f"{API_URL}/decision/step", json=followup_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Second followup step endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if data["step"] != "followup" or data["step_number"] != 3:
        print(f"Error: Second followup should transition to followup step 3, but got {data['step']} step {data['step_number']}")
        return False
    
    # Test third followup step (should complete the decision)
    followup_data = {
        "message": "I prefer macOS but I'm open to Windows if it's significantly better value.",
        "decision_id": decision_id,
        "step": "followup",
        "step_number": 3
    }
    
    response = requests.post(f"{API_URL}/decision/step", json=followup_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Third followup step endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if not data.get("is_complete"):
        print(f"Error: Third followup should complete the decision, but is_complete is {data.get('is_complete')}")
        return False
    
    if "recommendation" not in data:
        print(f"Error: Completed decision should include recommendation, but it's missing")
        return False
    
    recommendation = data["recommendation"]
    recommendation_fields = ["recommendation", "confidence_score", "reasoning"]
    for field in recommendation_fields:
        if field not in recommendation:
            print(f"Error: Recommendation missing required field '{field}'")
            return False
    
    print(f"Decision flow completed successfully with recommendation")
    return True

def test_anonymous_decision_step():
    """Test the anonymous decision step endpoint"""
    # Create initial decision step
    initial_data = {
        "message": "I'm trying to decide where to go on vacation this summer.",
        "step": "initial"
    }
    
    response = requests.post(f"{API_URL}/decision/step/anonymous", json=initial_data)
    
    if response.status_code != 200:
        print(f"Error: Anonymous decision step endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["decision_id", "step", "step_number", "response", "followup_question"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Anonymous decision step response missing required field '{field}'")
            return False
    
    if data["step"] != "followup" or data["step_number"] != 1:
        print(f"Error: Initial anonymous step should transition to followup step 1, but got {data['step']} step {data['step_number']}")
        return False
    
    # Store decision_id for next step
    decision_id = data["decision_id"]
    
    # Test followup step
    followup_data = {
        "message": "I'm looking for a beach destination with good food and culture.",
        "decision_id": decision_id,
        "step": "followup",
        "step_number": 1
    }
    
    response = requests.post(f"{API_URL}/decision/step/anonymous", json=followup_data)
    
    if response.status_code != 200:
        print(f"Error: Anonymous followup step endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Anonymous decision flow working correctly")
    return True

def test_decision_feedback():
    """Test submitting feedback for a decision"""
    # First create a decision
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Create initial decision step
    initial_data = {
        "message": "I'm trying to decide what smartphone to buy.",
        "step": "initial"
    }
    
    response = requests.post(f"{API_URL}/decision/step", json=initial_data, headers=headers)
    if response.status_code != 200:
        print(f"Error: Failed to create test decision: {response.status_code} - {response.text}")
        return False
    
    decision_id = response.json()["decision_id"]
    
    # Complete the decision flow (simplified for testing)
    for step_num in range(1, 4):
        followup_data = {
            "message": f"This is my answer to followup question {step_num}.",
            "decision_id": decision_id,
            "step": "followup",
            "step_number": step_num
        }
        
        response = requests.post(f"{API_URL}/decision/step", json=followup_data, headers=headers)
        if response.status_code != 200:
            print(f"Error: Failed to complete decision flow: {response.status_code} - {response.text}")
            return False
    
    # Submit feedback
    feedback_data = {
        "helpful": True,
        "feedback_text": "This was very helpful, thank you!"
    }
    
    response = requests.post(f"{API_URL}/decision/feedback/{decision_id}", json=feedback_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Feedback endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "message" not in data:
        print(f"Error: Feedback response missing 'message' field: {data}")
        return False
    
    print(f"Decision feedback submitted successfully")
    return True

# Run all tests
def run_all_tests():
    """Run all backend tests"""
    auth_tests = [
        ("Register Endpoint", test_register_endpoint),
        ("Register with Weak Password", test_register_weak_password),
        ("Register with Duplicate Email", test_register_duplicate_email),
        ("Login Endpoint", test_login_endpoint),
        ("Login with Invalid Credentials", test_login_invalid_credentials),
        ("Auth/Me Endpoint", test_auth_me_endpoint),
        ("Auth/Me without Token", test_auth_me_no_token)
    ]
    
    decision_tests = [
        ("Decision Step Endpoint", test_decision_step_endpoint),
        ("Anonymous Decision Step", test_anonymous_decision_step),
        ("Decision Feedback", test_decision_feedback)
    ]
    
    # Run authentication tests
    print("\n" + "="*80)
    print("TESTING AUTHENTICATION ENDPOINTS")
    print("="*80)
    for test_name, test_func in auth_tests:
        run_test(test_name, test_func)
    
    # Run decision flow tests
    print("\n" + "="*80)
    print("TESTING DECISION FLOW ENDPOINTS")
    print("="*80)
    for test_name, test_func in decision_tests:
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