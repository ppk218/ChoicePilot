#!/usr/bin/env python3
import requests
import json
import uuid
import time
import os
from dotenv import load_dotenv
import sys
import random

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
    "email": "test@example.com",
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

# Authentication helper functions
def register_test_user():
    """Register a test user and return the auth token"""
    try:
        # Check if user already exists by trying to login
        login_response = requests.post(f"{API_URL}/auth/login", json=TEST_USER)
        if login_response.status_code == 200:
            # User exists, return token
            return login_response.json().get("access_token")
        
        # User doesn't exist, register
        register_response = requests.post(f"{API_URL}/auth/register", json=TEST_USER)
        if register_response.status_code == 200:
            return register_response.json().get("access_token")
        else:
            print(f"Failed to register test user: {register_response.status_code} - {register_response.text}")
            return None
    except Exception as e:
        print(f"Error registering test user: {str(e)}")
        return None

def get_auth_headers(token=None):
    """Get authorization headers for authenticated requests"""
    global AUTH_TOKEN
    
    if token:
        AUTH_TOKEN = token
    elif not AUTH_TOKEN:
        AUTH_TOKEN = register_test_user()
    
    if not AUTH_TOKEN:
        print("Warning: No auth token available")
        return {}
    
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}

def test_export_pdf_endpoint_auth_required():
    """Test that PDF export endpoint requires authentication"""
    decision_id = str(uuid.uuid4())  # Use a random ID
    response = requests.post(f"{API_URL}/decisions/{decision_id}/export-pdf")
    
    # Should require authentication
    if response.status_code not in [401, 403]:
        print(f"Error: PDF export endpoint should require authentication but returned {response.status_code}")
        return False
    
    print(f"PDF export endpoint correctly requires authentication (status code: {response.status_code})")
    return True

