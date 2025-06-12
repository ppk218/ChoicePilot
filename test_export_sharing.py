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

# Test Pro user credentials for testing Pro features
TEST_PRO_USER = {
    "email": "pro_user@example.com",
    "password": "ProUserPassword123!"
}

# Store auth token for authenticated requests
AUTH_TOKEN = None
PRO_AUTH_TOKEN = None

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

def register_pro_test_user():
    """Register a Pro test user and return the auth token"""
    try:
        # Check if user already exists by trying to login
        login_response = requests.post(f"{API_URL}/auth/login", json=TEST_PRO_USER)
        if login_response.status_code == 200:
            # User exists, return token
            token = login_response.json().get("access_token")
            return token
        
        # User doesn't exist, register
        register_response = requests.post(f"{API_URL}/auth/register", json=TEST_PRO_USER)
        if register_response.status_code == 200:
            token = register_response.json().get("access_token")
            return token
        else:
            print(f"Failed to register Pro test user: {register_response.status_code} - {register_response.text}")
            return None
    except Exception as e:
        print(f"Error registering Pro test user: {str(e)}")
        return None

def get_auth_headers(token=None, pro_user=False):
    """Get authorization headers for authenticated requests"""
    global AUTH_TOKEN, PRO_AUTH_TOKEN
    
    if token:
        if pro_user:
            PRO_AUTH_TOKEN = token
        else:
            AUTH_TOKEN = token
    elif pro_user and not PRO_AUTH_TOKEN:
        PRO_AUTH_TOKEN = register_pro_test_user()
        token = PRO_AUTH_TOKEN
    elif not pro_user and not AUTH_TOKEN:
        AUTH_TOKEN = register_test_user()
        token = AUTH_TOKEN
    else:
        token = PRO_AUTH_TOKEN if pro_user else AUTH_TOKEN
    
    if not token:
        print(f"Warning: No auth token available for {'Pro' if pro_user else 'regular'} user")
        return {}
    
    return {"Authorization": f"Bearer {token}"}

