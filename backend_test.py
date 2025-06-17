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

def test_advanced_decision_endpoint_authenticated():
    """Test the advanced decision endpoint with authenticated user"""
    print("Testing advanced decision endpoint with authenticated user...")
    
    # Register a test user
    response, user_data = register_test_user()
    if response.status_code != 200:
        print(f"Error: Failed to register test user: {response.status_code} - {response.text}")
        return False
    
    token = response.json().get("access_token")
    headers = get_auth_headers(token)
    
    # Test structured decision
    structured_payload = {
        "message": "Should I buy iPhone or Samsung?",
        "step": "initial"
    }
    
    print("Testing advanced decision - structured question")
    structured_response = requests.post(f"{API_URL}/decision/advanced", json=structured_payload, headers=headers)
    
    if structured_response.status_code != 200:
        print(f"Error: Advanced decision endpoint returned status code {structured_response.status_code}")
        print(f"Response: {structured_response.text}")
        return False
    
    structured_data = structured_response.json()
    
    # Verify response format
    required_fields = ["decision_id", "step", "step_number", "response", "followup_questions", "decision_type", "session_version"]
    for field in required_fields:
        if field not in structured_data:
            print(f"Error: Advanced decision response missing required field '{field}'")
            return False
    
    # Verify decision type
    if structured_data["decision_type"] not in ["structured", "intuitive", "mixed"]:
        print(f"Error: Invalid decision type '{structured_data['decision_type']}'")
        return False
    else:
        print(f"Decision type: {structured_data['decision_type']}")
    
    # Verify followup questions format
    if not structured_data["followup_questions"] or not isinstance(structured_data["followup_questions"], list):
        print(f"Error: Missing or invalid followup questions: {structured_data['followup_questions']}")
        return False
    
    for question in structured_data["followup_questions"]:
        if "question" not in question or "nudge" not in question or "category" not in question:
            print(f"Error: Followup question missing required fields: {question}")
            return False
    
    decision_id = structured_data["decision_id"]
    print(f"Advanced decision created with ID: {decision_id}")
    print(f"First followup question: {structured_data['followup_questions'][0]['question']}")
    print(f"Nudge: {structured_data['followup_questions'][0]['nudge']}")
    
    # Test followup step
    followup_payload = {
        "message": "I prefer iPhone because of the ecosystem, but Samsung has better customization options.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nTesting advanced decision - followup step")
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload, headers=headers)
    
    if followup_response.status_code != 200:
        print(f"Error: Advanced decision followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    # Complete all followup questions to get recommendation
    for i in range(2, len(structured_data["followup_questions"]) + 1):
        next_followup_payload = {
            "message": f"This is my answer to question {i}.",
            "step": "followup",
            "decision_id": decision_id,
            "step_number": i
        }
        
        next_response = requests.post(f"{API_URL}/decision/advanced", json=next_followup_payload, headers=headers)
        
        if next_response.status_code != 200:
            print(f"Error: Advanced decision followup step {i} returned status code {next_response.status_code}")
            print(f"Response: {next_response.text}")
            return False
    
    # Test recommendation step
    recommendation_payload = {
        "message": "",
        "step": "recommendation",
        "decision_id": decision_id
    }
    
    print("\nTesting advanced decision - recommendation step")
    recommendation_response = requests.post(f"{API_URL}/decision/advanced", json=recommendation_payload, headers=headers)
    
    if recommendation_response.status_code != 200:
        print(f"Error: Advanced decision recommendation step returned status code {recommendation_response.status_code}")
        print(f"Response: {recommendation_response.text}")
        return False
    
    recommendation_data = recommendation_response.json()
    
    # Verify recommendation format
    if not recommendation_data.get("is_complete") or not recommendation_data.get("recommendation"):
        print(f"Error: Missing or invalid recommendation: {recommendation_data}")
        return False
    
    recommendation = recommendation_data["recommendation"]
    required_rec_fields = ["final_recommendation", "next_steps", "confidence_score", "confidence_tooltip", "reasoning", "trace"]
    for field in required_rec_fields:
        if field not in recommendation:
            print(f"Error: Recommendation missing required field '{field}'")
            return False
    
    # Verify trace information
    trace = recommendation["trace"]
    required_trace_fields = ["models_used", "frameworks_used", "themes", "confidence_factors", "personas_consulted"]
    for field in required_trace_fields:
        if field not in trace:
            print(f"Error: Trace missing required field '{field}'")
            return False
    
    print(f"Successfully received recommendation with confidence score: {recommendation['confidence_score']}")
    print(f"Models used: {', '.join(trace['models_used'])}")
    print(f"Frameworks used: {', '.join(trace['frameworks_used'])}")
    print(f"Next steps: {recommendation['next_steps']}")
    
    # Test intuitive decision
    intuitive_payload = {
        "message": "What career would make me happy?",
        "step": "initial"
    }
    
    print("\nTesting advanced decision - intuitive question")
    intuitive_response = requests.post(f"{API_URL}/decision/advanced", json=intuitive_payload, headers=headers)
    
    if intuitive_response.status_code != 200:
        print(f"Error: Advanced decision endpoint returned status code {intuitive_response.status_code}")
        print(f"Response: {intuitive_response.text}")
        return False
    
    intuitive_data = intuitive_response.json()
    
    # Verify decision type
    if intuitive_data["decision_type"] not in ["structured", "intuitive", "mixed"]:
        print(f"Error: Invalid decision type '{intuitive_data['decision_type']}'")
        return False
    else:
        print(f"Decision type: {intuitive_data['decision_type']}")
    
    # Test mixed decision
    mixed_payload = {
        "message": "Should I switch careers to data science?",
        "step": "initial"
    }
    
    print("\nTesting advanced decision - mixed question")
    mixed_response = requests.post(f"{API_URL}/decision/advanced", json=mixed_payload, headers=headers)
    
    if mixed_response.status_code != 200:
        print(f"Error: Advanced decision endpoint returned status code {mixed_response.status_code}")
        print(f"Response: {mixed_response.text}")
        return False
    
    mixed_data = mixed_response.json()
    
    # Verify decision type
    if mixed_data["decision_type"] not in ["structured", "intuitive", "mixed"]:
        print(f"Error: Invalid decision type '{mixed_data['decision_type']}'")
        return False
    else:
        print(f"Decision type: {mixed_data['decision_type']}")
    
    return True

def test_advanced_decision_endpoint_anonymous():
    """Test the advanced decision endpoint with anonymous user"""
    print("Testing advanced decision endpoint with anonymous user...")
    
    # Test structured decision
    structured_payload = {
        "message": "Should I buy MacBook Pro or Dell XPS?",
        "step": "initial"
    }
    
    print("Testing anonymous advanced decision - structured question")
    structured_response = requests.post(f"{API_URL}/decision/advanced", json=structured_payload)
    
    if structured_response.status_code != 200:
        print(f"Error: Anonymous advanced decision endpoint returned status code {structured_response.status_code}")
        print(f"Response: {structured_response.text}")
        return False
    
    structured_data = structured_response.json()
    
    # Verify response format
    required_fields = ["decision_id", "step", "step_number", "response", "followup_questions", "decision_type", "session_version"]
    for field in required_fields:
        if field not in structured_data:
            print(f"Error: Anonymous advanced decision response missing required field '{field}'")
            return False
    
    decision_id = structured_data["decision_id"]
    print(f"Anonymous advanced decision created with ID: {decision_id}")
    print(f"Decision type: {structured_data['decision_type']}")
    
    # Test followup step
    followup_payload = {
        "message": "I need it for software development and video editing.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nTesting anonymous advanced decision - followup step")
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Anonymous advanced decision followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    # Complete all followup questions to get recommendation
    for i in range(2, len(structured_data["followup_questions"]) + 1):
        next_followup_payload = {
            "message": f"This is my answer to question {i}.",
            "step": "followup",
            "decision_id": decision_id,
            "step_number": i
        }
        
        next_response = requests.post(f"{API_URL}/decision/advanced", json=next_followup_payload)
        
        if next_response.status_code != 200:
            print(f"Error: Anonymous advanced decision followup step {i} returned status code {next_response.status_code}")
            print(f"Response: {next_response.text}")
            return False
    
    # Test recommendation step
    recommendation_payload = {
        "message": "",
        "step": "recommendation",
        "decision_id": decision_id
    }
    
    print("\nTesting anonymous advanced decision - recommendation step")
    recommendation_response = requests.post(f"{API_URL}/decision/advanced", json=recommendation_payload)
    
    if recommendation_response.status_code != 200:
        print(f"Error: Anonymous advanced decision recommendation step returned status code {recommendation_response.status_code}")
        print(f"Response: {recommendation_response.text}")
        return False
    
    recommendation_data = recommendation_response.json()
    
    # Verify recommendation format
    if not recommendation_data.get("is_complete") or not recommendation_data.get("recommendation"):
        print(f"Error: Missing or invalid recommendation: {recommendation_data}")
        return False
    
    recommendation = recommendation_data["recommendation"]
    required_rec_fields = ["final_recommendation", "next_steps", "confidence_score", "confidence_tooltip", "reasoning", "trace"]
    for field in required_rec_fields:
        if field not in recommendation:
            print(f"Error: Recommendation missing required field '{field}'")
            return False
    
    # Verify trace information
    trace = recommendation["trace"]
    required_trace_fields = ["models_used", "frameworks_used", "themes", "confidence_factors", "personas_consulted"]
    for field in required_trace_fields:
        if field not in trace:
            print(f"Error: Trace missing required field '{field}'")
            return False
    
    print(f"Successfully received recommendation with confidence score: {recommendation['confidence_score']}")
    print(f"Models used: {', '.join(trace['models_used'])}")
    print(f"Frameworks used: {', '.join(trace['frameworks_used'])}")
    print(f"Next steps: {recommendation['next_steps']}")
    
    return True

def test_smart_classification_system():
    """Test the new smart classification and persona-based follow-up system"""
    print("Testing smart classification and persona-based follow-up system...")
    
    # Register a test user
    response, user_data = register_test_user()
    if response.status_code != 200:
        print(f"Error: Failed to register test user: {response.status_code} - {response.text}")
        return False
    
    token = response.json().get("access_token")
    headers = get_auth_headers(token)
    
    # Test cases with different complexity levels
    test_cases = [
        {
            "message": "What phone should I buy?",
            "expected_complexity": "LOW",
            "description": "Simple question"
        },
        {
            "message": "Should I switch careers to data science?",
            "expected_complexity": "MEDIUM",
            "description": "Medium complexity question"
        },
        {
            "message": "Should I leave my marriage?",
            "expected_complexity": "HIGH",
            "description": "High complexity question"
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\nTesting {test_case['description']}: '{test_case['message']}'")
        
        # Test with initial step
        initial_payload = {
            "message": test_case["message"],
            "step": "initial"
        }
        
        initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload, headers=headers)
        
        if initial_response.status_code != 200:
            print(f"Error: Advanced decision endpoint returned status code {initial_response.status_code}")
            print(f"Response: {initial_response.text}")
            all_passed = False
            continue
        
        initial_data = initial_response.json()
        
        # Verify response format
        required_fields = ["decision_id", "step", "step_number", "response", "followup_questions", "decision_type", "session_version"]
        for field in required_fields:
            if field not in initial_data:
                print(f"Error: Response missing required field '{field}'")
                all_passed = False
                continue
        
        # Get the session data to check classification
        decision_id = initial_data["decision_id"]
        
        # Check followup questions have persona information
        if not initial_data["followup_questions"] or not isinstance(initial_data["followup_questions"], list):
            print(f"Error: Missing or invalid followup questions: {initial_data['followup_questions']}")
            all_passed = False
            continue
        
        for question in initial_data["followup_questions"]:
            if "question" not in question or "nudge" not in question or "category" not in question:
                print(f"Error: Followup question missing required fields: {question}")
                all_passed = False
                continue
        
        # Check if personas are assigned to follow-up questions
        persona_found = False
        for question in initial_data["followup_questions"]:
            if "persona" in question:
                persona_found = True
                print(f"Persona found in follow-up question: {question.get('persona', 'None')}")
                break
        
        if not persona_found:
            print("Warning: No persona information found in follow-up questions")
        
        print(f"Decision type: {initial_data['decision_type']}")
        print(f"First followup question: {initial_data['followup_questions'][0]['question']}")
        print(f"Nudge: {initial_data['followup_questions'][0]['nudge']}")
        
        # Test followup step
        followup_payload = {
            "message": "This is my answer to the follow-up question.",
            "step": "followup",
            "decision_id": decision_id,
            "step_number": 1
        }
        
        print("\nTesting followup step")
        followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload, headers=headers)
        
        if followup_response.status_code != 200:
            print(f"Error: Followup step returned status code {followup_response.status_code}")
            print(f"Response: {followup_response.text}")
            all_passed = False
            continue
        
        # Complete all followup questions to get recommendation
        followup_data = followup_response.json()
        for i in range(2, len(initial_data["followup_questions"]) + 1):
            next_followup_payload = {
                "message": f"This is my answer to question {i}.",
                "step": "followup",
                "decision_id": decision_id,
                "step_number": i
            }
            
            next_response = requests.post(f"{API_URL}/decision/advanced", json=next_followup_payload, headers=headers)
            
            if next_response.status_code != 200:
                print(f"Error: Followup step {i} returned status code {next_response.status_code}")
                print(f"Response: {next_response.text}")
                all_passed = False
                break
        
        # Test recommendation step
        recommendation_payload = {
            "message": "",
            "step": "recommendation",
            "decision_id": decision_id
        }
        
        print("\nTesting recommendation step")
        recommendation_response = requests.post(f"{API_URL}/decision/advanced", json=recommendation_payload, headers=headers)
        
        if recommendation_response.status_code != 200:
            print(f"Error: Recommendation step returned status code {recommendation_response.status_code}")
            print(f"Response: {recommendation_response.text}")
            all_passed = False
            continue
        
        recommendation_data = recommendation_response.json()
        
        # Verify recommendation format
        if not recommendation_data.get("is_complete") or not recommendation_data.get("recommendation"):
            print(f"Error: Missing or invalid recommendation: {recommendation_data}")
            all_passed = False
            continue
        
        recommendation = recommendation_data["recommendation"]
        required_rec_fields = ["final_recommendation", "next_steps", "confidence_score", "confidence_tooltip", "reasoning", "trace"]
        for field in required_rec_fields:
            if field not in recommendation:
                print(f"Error: Recommendation missing required field '{field}'")
                all_passed = False
                continue
        
        # Verify trace information
        trace = recommendation["trace"]
        required_trace_fields = ["models_used", "frameworks_used", "themes", "confidence_factors", "personas_consulted"]
        for field in required_trace_fields:
            if field not in trace:
                print(f"Error: Trace missing required field '{field}'")
                all_passed = False
                continue
        
        print(f"Successfully received recommendation with confidence score: {recommendation['confidence_score']}")
        print(f"Models used: {', '.join(trace['models_used'])}")
        print(f"Frameworks used: {', '.join(trace['frameworks_used'])}")
        print(f"Personas consulted: {', '.join(trace['personas_consulted'])}")
        
    return all_passed

def test_anonymous_smart_classification():
    """Test the smart classification system with anonymous user"""
    print("Testing smart classification with anonymous user...")
    
    # Test with a medium complexity question
    initial_payload = {
        "message": "Should I switch careers to data science?",
        "step": "initial"
    }
    
    print("Testing anonymous advanced decision with medium complexity question")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Anonymous advanced decision endpoint returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    
    # Verify response format
    required_fields = ["decision_id", "step", "step_number", "response", "followup_questions", "decision_type", "session_version"]
    for field in required_fields:
        if field not in initial_data:
            print(f"Error: Response missing required field '{field}'")
            return False
    
    decision_id = initial_data["decision_id"]
    print(f"Anonymous advanced decision created with ID: {decision_id}")
    print(f"Decision type: {initial_data['decision_type']}")
    
    # Check followup questions have persona information
    if not initial_data["followup_questions"] or not isinstance(initial_data["followup_questions"], list):
        print(f"Error: Missing or invalid followup questions: {initial_data['followup_questions']}")
        return False
    
    for question in initial_data["followup_questions"]:
        if "question" not in question or "nudge" not in question or "category" not in question:
            print(f"Error: Followup question missing required fields: {question}")
            return False
    
    # Check if personas are assigned to follow-up questions
    persona_found = False
    for question in initial_data["followup_questions"]:
        if "persona" in question:
            persona_found = True
            print(f"Persona found in follow-up question: {question.get('persona', 'None')}")
            break
    
    if not persona_found:
        print("Warning: No persona information found in follow-up questions")
    
    print(f"First followup question: {initial_data['followup_questions'][0]['question']}")
    print(f"Nudge: {initial_data['followup_questions'][0]['nudge']}")
    
    # Test followup step
    followup_payload = {
        "message": "I'm currently a marketing manager but I'm interested in data science because of the analytical aspects.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nTesting anonymous followup step")
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Anonymous followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    # Complete all followup questions to get recommendation
    followup_data = followup_response.json()
    for i in range(2, len(initial_data["followup_questions"]) + 1):
        next_followup_payload = {
            "message": f"This is my answer to question {i}.",
            "step": "followup",
            "decision_id": decision_id,
            "step_number": i
        }
        
        next_response = requests.post(f"{API_URL}/decision/advanced", json=next_followup_payload)
        
        if next_response.status_code != 200:
            print(f"Error: Anonymous followup step {i} returned status code {next_response.status_code}")
            print(f"Response: {next_response.text}")
            return False
    
    # Test recommendation step
    recommendation_payload = {
        "message": "",
        "step": "recommendation",
        "decision_id": decision_id
    }
    
    print("\nTesting anonymous recommendation step")
    recommendation_response = requests.post(f"{API_URL}/decision/advanced", json=recommendation_payload)
    
    if recommendation_response.status_code != 200:
        print(f"Error: Anonymous recommendation step returned status code {recommendation_response.status_code}")
        print(f"Response: {recommendation_response.text}")
        return False
    
    recommendation_data = recommendation_response.json()
    
    # Verify recommendation format
    if not recommendation_data.get("is_complete") or not recommendation_data.get("recommendation"):
        print(f"Error: Missing or invalid recommendation: {recommendation_data}")
        return False
    
    recommendation = recommendation_data["recommendation"]
    required_rec_fields = ["final_recommendation", "next_steps", "confidence_score", "confidence_tooltip", "reasoning", "trace"]
    for field in required_rec_fields:
        if field not in recommendation:
            print(f"Error: Recommendation missing required field '{field}'")
            return False
    
    # Verify trace information
    trace = recommendation["trace"]
    required_trace_fields = ["models_used", "frameworks_used", "themes", "confidence_factors", "personas_consulted"]
    for field in required_trace_fields:
        if field not in trace:
            print(f"Error: Trace missing required field '{field}'")
            return False
    
    print(f"Successfully received anonymous recommendation with confidence score: {recommendation['confidence_score']}")
    print(f"Models used: {', '.join(trace['models_used'])}")
    print(f"Frameworks used: {', '.join(trace['frameworks_used'])}")
    print(f"Personas consulted: {', '.join(trace['personas_consulted'])}")
    
    return True

def test_hybrid_followup_system():
    """Test the hybrid AI-led follow-up system"""
    print("Testing hybrid AI-led follow-up system...")
    
    # Register a test user
    response, user_data = register_test_user()
    if response.status_code != 200:
        print(f"Error: Failed to register test user: {response.status_code} - {response.text}")
        return False
    
    token = response.json().get("access_token")
    headers = get_auth_headers(token)
    
    # Test initial step with career-related question
    initial_payload = {
        "message": "Should I switch careers to data science?",
        "step": "initial"
    }
    
    print("Testing hybrid follow-up system - initial step")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload, headers=headers)
    
    if initial_response.status_code != 200:
        print(f"Error: Hybrid follow-up system initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    
    # Verify that only the first question is returned
    if not initial_data["followup_questions"] or len(initial_data["followup_questions"]) != 1:
        print(f"Error: Expected exactly 1 followup question in initial response, got {len(initial_data['followup_questions'])}")
        return False
    
    first_question = initial_data["followup_questions"][0]
    print(f"First question: {first_question['question']}")
    print(f"Nudge: {first_question['nudge']}")
    print(f"Persona: {first_question['persona']}")
    
    # Test first followup step
    followup1_payload = {
        "message": "I currently work in marketing but have been learning Python and statistics in my free time.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nTesting hybrid follow-up system - first followup step")
    followup1_response = requests.post(f"{API_URL}/decision/advanced", json=followup1_payload, headers=headers)
    
    if followup1_response.status_code != 200:
        print(f"Error: First followup step returned status code {followup1_response.status_code}")
        print(f"Response: {followup1_response.text}")
        return False
    
    followup1_data = followup1_response.json()
    
    # Verify that the second question is returned
    if not followup1_data["followup_questions"] or len(followup1_data["followup_questions"]) != 1:
        print(f"Error: Expected exactly 1 followup question in second response, got {len(followup1_data['followup_questions'])}")
        return False
    
    second_question = followup1_data["followup_questions"][0]
    print(f"Second question: {second_question['question']}")
    print(f"Nudge: {second_question['nudge']}")
    print(f"Persona: {second_question['persona']}")
    
    # Test second followup step
    followup2_payload = {
        "message": "I'm concerned about the salary drop during the transition, but excited about the long-term prospects.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 2
    }
    
    print("\nTesting hybrid follow-up system - second followup step")
    followup2_response = requests.post(f"{API_URL}/decision/advanced", json=followup2_payload, headers=headers)
    
    if followup2_response.status_code != 200:
        print(f"Error: Second followup step returned status code {followup2_response.status_code}")
        print(f"Response: {followup2_response.text}")
        return False
    
    followup2_data = followup2_response.json()
    
    # Verify that the third question is returned
    if not followup2_data["followup_questions"] or len(followup2_data["followup_questions"]) != 1:
        print(f"Error: Expected exactly 1 followup question in third response, got {len(followup2_data['followup_questions'])}")
        return False
    
    third_question = followup2_data["followup_questions"][0]
    print(f"Third question: {third_question['question']}")
    print(f"Nudge: {third_question['nudge']}")
    print(f"Persona: {third_question['persona']}")
    
    # Test third followup step (should generate recommendation)
    followup3_payload = {
        "message": "I have about 6 months of savings and my current employer might support part-time education.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 3
    }
    
    print("\nTesting hybrid follow-up system - third followup step (recommendation)")
    followup3_response = requests.post(f"{API_URL}/decision/advanced", json=followup3_payload, headers=headers)
    
    if followup3_response.status_code != 200:
        print(f"Error: Third followup step returned status code {followup3_response.status_code}")
        print(f"Response: {followup3_response.text}")
        return False
    
    followup3_data = followup3_response.json()
    
    # Verify that we got a recommendation
    if not followup3_data.get("is_complete") or not followup3_data.get("recommendation"):
        print(f"Error: Missing or invalid recommendation after third followup: {followup3_data}")
        return False
    
    recommendation = followup3_data["recommendation"]
    
    # Verify that the recommendation includes the new fields
    if not recommendation.get("summary"):
        print("Error: Recommendation missing summary field")
        return False
    
    if not recommendation.get("next_steps_with_time") or not isinstance(recommendation["next_steps_with_time"], list):
        print("Error: Recommendation missing next_steps_with_time field")
        return False
    
    print(f"Summary: {recommendation['summary']}")
    print(f"Next steps with time: {recommendation['next_steps_with_time']}")
    
    # Verify that the recommendation references user answers
    user_answers = [
        "marketing", "Python", "statistics", 
        "salary drop", "transition", "long-term prospects",
        "6 months", "savings", "employer", "part-time education"
    ]
    
    answer_references_found = 0
    for term in user_answers:
        if term.lower() in recommendation["final_recommendation"].lower():
            answer_references_found += 1
            print(f"Found reference to user answer: '{term}'")
    
    if answer_references_found < 2:
        print(f"Warning: Recommendation only references {answer_references_found} user answers, expected at least 2")
    
    return True

def run_focused_tests():
    """Run the focused tests for the fixed issues"""
    tests = [
        ("Hybrid Follow-up System", test_hybrid_followup_system),
        ("Smart Classification System", test_smart_classification_system),
        ("Anonymous Smart Classification", test_anonymous_smart_classification),
        ("Email Validation", test_email_validation),
        ("Name Validation", test_name_validation),
        ("Password Requirements", test_password_requirements),
        ("Authenticated Decision Flow", test_authenticated_decision_flow),
        ("Anonymous Decision Flow", test_anonymous_decision_flow),
        ("Decision Feedback", test_decision_feedback),
        ("Core Authentication", test_auth_endpoints),
        ("Decision Types", test_decision_types),
        ("Advanced Decision Endpoint - Authenticated", test_advanced_decision_endpoint_authenticated),
        ("Advanced Decision Endpoint - Anonymous", test_advanced_decision_endpoint_anonymous)
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