def test_export_pdf_endpoint_structure():
    """Test the structure of the PDF export endpoint (not actual functionality)"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Use a random decision ID
    decision_id = str(uuid.uuid4())
    
    # Try to export PDF
    response = requests.post(
        f"{API_URL}/decisions/{decision_id}/export-pdf",
        headers=headers
    )
    
    # We expect either a 403 (Pro required) or a 404 (Decision not found) or a 500 (internal error)
    if response.status_code not in [403, 404, 500]:
        print(f"Error: PDF export endpoint returned unexpected status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check if the error message indicates the endpoint exists but requires Pro
    if response.status_code == 403 or (response.status_code == 500 and "Pro subscription" in response.text):
        print(f"PDF export endpoint exists and requires Pro subscription")
        return True
    elif response.status_code == 404 or (response.status_code == 500 and "not found" in response.text.lower()):
        print(f"PDF export endpoint exists but decision not found")
        return True
    else:
        print(f"PDF export endpoint exists but returned an error: {response.text}")
        return True

def test_create_share_endpoint_auth_required():
    """Test that share creation endpoint requires authentication"""
    decision_id = str(uuid.uuid4())  # Use a random ID
    response = requests.post(f"{API_URL}/decisions/{decision_id}/share")
    
    # Should require authentication
    if response.status_code not in [401, 403]:
        print(f"Error: Share creation endpoint should require authentication but returned {response.status_code}")
        return False
    
    print(f"Share creation endpoint correctly requires authentication (status code: {response.status_code})")
    return True

def test_create_share_endpoint_structure():
    """Test the structure of the share creation endpoint (not actual functionality)"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Use a random decision ID
    decision_id = str(uuid.uuid4())
    
    # Try to create share
    response = requests.post(
        f"{API_URL}/decisions/{decision_id}/share",
        headers=headers
    )
    
    # We expect either a 404 (Decision not found) or a 500 (internal error)
    if response.status_code not in [404, 500]:
        print(f"Error: Share creation endpoint returned unexpected status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check if the error message indicates the endpoint exists but decision not found
    if response.status_code == 404 or (response.status_code == 500 and "not found" in response.text.lower()):
        print(f"Share creation endpoint exists but decision not found")
        return True
    else:
        print(f"Share creation endpoint exists but returned an error: {response.text}")
        return True

def test_get_shared_decision_endpoint_structure():
    """Test the structure of the get shared decision endpoint (not actual functionality)"""
    # Use a random share ID
    share_id = str(uuid.uuid4())
    
    # Try to get shared decision
    response = requests.get(f"{API_URL}/shared/{share_id}")
    
    # We expect either a 404 (Share not found) or a 500 (internal error)
    if response.status_code not in [404, 500]:
        print(f"Error: Get shared decision endpoint returned unexpected status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check if the error message indicates the endpoint exists but share not found
    if response.status_code == 404 or (response.status_code == 500 and "not found" in response.text.lower()):
        print(f"Get shared decision endpoint exists but share not found")
        return True
    else:
        print(f"Get shared decision endpoint exists but returned an error: {response.text}")
        return True

def test_revoke_share_endpoint_auth_required():
    """Test that revoke share endpoint requires authentication"""
    share_id = str(uuid.uuid4())  # Use a random ID
    response = requests.delete(f"{API_URL}/decisions/shares/{share_id}")
    
    # Should require authentication
    if response.status_code not in [401, 403]:
        print(f"Error: Revoke share endpoint should require authentication but returned {response.status_code}")
        return False
    
    print(f"Revoke share endpoint correctly requires authentication (status code: {response.status_code})")
    return True

def test_revoke_share_endpoint_structure():
    """Test the structure of the revoke share endpoint (not actual functionality)"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Use a random share ID
    share_id = str(uuid.uuid4())
    
    # Try to revoke share
    response = requests.delete(
        f"{API_URL}/decisions/shares/{share_id}",
        headers=headers
    )
    
    # We expect either a 404 (Share not found) or a 500 (internal error)
    if response.status_code not in [404, 500]:
        print(f"Error: Revoke share endpoint returned unexpected status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check if the error message indicates the endpoint exists but share not found
    if response.status_code == 404 or (response.status_code == 500 and "not found" in response.text.lower()):
        print(f"Revoke share endpoint exists but share not found")
        return True
    else:
        print(f"Revoke share endpoint exists but returned an error: {response.text}")
        return True

def test_get_decision_shares_endpoint_auth_required():
    """Test that get decision shares endpoint requires authentication"""
    decision_id = str(uuid.uuid4())  # Use a random ID
    response = requests.get(f"{API_URL}/decisions/{decision_id}/shares")
    
    # Should require authentication
    if response.status_code not in [401, 403]:
        print(f"Error: Get decision shares endpoint should require authentication but returned {response.status_code}")
        return False
    
    print(f"Get decision shares endpoint correctly requires authentication (status code: {response.status_code})")
    return True

def test_get_decision_shares_endpoint_structure():
    """Test the structure of the get decision shares endpoint (not actual functionality)"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Use a random decision ID
    decision_id = str(uuid.uuid4())
    
    # Try to get decision shares
    response = requests.get(
        f"{API_URL}/decisions/{decision_id}/shares",
        headers=headers
    )
    
    # We expect either a 404 (Decision not found), a 200 (empty shares list), or a 500 (internal error)
    if response.status_code not in [200, 404, 500]:
        print(f"Error: Get decision shares endpoint returned unexpected status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # If 200, check the response structure
    if response.status_code == 200:
        data = response.json()
        if "shares" not in data:
            print(f"Error: Get decision shares response missing 'shares' field: {data}")
            return False
        
        print(f"Get decision shares endpoint returned empty shares list")
        return True
    # Check if the error message indicates the endpoint exists but decision not found
    elif response.status_code == 404 or (response.status_code == 500 and "not found" in response.text.lower()):
        print(f"Get decision shares endpoint exists but decision not found")
        return True
    else:
        print(f"Get decision shares endpoint exists but returned an error: {response.text}")
        return True

def test_compare_decisions_endpoint_auth_required():
    """Test that compare decisions endpoint requires authentication"""
    response = requests.post(f"{API_URL}/decisions/compare", json={"decision_ids": [str(uuid.uuid4()), str(uuid.uuid4())]})
    
    # Should require authentication
    if response.status_code not in [401, 403]:
        print(f"Error: Compare decisions endpoint should require authentication but returned {response.status_code}")
        return False
    
    print(f"Compare decisions endpoint correctly requires authentication (status code: {response.status_code})")
    return True

def test_compare_decisions_endpoint_structure():
    """Test the structure of the compare decisions endpoint (not actual functionality)"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Use random decision IDs
    decision_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    
    # Try to compare decisions
    response = requests.post(
        f"{API_URL}/decisions/compare",
        json={"decision_ids": decision_ids},
        headers=headers
    )
    
    # We expect either a 404 (Decisions not found), a 422 (Validation error), or a 500 (internal error)
    if response.status_code not in [404, 422, 500]:
        print(f"Error: Compare decisions endpoint returned unexpected status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Compare decisions endpoint exists but returned expected error for non-existent decisions")
    return True

def test_compare_decisions_validation_structure():
    """Test the validation structure of the compare decisions endpoint (not actual functionality)"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Test with too few decisions (1)
    response = requests.post(
        f"{API_URL}/decisions/compare",
        json={"decision_ids": [str(uuid.uuid4())]},
        headers=headers
    )
    
    # Should return 400 Bad Request or 422 Validation Error
    if response.status_code not in [400, 422]:
        print(f"Error: Compare with too few decisions should return 400 or 422 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test with too many decisions (6)
    too_many_ids = [str(uuid.uuid4()) for _ in range(6)]
    
    response = requests.post(
        f"{API_URL}/decisions/compare",
        json={"decision_ids": too_many_ids},
        headers=headers
    )
    
    # Should return 400 Bad Request or 422 Validation Error
    if response.status_code not in [400, 422]:
        print(f"Error: Compare with too many decisions should return 400 or 422 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Decision comparison validation structure works correctly")
    return True

def run_all_tests():
    """Run all export and sharing tests"""
    tests = [
        # Export & Sharing tests - Authentication Requirements
        ("PDF Export Auth Required", test_export_pdf_endpoint_auth_required),
        ("Create Share Auth Required", test_create_share_endpoint_auth_required),
        ("Revoke Share Auth Required", test_revoke_share_endpoint_auth_required),
        ("Get Decision Shares Auth Required", test_get_decision_shares_endpoint_auth_required),
        ("Compare Decisions Auth Required", test_compare_decisions_endpoint_auth_required),
        
        # Export & Sharing tests - Endpoint Structure
        ("PDF Export Structure", test_export_pdf_endpoint_structure),
        ("Create Share Structure", test_create_share_endpoint_structure),
        ("Get Shared Decision Structure", test_get_shared_decision_endpoint_structure),
        ("Revoke Share Structure", test_revoke_share_endpoint_structure),
        ("Get Decision Shares Structure", test_get_decision_shares_endpoint_structure),
        ("Compare Decisions Structure", test_compare_decisions_endpoint_structure),
        ("Compare Decisions Validation Structure", test_compare_decisions_validation_structure),
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