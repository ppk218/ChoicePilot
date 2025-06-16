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

def get_auth_headers(token):
    """Get authorization headers for authenticated requests"""
    if not token:
        print("Warning: No auth token available")
        return {}
    
    return {"Authorization": f"Bearer {token}"}

def test_enhanced_recommendation_fields():
    """Test that the enhanced recommendation fields (summary and next_steps_with_time) are generated correctly"""
    print("Testing enhanced recommendation fields...")
    
    # Register a test user
    response, user_data = register_test_user()
    if response.status_code != 200:
        print(f"Error: Failed to register test user: {response.status_code} - {response.text}")
        return False
    
    token = response.json().get("access_token")
    headers = get_auth_headers(token)
    
    # Test with a complex decision that should generate detailed recommendations
    initial_payload = {
        "message": "Should I quit my job to start my own business?",
        "step": "initial"
    }
    
    print("Testing advanced decision - complex career question")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload, headers=headers)
    
    if initial_response.status_code != 200:
        print(f"Error: Advanced decision endpoint returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Advanced decision created with ID: {decision_id}")
    
    # Complete all followup questions to get to the recommendation
    followup_answers = [
        "I've been working at my current job for 5 years and feel unfulfilled. I have a business idea for a consulting service in my industry.",
        "I have about 6 months of savings and my partner has a stable job that could support us during the transition.",
        "My biggest concern is financial stability, but I'm also worried about regretting not trying."
    ]
    
    for i, answer in enumerate(followup_answers, 1):
        followup_payload = {
            "message": answer,
            "step": "followup",
            "decision_id": decision_id,
            "step_number": i
        }
        
        print(f"\nSubmitting followup answer {i}")
        followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload, headers=headers)
        
        if followup_response.status_code != 200:
            print(f"Error: Advanced decision followup step {i} returned status code {followup_response.status_code}")
            print(f"Response: {followup_response.text}")
            return False
    
    # Get the recommendation
    recommendation_payload = {
        "message": "",
        "step": "recommendation",
        "decision_id": decision_id
    }
    
    print("\nGetting recommendation")
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
    
    # Check for the enhanced fields
    if "summary" not in recommendation:
        print("Error: Recommendation missing 'summary' field")
        return False
    else:
        print(f"Summary field found: {recommendation['summary']}")
    
    if "next_steps_with_time" not in recommendation:
        print("Error: Recommendation missing 'next_steps_with_time' field")
        return False
    else:
        next_steps_with_time = recommendation["next_steps_with_time"]
        if not isinstance(next_steps_with_time, list) or len(next_steps_with_time) == 0:
            print(f"Error: 'next_steps_with_time' is not a valid list: {next_steps_with_time}")
            return False
        
        # Check structure of next_steps_with_time items
        for i, step in enumerate(next_steps_with_time):
            if not isinstance(step, dict):
                print(f"Error: Step {i+1} is not a dictionary: {step}")
                return False
            
            required_fields = ["step", "time_estimate", "description"]
            for field in required_fields:
                if field not in step:
                    print(f"Error: Step {i+1} missing required field '{field}': {step}")
                    return False
        
        print(f"Next steps with time estimates found ({len(next_steps_with_time)} steps):")
        for i, step in enumerate(next_steps_with_time):
            print(f"  Step {i+1}: {step['step']} - {step['time_estimate']}")
            print(f"    Description: {step['description']}")
    
    # Verify that the summary is a concise TL;DR
    summary = recommendation["summary"]
    if len(summary.split()) > 50:  # Rough check that it's not too long
        print(f"Warning: Summary might be too long for a TL;DR ({len(summary.split())} words)")
    
    # Verify that time estimates are in a reasonable format
    time_pattern = re.compile(r'(\d+)[\s-]*(\w+|\d+\s\w+)')
    for step in next_steps_with_time:
        time_estimate = step["time_estimate"]
        if not time_pattern.search(time_estimate) and "hour" not in time_estimate.lower() and "day" not in time_estimate.lower() and "week" not in time_estimate.lower() and "month" not in time_estimate.lower() and "minute" not in time_estimate.lower():
            print(f"Warning: Time estimate '{time_estimate}' might not be in a standard format")
    
    print("Enhanced recommendation fields test passed successfully")
    return True

def test_anonymous_enhanced_recommendation_fields():
    """Test that the enhanced recommendation fields work for anonymous users too"""
    print("Testing enhanced recommendation fields for anonymous users...")
    
    # Test with a complex decision that should generate detailed recommendations
    initial_payload = {
        "message": "Should I buy a house or continue renting?",
        "step": "initial"
    }
    
    print("Testing anonymous advanced decision - complex financial question")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Anonymous advanced decision endpoint returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Anonymous advanced decision created with ID: {decision_id}")
    
    # Complete all followup questions to get to the recommendation
    followup_answers = [
        "I've been renting for 8 years and have $60,000 saved for a down payment. Houses in my area cost $350,000-$400,000.",
        "Mortgage payments would be about 30% higher than my current rent, but I'd be building equity.",
        "I plan to stay in the area for at least 5 years, and I'm thinking about starting a family in the next 2-3 years."
    ]
    
    for i, answer in enumerate(followup_answers, 1):
        followup_payload = {
            "message": answer,
            "step": "followup",
            "decision_id": decision_id,
            "step_number": i
        }
        
        print(f"\nSubmitting anonymous followup answer {i}")
        followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
        
        if followup_response.status_code != 200:
            print(f"Error: Anonymous advanced decision followup step {i} returned status code {followup_response.status_code}")
            print(f"Response: {followup_response.text}")
            return False
    
    # Get the recommendation
    recommendation_payload = {
        "message": "",
        "step": "recommendation",
        "decision_id": decision_id
    }
    
    print("\nGetting anonymous recommendation")
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
    
    # Check for the enhanced fields
    if "summary" not in recommendation:
        print("Error: Anonymous recommendation missing 'summary' field")
        return False
    else:
        print(f"Summary field found: {recommendation['summary']}")
    
    if "next_steps_with_time" not in recommendation:
        print("Error: Anonymous recommendation missing 'next_steps_with_time' field")
        return False
    else:
        next_steps_with_time = recommendation["next_steps_with_time"]
        if not isinstance(next_steps_with_time, list) or len(next_steps_with_time) == 0:
            print(f"Error: 'next_steps_with_time' is not a valid list: {next_steps_with_time}")
            return False
        
        # Check structure of next_steps_with_time items
        for i, step in enumerate(next_steps_with_time):
            if not isinstance(step, dict):
                print(f"Error: Step {i+1} is not a dictionary: {step}")
                return False
            
            required_fields = ["step", "time_estimate", "description"]
            for field in required_fields:
                if field not in step:
                    print(f"Error: Step {i+1} missing required field '{field}': {step}")
                    return False
        
        print(f"Next steps with time estimates found ({len(next_steps_with_time)} steps):")
        for i, step in enumerate(next_steps_with_time):
            print(f"  Step {i+1}: {step['step']} - {step['time_estimate']}")
            print(f"    Description: {step['description']}")
    
    print("Anonymous enhanced recommendation fields test passed successfully")
    return True

def run_enhanced_fields_tests():
    """Run tests for the enhanced recommendation fields"""
    tests = [
        ("Enhanced Recommendation Fields", test_enhanced_recommendation_fields),
        ("Anonymous Enhanced Recommendation Fields", test_anonymous_enhanced_recommendation_fields)
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
    run_enhanced_fields_tests()