def create_real_decision(pro_user=False):
    """Create a real decision in the database and return the decision_id"""
    # Get auth token
    headers = get_auth_headers(pro_user=pro_user)
    if not headers:
        print(f"Error: Could not get authentication token for {'Pro' if pro_user else 'regular'} user")
        return None
    
    # Create a new decision via chat endpoint
    decision_id = str(uuid.uuid4())
    
    # Generate a random decision topic for variety
    topics = [
        "I'm trying to decide between a MacBook Pro and a Dell XPS for programming work.",
        "Should I invest in stocks or real estate with my savings?",
        "I'm considering a vacation to either Japan or Italy next summer.",
        "Should I pursue a master's degree or focus on gaining work experience?",
        "I'm trying to decide whether to buy or lease a car."
    ]
    
    message = random.choice(topics)
    categories = ["consumer", "financial", "travel", "career", "general"]
    category = categories[topics.index(message) % len(categories)]
    
    payload = {
        "message": message,
        "decision_id": decision_id,
        "category": category,
        "preferences": {"priority": "balanced"}
    }
    
    # Use the real API to create a decision
    response = requests.post(f"{API_URL}/chat", json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Error: Failed to create test decision: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    created_decision_id = data.get("decision_id")
    print(f"Created real decision with ID: {created_decision_id}")
    
    # Add a second message to make the conversation more realistic
    follow_up_message = f"I'd like to know more about the {category} aspects."
    follow_up_payload = {
        "message": follow_up_message,
        "decision_id": created_decision_id,
        "category": category
    }
    
    follow_up_response = requests.post(f"{API_URL}/chat", json=follow_up_payload, headers=headers)
    if follow_up_response.status_code != 200:
        print(f"Warning: Failed to add follow-up message: {follow_up_response.status_code}")
    else:
        print(f"Added follow-up message to decision {created_decision_id}")
    
    return created_decision_id

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

def test_export_pdf_endpoint_pro_required():
    """Test that PDF export endpoint requires Pro subscription"""
    # Get auth token for regular (non-Pro) user
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Create a real decision
    decision_id = create_real_decision()
    if not decision_id:
        print("Error: Could not create test decision")
        return False
    
    # Try to export PDF as non-Pro user
    response = requests.post(
        f"{API_URL}/decisions/{decision_id}/export-pdf",
        headers=headers
    )
    
    # Should require Pro subscription
    if response.status_code != 403:
        print(f"Error: PDF export endpoint should require Pro subscription but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"PDF export endpoint correctly requires Pro subscription (status code: {response.status_code})")
    return True

def test_export_pdf_endpoint_nonexistent_decision():
    """Test PDF export with non-existent decision ID"""
    # Get auth token for Pro user
    headers = get_auth_headers(pro_user=True)
    if not headers:
        print("Error: Could not get Pro user authentication token")
        return False
    
    # Use a random non-existent decision ID
    fake_decision_id = str(uuid.uuid4())
    
    # Try to export PDF for non-existent decision
    response = requests.post(
        f"{API_URL}/decisions/{fake_decision_id}/export-pdf",
        headers=headers
    )
    
    # Should return 404 Not Found
    if response.status_code != 404:
        print(f"Error: PDF export with non-existent decision ID should return 404 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"PDF export with non-existent decision ID correctly returns 404 Not Found")
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

def test_create_share_endpoint():
    """Test creating a shareable link for a decision"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Create a real decision
    decision_id = create_real_decision()
    if not decision_id:
        print("Error: Could not create test decision")
        return False
    
    # Create shareable link
    response = requests.post(
        f"{API_URL}/decisions/{decision_id}/share",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error: Share creation endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["share_id", "share_url", "privacy_level", "created_at"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Share creation response missing required field '{field}'")
            return False
    
    if not data["share_id"] or not data["share_url"]:
        print("Error: Share ID or URL is empty")
        return False
    
    # Check that share URL contains share ID
    if data["share_id"] not in data["share_url"]:
        print(f"Error: Share URL '{data['share_url']}' does not contain share ID '{data['share_id']}'")
        return False
    
    print(f"Share creation successful: {data['share_url']}")
    return True, data["share_id"]  # Return share_id for use in other tests

def test_create_share_endpoint_nonexistent_decision():
    """Test share creation with non-existent decision ID"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Use a random non-existent decision ID
    fake_decision_id = str(uuid.uuid4())
    
    # Try to create share for non-existent decision
    response = requests.post(
        f"{API_URL}/decisions/{fake_decision_id}/share",
        headers=headers
    )
    
    # Should return 404 Not Found
    if response.status_code != 404:
        print(f"Error: Share creation with non-existent decision ID should return 404 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Share creation with non-existent decision ID correctly returns 404 Not Found")
    return True

def test_get_shared_decision_endpoint():
    """Test retrieving a shared decision"""
    # First create a share
    result = test_create_share_endpoint()
    if not isinstance(result, tuple) or not result[0]:
        print("Error: Could not create share for testing")
        return False
    
    share_id = result[1]
    
    # Get shared decision (public endpoint, no auth required)
    response = requests.get(f"{API_URL}/shared/{share_id}")
    
    if response.status_code != 200:
        print(f"Error: Get shared decision endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["decision", "conversations", "share_info"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Shared decision response missing required field '{field}'")
            return False
    
    # Check decision data
    decision = data["decision"]
    decision_required_fields = ["title", "category", "advisor_style", "message_count"]
    for field in decision_required_fields:
        if field not in decision:
            print(f"Error: Shared decision data missing required field '{field}'")
            return False
    
    # Check share info
    share_info = data["share_info"]
    share_info_required_fields = ["view_count", "created_at", "privacy_level"]
    for field in share_info_required_fields:
        if field not in share_info:
            print(f"Error: Share info missing required field '{field}'")
            return False
    
    print(f"Get shared decision successful: {decision['title']} with {len(data['conversations'])} conversations")
    return True

def test_get_shared_decision_nonexistent():
    """Test retrieving a non-existent shared decision"""
    # Use a random non-existent share ID
    fake_share_id = str(uuid.uuid4())
    
    # Try to get non-existent shared decision
    response = requests.get(f"{API_URL}/shared/{fake_share_id}")
    
    # Should return 404 Not Found
    if response.status_code != 404:
        print(f"Error: Get non-existent shared decision should return 404 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Get non-existent shared decision correctly returns 404 Not Found")
    return True

def test_revoke_share_endpoint():
    """Test revoking a decision share"""
    # First create a share
    result = test_create_share_endpoint()
    if not isinstance(result, tuple) or not result[0]:
        print("Error: Could not create share for testing")
        return False
    
    share_id = result[1]
    
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Revoke share
    response = requests.delete(
        f"{API_URL}/decisions/shares/{share_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error: Revoke share endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "message" not in data:
        print(f"Error: Revoke share response missing 'message' field: {data}")
        return False
    
    # Verify share is revoked by trying to access it
    verify_response = requests.get(f"{API_URL}/shared/{share_id}")
    if verify_response.status_code != 404:
        print(f"Error: Share should be revoked but is still accessible (status code: {verify_response.status_code})")
        return False
    
    print(f"Share revocation successful: {data['message']}")
    return True

def test_revoke_share_nonexistent():
    """Test revoking a non-existent share"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Use a random non-existent share ID
    fake_share_id = str(uuid.uuid4())
    
    # Try to revoke non-existent share
    response = requests.delete(
        f"{API_URL}/decisions/shares/{fake_share_id}",
        headers=headers
    )
    
    # Should return 404 Not Found
    if response.status_code != 404:
        print(f"Error: Revoke non-existent share should return 404 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Revoke non-existent share correctly returns 404 Not Found")
    return True

def test_get_decision_shares_endpoint():
    """Test getting all shares for a decision"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Create a real decision
    decision_id = create_real_decision()
    if not decision_id:
        print("Error: Could not create test decision")
        return False
    
    # Create a share for the decision
    response = requests.post(
        f"{API_URL}/decisions/{decision_id}/share",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error: Could not create share for testing: {response.status_code}")
        return False
    
    # Get all shares for the decision
    response = requests.get(
        f"{API_URL}/decisions/{decision_id}/shares",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error: Get decision shares endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "shares" not in data:
        print(f"Error: Get decision shares response missing 'shares' field: {data}")
        return False
    
    shares = data["shares"]
    if not shares:
        print(f"Error: No shares returned for decision that should have at least one share")
        return False
    
    # Check share data
    share = shares[0]
    required_fields = ["share_id", "decision_id", "privacy_level", "created_at", "view_count"]
    for field in required_fields:
        if field not in share:
            print(f"Error: Share data missing required field '{field}'")
            return False
    
    if share["decision_id"] != decision_id:
        print(f"Error: Share decision_id '{share['decision_id']}' doesn't match expected '{decision_id}'")
        return False
    
    print(f"Get decision shares successful: {len(shares)} shares found")
    return True

def test_compare_decisions_endpoint():
    """Test comparing multiple decisions"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Create two real decisions
    decision_id1 = create_real_decision()
    decision_id2 = create_real_decision()
    
    if not decision_id1 or not decision_id2:
        print("Error: Could not create test decisions")
        return False
    
    # Compare decisions
    response = requests.post(
        f"{API_URL}/decisions/compare",
        json={"decision_ids": [decision_id1, decision_id2]},
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error: Compare decisions endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["comparisons", "insights", "comparison_id", "generated_at"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Compare decisions response missing required field '{field}'")
            return False
    
    comparisons = data["comparisons"]
    if len(comparisons) != 2:
        print(f"Error: Expected 2 comparisons but got {len(comparisons)}")
        return False
    
    # Check comparison data
    for comparison in comparisons:
        comparison_required_fields = ["decision_id", "title", "category", "metrics"]
        for field in comparison_required_fields:
            if field not in comparison:
                print(f"Error: Comparison data missing required field '{field}'")
                return False
        
        metrics = comparison["metrics"]
        metrics_required_fields = ["total_messages", "unique_advisors", "total_credits", "ai_models_used"]
        for field in metrics_required_fields:
            if field not in metrics:
                print(f"Error: Metrics data missing required field '{field}'")
                return False
    
    # Check insights data
    insights = data["insights"]
    insights_required_fields = ["total_decisions", "averages", "patterns"]
    for field in insights_required_fields:
        if field not in insights:
            print(f"Error: Insights data missing required field '{field}'")
            return False
    
    print(f"Compare decisions successful: {len(comparisons)} decisions compared")
    return True

def test_compare_decisions_validation():
    """Test decision comparison validation (min/max decisions)"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Test with too few decisions (1)
    decision_id = create_real_decision()
    if not decision_id:
        print("Error: Could not create test decision")
        return False
    
    response = requests.post(
        f"{API_URL}/decisions/compare",
        json={"decision_ids": [decision_id]},
        headers=headers
    )
    
    # Should return 400 Bad Request
    if response.status_code != 400:
        print(f"Error: Compare with too few decisions should return 400 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test with too many decisions (6)
    too_many_ids = [str(uuid.uuid4()) for _ in range(6)]
    
    response = requests.post(
        f"{API_URL}/decisions/compare",
        json={"decision_ids": too_many_ids},
        headers=headers
    )
    
    # Should return 400 Bad Request
    if response.status_code != 400:
        print(f"Error: Compare with too many decisions should return 400 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Decision comparison validation works correctly")
    return True

def run_all_tests():
    """Run all export and sharing tests"""
    tests = [
        # Export & Sharing tests
        ("PDF Export Auth Required", test_export_pdf_endpoint_auth_required),
        ("PDF Export Pro Required", test_export_pdf_endpoint_pro_required),
        ("PDF Export Non-existent Decision", test_export_pdf_endpoint_nonexistent_decision),
        ("Create Share Auth Required", test_create_share_endpoint_auth_required),
        ("Create Share", lambda: test_create_share_endpoint()[0] if isinstance(test_create_share_endpoint(), tuple) else test_create_share_endpoint()),
        ("Create Share Non-existent Decision", test_create_share_endpoint_nonexistent_decision),
        ("Get Shared Decision", test_get_shared_decision_endpoint),
        ("Get Non-existent Shared Decision", test_get_shared_decision_nonexistent),
        ("Revoke Share", test_revoke_share_endpoint),
        ("Revoke Non-existent Share", test_revoke_share_nonexistent),
        ("Get Decision Shares", test_get_decision_shares_endpoint),
        ("Compare Decisions", test_compare_decisions_endpoint),
        ("Compare Decisions Validation", test_compare_decisions_validation),
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